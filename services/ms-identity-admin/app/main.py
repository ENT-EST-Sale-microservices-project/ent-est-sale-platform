from __future__ import annotations

import os
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from cassandra.policies import RoundRobinPolicy
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from .runtime import extract_request_id, setup_service_runtime

AUTH_CORE_BASE_URL = os.getenv("AUTH_CORE_BASE_URL", "http://ms-auth-core:8000")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("IDENTITY_ADMIN_TIMEOUT_SECONDS", "8"))
ALLOWED_ROLES = {
    role.strip()
    for role in os.getenv("IDENTITY_ADMIN_ALLOWED_ROLES", "admin").split(",")
    if role.strip()
}

KEYCLOAK_BASE_URL = os.getenv("KEYCLOAK_BASE_URL", "http://keycloak:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "ent-est")
KEYCLOAK_ADMIN_REALM = os.getenv("KEYCLOAK_ADMIN_REALM", "master")
KEYCLOAK_ADMIN = os.getenv("KEYCLOAK_ADMIN", "admin")
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "ChangeMe_123!")

CASSANDRA_CONTACT_POINTS = [
    host.strip() for host in os.getenv("CASSANDRA_CONTACT_POINTS", "cassandra").split(",") if host.strip()
]
CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_USERNAME = os.getenv("CASSANDRA_USERNAME", "cassandra")
CASSANDRA_PASSWORD = os.getenv("CASSANDRA_PASSWORD", "ChangeMe_123!")
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "ent_est")
PROFILE_TABLE = os.getenv("IDENTITY_ADMIN_PROFILE_TABLE", "user_profiles")

app = FastAPI(
    title="MS-Identity-Admin",
    version="0.1.0",
    description="User profile management and Keycloak synchronization service.",
)
setup_service_runtime(app, "ms-identity-admin")

cluster: Cluster | None = None
db_session = None
insert_profile_stmt = None
update_profile_stmt = None
select_profile_stmt = None
select_profiles_stmt = None
delete_profile_stmt = None

keycloak_access_token: str | None = None
keycloak_token_expires: datetime | None = None


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: str = Field(min_length=5, max_length=255)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    roles: list[str] = Field(default_factory=lambda: ["student"])
    enabled: bool = Field(default=True)


class UpdateUserRequest(BaseModel):
    email: str | None = Field(default=None, min_length=5, max_length=255)
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    roles: list[str] | None = Field(default=None)
    enabled: bool | None = Field(default=None)


class UserProfileResponse(BaseModel):
    user_id: str
    username: str
    email: str
    first_name: str
    last_name: str
    roles: list[str]
    enabled: bool
    keycloak_id: str | None
    created_at: str
    updated_at: str


class UpdateRolesRequest(BaseModel):
    roles: list[str] = Field(min_length=1)


def _timestamp() -> datetime:
    return datetime.now(timezone.utc)


def _iso(ts: datetime | None) -> str:
    return (ts or _timestamp()).isoformat()


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _forbidden(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _extract_roles(claims: dict[str, Any]) -> set[str]:
    return set((claims.get("realm_access") or {}).get("roles", []))


async def require_admin(
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _unauthorized("Missing bearer token")

    attempts = 3
    backoff = 0.15
    resp: httpx.Response | None = None
    for attempt in range(1, attempts + 1):
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                resp = await client.get(
                    f"{AUTH_CORE_BASE_URL}/auth/me",
                    headers={"Authorization": authorization},
                )
            break
        except httpx.RequestError as exc:
            if attempt < attempts:
                await asyncio.sleep(backoff)
                backoff *= 2
                continue
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"auth-core unavailable: {exc.__class__.__name__}",
            ) from exc

    assert resp is not None

    if resp.status_code == status.HTTP_401_UNAUTHORIZED:
        raise _unauthorized("Invalid or expired token")

    if resp.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="auth-core returned an unexpected error",
        )

    claims = resp.json()
    token_roles = _extract_roles(claims)
    if not token_roles.intersection(ALLOWED_ROLES):
        raise _forbidden(
            f"Forbidden. Required one of roles: {', '.join(sorted(ALLOWED_ROLES))}"
        )

    return claims


async def _get_keycloak_token() -> str:
    global keycloak_access_token, keycloak_token_expires

    if keycloak_access_token and keycloak_token_expires and datetime.now(timezone.utc) < keycloak_token_expires:
        return keycloak_access_token

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        resp = await client.post(
            f"{KEYCLOAK_BASE_URL}/realms/{KEYCLOAK_ADMIN_REALM}/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": "admin-cli",
                "username": KEYCLOAK_ADMIN,
                "password": KEYCLOAK_ADMIN_PASSWORD,
            },
        )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to obtain Keycloak admin token",
        )

    data = resp.json()
    keycloak_access_token = data["access_token"]
    expires_in = data.get("expires_in", 300)
    keycloak_token_expires = datetime.now(timezone.utc).timestamp() + expires_in - 30
    return keycloak_access_token


async def _create_keycloak_user(user_data: CreateUserRequest) -> str:
    token = await _get_keycloak_token()

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        resp = await client.post(
            f"{KEYCLOAK_BASE_URL}/admin/realms/{KEYCLOAK_REALM}/users",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "username": user_data.username,
                "email": user_data.email,
                "firstName": user_data.first_name,
                "lastName": user_data.last_name,
                "enabled": user_data.enabled,
                "credentials": [
                    {
                        "type": "password",
                        "value": "ChangeMe_123!",
                        "temporary": True,
                    }
                ],
            },
        )

    if resp.status_code not in (200, 201):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to create Keycloak user: {resp.text}",
        )

    # Get user ID from Location header
    location = resp.headers.get("Location", "")
    user_id = location.split("/")[-1] if location else user_data.username

    # Set roles in Keycloak
    if user_data.roles:
        await _set_keycloak_roles(user_id, user_data.roles)

    return user_id


async def _set_keycloak_roles(user_id: str, roles: list[str]) -> None:
    token = await _get_keycloak_token()

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        # Get available realm roles
        resp = await client.get(
            f"{KEYCLOAK_BASE_URL}/admin/realms/{KEYCLOAK_REALM}/roles",
            headers={"Authorization": f"Bearer {token}"},
        )

    if resp.status_code != 200:
        return

    available_roles = {r["name"]: r for r in resp.json()}
    role_reprs = []
    for role_name in roles:
        if role_name in available_roles:
            role_reprs.append(available_roles[role_name])

    if role_reprs:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            await client.post(
                f"{KEYCLOAK_BASE_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}/role-mappings/realm",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=role_reprs,
            )


async def _update_keycloak_user(user_id: str, keycloak_id: str, update_data: UpdateUserRequest) -> None:
    token = await _get_keycloak_token()

    update_json = {}
    if update_data.email is not None:
        update_json["email"] = update_data.email
    if update_data.first_name is not None:
        update_json["firstName"] = update_data.first_name
    if update_data.last_name is not None:
        update_json["lastName"] = update_data.last_name
    if update_data.enabled is not None:
        update_json["enabled"] = update_data.enabled

    if update_json:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            resp = await client.put(
                f"{KEYCLOAK_BASE_URL}/admin/realms/{KEYCLOAK_REALM}/users/{keycloak_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=update_json,
            )

        if resp.status_code not in (200, 204):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to update Keycloak user: {resp.text}",
            )

    if update_data.roles is not None:
        await _set_keycloak_roles(keycloak_id, update_data.roles)


def _ensure_db() -> None:
    global cluster, db_session
    global insert_profile_stmt, update_profile_stmt, select_profile_stmt, select_profiles_stmt, delete_profile_stmt

    if db_session is not None:
        return

    auth_provider = PlainTextAuthProvider(
        username=CASSANDRA_USERNAME,
        password=CASSANDRA_PASSWORD,
    )
    cluster = Cluster(
        contact_points=CASSANDRA_CONTACT_POINTS,
        port=CASSANDRA_PORT,
        load_balancing_policy=RoundRobinPolicy(),
        auth_provider=auth_provider,
    )
    db_session = cluster.connect()
    db_session.execute(
        "CREATE KEYSPACE IF NOT EXISTS "
        f"{CASSANDRA_KEYSPACE} "
        "WITH replication = {'class':'SimpleStrategy','replication_factor':1};"
    )
    db_session.set_keyspace(CASSANDRA_KEYSPACE)
    db_session.execute(
        "CREATE TABLE IF NOT EXISTS "
        f"{PROFILE_TABLE} ("
        "user_id text PRIMARY KEY,"
        "username text,"
        "email text,"
        "first_name text,"
        "last_name text,"
        "roles list<text>,"
        "enabled boolean,"
        "keycloak_id text,"
        "created_at timestamp,"
        "updated_at timestamp"
        ");"
    )

    insert_profile_stmt = db_session.prepare(
        "INSERT INTO "
        f"{PROFILE_TABLE} "
        "(user_id, username, email, first_name, last_name, roles, enabled, keycloak_id, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    update_profile_stmt = db_session.prepare(
        "UPDATE "
        + PROFILE_TABLE
        + " SET email = ?, first_name = ?, last_name = ?, roles = ?, enabled = ?, updated_at = ? WHERE user_id = ?"
    )
    select_profile_stmt = db_session.prepare(
        "SELECT user_id, username, email, first_name, last_name, roles, enabled, keycloak_id, created_at, updated_at "
        "FROM " + PROFILE_TABLE + " WHERE user_id = ?"
    )
    select_profiles_stmt = db_session.prepare(
        "SELECT user_id, username, email, first_name, last_name, roles, enabled, keycloak_id, created_at, updated_at "
        "FROM " + PROFILE_TABLE
    )
    delete_profile_stmt = db_session.prepare(
        "DELETE FROM " + PROFILE_TABLE + " WHERE user_id = ?"
    )


def _serialize_profile(row: Any) -> dict[str, Any]:
    return {
        "user_id": row.user_id,
        "username": row.username,
        "email": row.email,
        "first_name": row.first_name,
        "last_name": row.last_name,
        "roles": list(row.roles or []),
        "enabled": row.enabled,
        "keycloak_id": row.keycloak_id,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


def _get_profile_or_none(user_id: str) -> dict[str, Any] | None:
    _ensure_db()
    row = db_session.execute(select_profile_stmt, (user_id,)).one()
    if row is None:
        return None
    return _serialize_profile(row)


@app.on_event("startup")
def startup() -> None:
    _ensure_db()


@app.on_event("shutdown")
def shutdown() -> None:
    if cluster is not None:
        cluster.shutdown()


@app.get("/identity-admin/health", tags=["identity-admin"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ms-identity-admin",
    }


@app.post("/admin/users", response_model=UserProfileResponse, tags=["identity-admin"])
async def create_user(
    request: Request,
    payload: CreateUserRequest,
    _: dict[str, Any] = Depends(require_admin),
) -> UserProfileResponse:
    _ensure_db()
    user_id = str(uuid.uuid4())
    now = _timestamp()

    keycloak_id = await _create_keycloak_user(payload)

    db_session.execute(
        insert_profile_stmt,
        (
            user_id,
            payload.username,
            payload.email,
            payload.first_name,
            payload.last_name,
            payload.roles,
            payload.enabled,
            keycloak_id,
            now,
            now,
        ),
    )

    return UserProfileResponse(
        user_id=user_id,
        username=payload.username,
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        roles=payload.roles,
        enabled=payload.enabled,
        keycloak_id=keycloak_id,
        created_at=now.isoformat(),
        updated_at=now.isoformat(),
    )


@app.get("/admin/users", response_model=list[UserProfileResponse], tags=["identity-admin"])
def list_users(
    _: dict[str, Any] = Depends(require_admin),
) -> list[UserProfileResponse]:
    _ensure_db()
    rows = db_session.execute(select_profiles_stmt)
    return [UserProfileResponse(**_serialize_profile(row)) for row in rows]


@app.get("/admin/users/{user_id}", response_model=UserProfileResponse, tags=["identity-admin"])
def get_user(
    user_id: str,
    _: dict[str, Any] = Depends(require_admin),
) -> UserProfileResponse:
    profile = _get_profile_or_none(user_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserProfileResponse(**profile)


@app.patch("/admin/users/{user_id}", response_model=UserProfileResponse, tags=["identity-admin"])
async def update_user(
    request: Request,
    user_id: str,
    payload: UpdateUserRequest,
    _: dict[str, Any] = Depends(require_admin),
) -> UserProfileResponse:
    _ensure_db()
    profile = _get_profile_or_none(user_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    now = _timestamp()

    email = payload.email if payload.email is not None else profile["email"]
    first_name = payload.first_name if payload.first_name is not None else profile["first_name"]
    last_name = payload.last_name if payload.last_name is not None else profile["last_name"]
    roles = payload.roles if payload.roles is not None else profile["roles"]
    enabled = payload.enabled if payload.enabled is not None else profile["enabled"]

    if profile.get("keycloak_id"):
        await _update_keycloak_user(user_id, profile["keycloak_id"], payload)

    db_session.execute(
        update_profile_stmt,
        (email, first_name, last_name, roles, enabled, now, user_id),
    )

    updated = _get_profile_or_none(user_id)
    return UserProfileResponse(**updated)


@app.patch(
    "/admin/users/{user_id}/roles",
    response_model=UserProfileResponse,
    tags=["identity-admin"],
)
async def update_user_roles(
    request: Request,
    user_id: str,
    payload: UpdateRolesRequest,
    _: dict[str, Any] = Depends(require_admin),
) -> UserProfileResponse:
    _ensure_db()
    profile = _get_profile_or_none(user_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    now = _timestamp()
    roles = payload.roles

    if profile.get("keycloak_id"):
        await _set_keycloak_roles(profile["keycloak_id"], roles)

    db_session.execute(
        update_profile_stmt,
        (
            profile["email"],
            profile["first_name"],
            profile["last_name"],
            roles,
            profile["enabled"],
            now,
            user_id,
        ),
    )

    updated = _get_profile_or_none(user_id)
    return UserProfileResponse(**updated)


@app.delete("/admin/users/{user_id}", tags=["identity-admin"])
async def delete_user(
    request: Request,
    user_id: str,
    _: dict[str, Any] = Depends(require_admin),
) -> dict[str, str]:
    _ensure_db()
    profile = _get_profile_or_none(user_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_session.execute(delete_profile_stmt, (user_id,))
    return {"status": "deleted"}