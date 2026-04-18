from __future__ import annotations

import os
import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import aio_pika
import httpx
from cassandra.cluster import Cluster
from cassandra.policies import RoundRobinPolicy
from cassandra.auth import PlainTextAuthProvider
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, EmailStr, Field

from .runtime import extract_request_id, setup_service_runtime


@dataclass(frozen=True)
class Settings:
    auth_core_base_url: str = os.getenv("AUTH_CORE_BASE_URL", "http://ms-auth-core:8000")
    timeout_seconds: float = float(os.getenv("IDENTITY_ADMIN_TIMEOUT_SECONDS", "8"))
    idempotent_retries: int = int(os.getenv("IDENTITY_ADMIN_IDEMPOTENT_RETRIES", "2"))
    admin_allowed_roles: set[str] = frozenset(
        role.strip()
        for role in os.getenv("IDENTITY_ADMIN_ALLOWED_ROLES", "admin").split(",")
        if role.strip()
    )

    keycloak_base_url: str = os.getenv("KEYCLOAK_BASE_URL", "http://keycloak:8080")
    keycloak_realm: str = os.getenv("KEYCLOAK_REALM", "ent-est")
    keycloak_admin_realm: str = os.getenv("KEYCLOAK_ADMIN_REALM", "master")
    keycloak_admin_username: str = os.getenv("KEYCLOAK_ADMIN", "admin")
    keycloak_admin_password: str = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "ChangeMe_123!")

    cassandra_contact_points: tuple[str, ...] = tuple(
        host.strip()
        for host in os.getenv("CASSANDRA_CONTACT_POINTS", "cassandra").split(",")
        if host.strip()
    )
    cassandra_port: int = int(os.getenv("CASSANDRA_PORT", "9042"))
    cassandra_username: str = os.getenv("CASSANDRA_USERNAME", "cassandra")
    cassandra_password: str = os.getenv("CASSANDRA_PASSWORD", "ChangeMe_123!")
    cassandra_keyspace: str = os.getenv("CASSANDRA_KEYSPACE", "ent_est")
    profile_table: str = os.getenv("IDENTITY_ADMIN_PROFILE_TABLE", "user_profiles")


settings = Settings()
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://ent:ChangeMe_123!@rabbitmq:5672/")
EVENTS_EXCHANGE = os.getenv("EVENTS_EXCHANGE", "ent.events.topic")
ENABLE_EVENT_PUBLISHING = os.getenv("ENABLE_EVENT_PUBLISHING", "true").lower() in {
    "1",
    "true",
    "yes",
    "on",
}

app = FastAPI(
    title="MS-Identity-Admin",
    version="0.1.0",
    description="Admin APIs for user provisioning and role assignment.",
)
setup_service_runtime(app, "ms-identity-admin")


cluster: Cluster | None = None
db_session = None
insert_profile_stmt = None
select_profile_stmt = None


async def _http_request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json_body: Any = None,
    form_data: dict[str, Any] | None = None,
    service_name: str = "downstream",
) -> httpx.Response:
    attempts = settings.idempotent_retries + 1 if method.upper() == "GET" else 1
    backoff = 0.15
    for attempt in range(1, attempts + 1):
        try:
            async with httpx.AsyncClient(timeout=settings.timeout_seconds) as client:
                return await client.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    json=json_body,
                    data=form_data,
                )
        except httpx.RequestError as exc:
            if attempt < attempts:
                await asyncio.sleep(backoff)
                backoff *= 2
                continue
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"{service_name} unavailable: {exc.__class__.__name__}",
            ) from exc

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"{service_name} unavailable: UnknownError",
    )


async def _publish_event(event_type: str, payload: dict[str, Any], correlation_id: str | None) -> None:
    if not ENABLE_EVENT_PUBLISHING:
        return
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                EVENTS_EXCHANGE,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            event = {
                "event_id": str(uuid4()),
                "event_type": event_type,
                "occurred_at": _timestamp().isoformat(),
                "producer": "ms-identity-admin",
                "correlation_id": correlation_id,
                "payload": payload,
            }
            message = aio_pika.Message(
                body=json.dumps(event).encode("utf-8"),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            routing_key = ".".join(event_type.split(".")[:2]) if "." in event_type else event_type
            await exchange.publish(message, routing_key=routing_key)
    except Exception:
        # Publishing failure should not break provisioning path in MVP phase.
        pass


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=256)
    roles: list[str] = Field(default_factory=lambda: ["student"])
    enabled: bool = True


class PatchUserRolesRequest(BaseModel):
    roles: list[str] = Field(min_length=1)


class UserProfileResponse(BaseModel):
    user_id: str
    username: str
    email: str | None = None
    full_name: str
    role: str | None = None
    status: str
    created_at: str
    updated_at: str


def _timestamp() -> datetime:
    return datetime.now(timezone.utc)


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

    resp = await _http_request(
        "GET",
        f"{settings.auth_core_base_url}/auth/me",
        headers={"Authorization": authorization},
        service_name="auth-core",
    )

    if resp.status_code == status.HTTP_401_UNAUTHORIZED:
        raise _unauthorized("Invalid or expired token")

    if resp.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="auth-core returned an unexpected error",
        )

    claims = resp.json()
    roles = _extract_roles(claims)
    if not roles.intersection(settings.admin_allowed_roles):
        raise _forbidden(
            f"Forbidden. Required one of roles: {', '.join(sorted(settings.admin_allowed_roles))}"
        )
    return claims


async def _keycloak_admin_token() -> str:
    token_url = (
        f"{settings.keycloak_base_url}/realms/{settings.keycloak_admin_realm}"
        "/protocol/openid-connect/token"
    )
    data = {
        "client_id": "admin-cli",
        "grant_type": "password",
        "username": settings.keycloak_admin_username,
        "password": settings.keycloak_admin_password,
    }
    resp = await _http_request(
        "POST",
        token_url,
        form_data=data,
        service_name="keycloak",
    )

    if resp.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to get Keycloak admin token",
        )

    token = resp.json().get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid Keycloak admin token response",
        )
    return token


def _kc_admin_api(path: str) -> str:
    return f"{settings.keycloak_base_url}/admin/realms/{settings.keycloak_realm}{path}"


def _extract_location_id(resp: httpx.Response) -> str | None:
    location = resp.headers.get("Location") or resp.headers.get("location")
    if not location:
        return None
    return location.rstrip("/").split("/")[-1]


async def _keycloak_find_user_id(token: str, username: str) -> str | None:
    resp = await _http_request(
        "GET",
        _kc_admin_api("/users"),
        params={"username": username, "exact": "true"},
        headers={"Authorization": f"Bearer {token}"},
        service_name="keycloak",
    )

    if resp.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to search user in Keycloak",
        )

    users = resp.json()
    if not users:
        return None
    return users[0].get("id")


async def _keycloak_get_realm_role(token: str, role_name: str) -> dict[str, Any]:
    resp = await _http_request(
        "GET",
        _kc_admin_api(f"/roles/{role_name}"),
        headers={"Authorization": f"Bearer {token}"},
        service_name="keycloak",
    )

    if resp.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role not found in realm: {role_name}",
        )
    if resp.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to resolve realm role in Keycloak",
        )
    return resp.json()


async def _keycloak_assign_roles(token: str, user_id: str, roles: list[str]) -> None:
    role_representations = []
    for role_name in sorted(set(roles)):
        role_representations.append(await _keycloak_get_realm_role(token, role_name))

    resp = await _http_request(
        "POST",
        _kc_admin_api(f"/users/{user_id}/role-mappings/realm"),
        headers={"Authorization": f"Bearer {token}"},
        json_body=role_representations,
        service_name="keycloak",
    )

    if resp.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to assign user roles in Keycloak",
        )


async def _keycloak_replace_roles(token: str, user_id: str, roles: list[str]) -> None:
    current_resp = await _http_request(
        "GET",
        _kc_admin_api(f"/users/{user_id}/role-mappings/realm"),
        headers={"Authorization": f"Bearer {token}"},
        service_name="keycloak",
    )

    if current_resp.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch current user roles from Keycloak",
        )

    current_roles = current_resp.json()
    if current_roles:
        del_resp = await _http_request(
            "DELETE",
            _kc_admin_api(f"/users/{user_id}/role-mappings/realm"),
            headers={"Authorization": f"Bearer {token}"},
            json_body=current_roles,
            service_name="keycloak",
        )

        if del_resp.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to remove existing roles from Keycloak",
            )

    await _keycloak_assign_roles(token, user_id, roles)


def _ensure_db() -> None:
    global cluster, db_session, insert_profile_stmt, select_profile_stmt

    if db_session is not None:
        return

    auth_provider = PlainTextAuthProvider(
        username=settings.cassandra_username,
        password=settings.cassandra_password,
    )
    cluster = Cluster(
        contact_points=list(settings.cassandra_contact_points),
        port=settings.cassandra_port,
        load_balancing_policy=RoundRobinPolicy(),
        auth_provider=auth_provider,
    )
    db_session = cluster.connect()

    db_session.execute(
        "CREATE KEYSPACE IF NOT EXISTS "
        f"{settings.cassandra_keyspace} "
        "WITH replication = {'class':'SimpleStrategy','replication_factor':1};"
    )
    db_session.set_keyspace(settings.cassandra_keyspace)
    db_session.execute(
        "CREATE TABLE IF NOT EXISTS "
        f"{settings.profile_table} ("
        "user_id text PRIMARY KEY,"
        "username text,"
        "email text,"
        "full_name text,"
        "role text,"
        "status text,"
        "created_at timestamp,"
        "updated_at timestamp"
        ");"
    )

    insert_profile_stmt = db_session.prepare(
        "INSERT INTO "
        f"{settings.profile_table} "
        "(user_id, username, email, full_name, role, status, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    )
    select_profile_stmt = db_session.prepare(
        "SELECT user_id, username, email, full_name, role, status, created_at, updated_at "
        "FROM " + settings.profile_table + " WHERE user_id = ?"
    )


def _store_profile(
    *,
    user_id: str,
    username: str,
    email: str | None,
    full_name: str,
    role: str | None,
    status: str,
    created_at: datetime | None = None,
) -> None:
    _ensure_db()
    now = _timestamp()
    original_created_at = created_at or now
    db_session.execute(
        insert_profile_stmt,
        (
            user_id,
            username,
            email,
            full_name,
            role,
            status,
            original_created_at,
            now,
        ),
    )


def _get_profile(user_id: str) -> dict[str, Any] | None:
    _ensure_db()
    row = db_session.execute(select_profile_stmt, (user_id,)).one()
    if row is None:
        return None
    return {
        "user_id": row.user_id,
        "username": row.username,
        "email": row.email,
        "full_name": row.full_name,
        "role": row.role,
        "status": row.status or "active",
        "created_at": (row.created_at or _timestamp()).isoformat(),
        "updated_at": (row.updated_at or _timestamp()).isoformat(),
    }


async def _keycloak_get_user(token: str, user_id: str) -> dict[str, Any]:
    resp = await _http_request(
        "GET",
        _kc_admin_api(f"/users/{user_id}"),
        headers={"Authorization": f"Bearer {token}"},
        service_name="keycloak",
    )

    if resp.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if resp.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve user from Keycloak",
        )
    return resp.json()


async def _keycloak_list_users(token: str, search: str | None, limit: int) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"max": limit}
    if search:
        params["search"] = search
    resp = await _http_request(
        "GET",
        _kc_admin_api("/users"),
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        service_name="keycloak",
    )

    if resp.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to list users from Keycloak",
        )
    return resp.json()


def _display_name(user: dict[str, Any]) -> str:
    first = (user.get("firstName") or "").strip()
    last = (user.get("lastName") or "").strip()
    full = f"{first} {last}".strip()
    return full or (user.get("username") or "")


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
        "realm": settings.keycloak_realm,
    }


@app.post("/admin/users", response_model=UserProfileResponse, tags=["identity-admin"])
async def create_user(
    request: Request,
    payload: CreateUserRequest,
    _: dict[str, Any] = Depends(require_admin),
) -> UserProfileResponse:
    token = await _keycloak_admin_token()
    user_body = {
        "username": payload.username,
        "email": payload.email,
        "firstName": payload.first_name,
        "lastName": payload.last_name,
        "enabled": payload.enabled,
        "emailVerified": True,
    }
    create_resp = await _http_request(
        "POST",
        _kc_admin_api("/users"),
        headers={"Authorization": f"Bearer {token}"},
        json_body=user_body,
        service_name="keycloak",
    )

    if create_resp.status_code == status.HTTP_409_CONFLICT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists in Keycloak",
        )
    if create_resp.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to create user in Keycloak",
        )

    user_id = _extract_location_id(create_resp) or await _keycloak_find_user_id(
        token, payload.username
    )
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="User created but unable to resolve Keycloak user_id",
        )

    pwd_resp = await _http_request(
        "PUT",
        _kc_admin_api(f"/users/{user_id}/reset-password"),
        headers={"Authorization": f"Bearer {token}"},
        json_body={
            "type": "password",
            "value": payload.password,
            "temporary": False,
        },
        service_name="keycloak",
    )

    if pwd_resp.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to set user password in Keycloak",
        )

    await _keycloak_assign_roles(token, user_id, payload.roles)

    created_at = _timestamp()
    full_name = f"{payload.first_name} {payload.last_name}".strip()
    primary_role = payload.roles[0] if payload.roles else None
    user_status = "active" if payload.enabled else "suspended"
    _store_profile(
        user_id=user_id,
        username=payload.username,
        email=str(payload.email),
        full_name=full_name,
        role=primary_role,
        status=user_status,
        created_at=created_at,
    )

    profile = _get_profile(user_id)
    await _publish_event(
        "user.created.v1",
        {
            "user_id": user_id,
            "username": payload.username,
            "email": str(payload.email),
            "role": primary_role,
            "status": user_status,
        },
        extract_request_id(request),
    )
    return UserProfileResponse(**profile)


@app.patch("/admin/users/{user_id}/roles", response_model=UserProfileResponse, tags=["identity-admin"])
async def patch_user_roles(
    request: Request,
    user_id: str,
    payload: PatchUserRolesRequest,
    _: dict[str, Any] = Depends(require_admin),
) -> UserProfileResponse:
    token = await _keycloak_admin_token()
    kc_user = await _keycloak_get_user(token, user_id)
    await _keycloak_replace_roles(token, user_id, payload.roles)

    profile = _get_profile(user_id)
    primary_role = payload.roles[0] if payload.roles else None
    full_name = _display_name(kc_user)
    if profile:
        created = datetime.fromisoformat(profile["created_at"])
    else:
        created = _timestamp()
    _store_profile(
        user_id=user_id,
        username=kc_user.get("username") or "",
        email=kc_user.get("email"),
        full_name=full_name,
        role=primary_role,
        status="active" if kc_user.get("enabled", True) else "suspended",
        created_at=created,
    )
    profile = UserProfileResponse(**_get_profile(user_id))
    await _publish_event(
        "user.role.assigned.v1",
        {
            "user_id": user_id,
            "role": primary_role,
        },
        extract_request_id(request),
    )
    return profile


@app.get("/admin/users/{user_id}", response_model=UserProfileResponse, tags=["identity-admin"])
async def get_user(
    user_id: str,
    _: dict[str, Any] = Depends(require_admin),
) -> UserProfileResponse:
    token = await _keycloak_admin_token()
    kc_user = await _keycloak_get_user(token, user_id)
    profile = _get_profile(user_id)
    if profile:
        return UserProfileResponse(**profile)

    now = _timestamp().isoformat()
    return UserProfileResponse(
        user_id=user_id,
        username=kc_user.get("username") or "",
        email=kc_user.get("email"),
        full_name=_display_name(kc_user),
        role=None,
        status="active" if kc_user.get("enabled", True) else "suspended",
        created_at=now,
        updated_at=now,
    )


@app.get("/admin/users", response_model=list[UserProfileResponse], tags=["identity-admin"])
async def list_users(
    search: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=25, ge=1, le=100),
    _: dict[str, Any] = Depends(require_admin),
) -> list[UserProfileResponse]:
    token = await _keycloak_admin_token()
    users = await _keycloak_list_users(token, search=search, limit=limit)
    output: list[UserProfileResponse] = []
    now = _timestamp().isoformat()
    for user in users:
        user_id = user.get("id")
        if not user_id:
            continue
        profile = _get_profile(user_id)
        if profile:
            output.append(UserProfileResponse(**profile))
            continue
        output.append(
            UserProfileResponse(
                user_id=user_id,
                username=user.get("username") or "",
                email=user.get("email"),
                full_name=_display_name(user),
                role=None,
                status="active" if user.get("enabled", True) else "suspended",
                created_at=now,
                updated_at=now,
            )
        )
    return output
