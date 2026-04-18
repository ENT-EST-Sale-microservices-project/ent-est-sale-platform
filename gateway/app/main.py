from __future__ import annotations

import os
import asyncio
from typing import Any

import httpx
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from .runtime import setup_service_runtime

AUTH_CORE_BASE_URL = os.getenv("AUTH_CORE_BASE_URL", "http://ms-auth-core:8000")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("GATEWAY_TIMEOUT_SECONDS", "8"))
IDEMPOTENT_RETRIES = int(os.getenv("GATEWAY_IDEMPOTENT_RETRIES", "2"))
COURSE_CONTENT_BASE_URL = os.getenv("GATEWAY_COURSE_CONTENT_URL", "http://ms-course-content:8000")
COURSE_ACCESS_BASE_URL = os.getenv("GATEWAY_COURSE_ACCESS_URL", "http://ms-course-access:8000")
IDENTITY_ADMIN_BASE_URL = os.getenv("GATEWAY_IDENTITY_ADMIN_URL", "http://ms-identity-admin:8000")
NOTIFICATION_BASE_URL = os.getenv("GATEWAY_NOTIFICATION_URL", "http://ms-notification:8000")

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "GATEWAY_CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000,http://localhost:4173",
    ).split(",")
    if origin.strip()
]

app = FastAPI(
    title="MS-API-Gateway",
    version="0.1.0",
    description="API gateway with JWT guard delegated to ms-auth-core.",
)
setup_service_runtime(app, "ms-api-gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["x-request-id", "x-correlation-id"],
)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def _request_downstream(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_payload: Any = None,
    files: Any = None,
    params: dict[str, Any] | None = None,
    service_name: str,
) -> httpx.Response:
    attempts = IDEMPOTENT_RETRIES + 1 if method.upper() == "GET" else 1
    backoff = 0.15
    last_exc: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                return await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_payload,
                    files=files,
                    params=params,
                )
        except httpx.RequestError as exc:
            last_exc = exc
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
        detail=f"{service_name} unavailable: {last_exc.__class__.__name__ if last_exc else 'UnknownError'}",
    )


async def verify_jwt_and_get_claims(
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _unauthorized("Missing bearer token")

    resp = await _request_downstream(
        "GET",
        f"{AUTH_CORE_BASE_URL}/auth/me",
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

    return resp.json()


def require_roles(*required_roles: str):
    async def _role_guard(claims: dict[str, Any] = Depends(verify_jwt_and_get_claims)) -> dict[str, Any]:
        token_roles = set((claims.get("realm_access") or {}).get("roles", []))
        if not token_roles.intersection(required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden. Required one of roles: {', '.join(required_roles)}",
            )
        return claims

    return _role_guard


def _access_payload(message: str, claims: dict[str, Any]) -> dict[str, Any]:
    return {
        "message": message,
        "sub": claims.get("sub"),
        "preferred_username": claims.get("preferred_username"),
        "roles": (claims.get("realm_access") or {}).get("roles", []),
    }

def _extract_roles(claims: dict[str, Any]) -> set[str]:
    return set((claims.get("realm_access") or {}).get("roles", []))


def _extract_detail(resp: httpx.Response) -> str:
    try:
        payload = resp.json()
        if isinstance(payload, dict) and payload.get("detail"):
            return str(payload.get("detail"))
    except Exception:
        pass
    return resp.text or "Downstream error"


def _map_downstream_error(resp: httpx.Response, service_name: str) -> HTTPException:
    if resp.status_code == status.HTTP_401_UNAUTHORIZED:
        return _unauthorized(_extract_detail(resp))
    if resp.status_code == status.HTTP_403_FORBIDDEN:
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_extract_detail(resp))
    if resp.status_code == status.HTTP_404_NOT_FOUND:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_extract_detail(resp))
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"{service_name} error: {_extract_detail(resp)}",
    )


@app.get("/gateway/health", tags=["gateway"])
async def gateway_health() -> dict[str, str]:
    return {"status": "ok", "service": "ms-api-gateway"}


@app.get("/api/me", tags=["auth-proxy"])
async def gateway_me(claims: dict[str, Any] = Depends(verify_jwt_and_get_claims)) -> dict[str, Any]:
    return claims


@app.get("/api/protected/ping", tags=["protected"])
async def protected_ping(
    claims: dict[str, Any] = Depends(verify_jwt_and_get_claims),
) -> dict[str, Any]:
    return _access_payload("pong", claims)


@app.get("/api/protected/admin", tags=["protected"])
async def protected_admin(
    claims: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    return _access_payload("admin access granted", claims)


@app.get("/api/protected/teacher", tags=["protected"])
async def protected_teacher(
    claims: dict[str, Any] = Depends(require_roles("teacher")),
) -> dict[str, Any]:
    return _access_payload("teacher access granted", claims)


@app.get("/api/protected/student", tags=["protected"])
async def protected_student(
    claims: dict[str, Any] = Depends(require_roles("student")),
) -> dict[str, Any]:
    return _access_payload("student access granted", claims)


@app.get("/api/protected/academic", tags=["protected"])
async def protected_academic(
    claims: dict[str, Any] = Depends(require_roles("teacher", "admin")),
) -> dict[str, Any]:
    return _access_payload("academic staff access granted", claims)


@app.get("/api/content/courses", tags=["courses-content"])
async def gateway_list_content_courses(
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(require_roles("teacher", "admin")),
) -> Any:
    resp = await _request_downstream(
        "GET",
        f"{COURSE_CONTENT_BASE_URL}/courses",
        headers={"Authorization": authorization or ""},
        service_name="course-content",
    )

    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "course-content")
    return resp.json()


@app.post("/api/content/courses", tags=["courses-content"])
async def gateway_create_course(
    payload: dict[str, Any],
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(require_roles("teacher", "admin")),
) -> Any:
    resp = await _request_downstream(
        "POST",
        f"{COURSE_CONTENT_BASE_URL}/courses",
        json_payload=payload,
        headers={"Authorization": authorization or ""},
        service_name="course-content",
    )

    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "course-content")
    return resp.json()


@app.post("/api/content/courses/{course_id}/assets", tags=["courses-content"])
async def gateway_upload_course_asset(
    course_id: str,
    file: UploadFile = File(...),
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(require_roles("teacher", "admin")),
) -> Any:
    content = await file.read()
    files = {"file": (file.filename, content, file.content_type or "application/octet-stream")}
    resp = await _request_downstream(
        "POST",
        f"{COURSE_CONTENT_BASE_URL}/courses/{course_id}/assets",
        files=files,
        headers={"Authorization": authorization or ""},
        service_name="course-content",
    )

    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "course-content")
    return resp.json()


@app.put("/api/content/courses/{course_id}", tags=["courses-content"])
async def gateway_update_course(
    course_id: str,
    payload: dict[str, Any],
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(require_roles("teacher", "admin")),
) -> Any:
    resp = await _request_downstream(
        "PUT",
        f"{COURSE_CONTENT_BASE_URL}/courses/{course_id}",
        json_payload=payload,
        headers={"Authorization": authorization or ""},
        service_name="course-content",
    )

    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "course-content")
    return resp.json()


@app.delete("/api/content/courses/{course_id}", tags=["courses-content"])
async def gateway_delete_course(
    course_id: str,
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(require_roles("teacher", "admin")),
) -> Any:
    resp = await _request_downstream(
        "DELETE",
        f"{COURSE_CONTENT_BASE_URL}/courses/{course_id}",
        headers={"Authorization": authorization or ""},
        service_name="course-content",
    )

    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "course-content")
    return resp.json()


@app.delete("/api/content/courses/{course_id}/assets/{asset_id}", tags=["courses-content"])
async def gateway_delete_course_asset(
    course_id: str,
    asset_id: str,
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(require_roles("teacher", "admin")),
) -> Any:
    resp = await _request_downstream(
        "DELETE",
        f"{COURSE_CONTENT_BASE_URL}/courses/{course_id}/assets/{asset_id}",
        headers={"Authorization": authorization or ""},
        service_name="course-content",
    )

    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "course-content")
    return resp.json()


@app.get("/api/access/courses", tags=["courses-access"])
async def gateway_list_courses(
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(require_roles("student")),
) -> Any:
    resp = await _request_downstream(
        "GET",
        f"{COURSE_ACCESS_BASE_URL}/courses",
        headers={"Authorization": authorization or ""},
        service_name="course-access",
    )

    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "course-access")
    return resp.json()


@app.get("/api/access/courses/{course_id}", tags=["courses-access"])
async def gateway_get_course(
    course_id: str,
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(require_roles("student")),
) -> Any:
    resp = await _request_downstream(
        "GET",
        f"{COURSE_ACCESS_BASE_URL}/courses/{course_id}",
        headers={"Authorization": authorization or ""},
        service_name="course-access",
    )

    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "course-access")
    return resp.json()


@app.post("/api/access/courses/{course_id}/download-links", tags=["courses-access"])
async def gateway_download_link(
    course_id: str,
    payload: dict[str, Any],
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(require_roles("student")),
) -> Any:
    resp = await _request_downstream(
        "POST",
        f"{COURSE_ACCESS_BASE_URL}/courses/{course_id}/download-links",
        json_payload=payload,
        headers={"Authorization": authorization or ""},
        service_name="course-access",
    )

    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "course-access")
    return resp.json()


@app.post("/api/admin/users", tags=["identity-admin"])
async def gateway_admin_create_user(
    payload: dict[str, Any],
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> Any:
    resp = await _request_downstream(
        "POST",
        f"{IDENTITY_ADMIN_BASE_URL}/admin/users",
        json_payload=payload,
        headers={"Authorization": authorization or ""},
        service_name="identity-admin",
    )

    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "identity-admin")
    return resp.json()


@app.patch("/api/admin/users/{user_id}/roles", tags=["identity-admin"])
async def gateway_admin_patch_user_roles(
    user_id: str,
    payload: dict[str, Any],
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> Any:
    resp = await _request_downstream(
        "PATCH",
        f"{IDENTITY_ADMIN_BASE_URL}/admin/users/{user_id}/roles",
        json_payload=payload,
        headers={"Authorization": authorization or ""},
        service_name="identity-admin",
    )

    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "identity-admin")
    return resp.json()


@app.get("/api/admin/users/{user_id}", tags=["identity-admin"])
async def gateway_admin_get_user(
    user_id: str,
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> Any:
    resp = await _request_downstream(
        "GET",
        f"{IDENTITY_ADMIN_BASE_URL}/admin/users/{user_id}",
        headers={"Authorization": authorization or ""},
        service_name="identity-admin",
    )

    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "identity-admin")
    return resp.json()


@app.get("/api/admin/users", tags=["identity-admin"])
async def gateway_admin_list_users(
    search: str | None = None,
    limit: int = 25,
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> Any:
    params: dict[str, Any] = {"limit": limit}
    if search:
        params["search"] = search

    resp = await _request_downstream(
        "GET",
        f"{IDENTITY_ADMIN_BASE_URL}/admin/users",
        params=params,
        headers={"Authorization": authorization or ""},
        service_name="identity-admin",
    )

    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "identity-admin")
    return resp.json()


@app.get("/api/notifications", tags=["notifications"])
async def gateway_list_notifications(
    claims: dict[str, Any] = Depends(verify_jwt_and_get_claims),
) -> Any:
    user_id = claims.get("sub")
    if not user_id:
        raise _unauthorized("Invalid token claims")

    resp = await _request_downstream(
        "GET",
        f"{NOTIFICATION_BASE_URL}/notifications/{user_id}",
        service_name="ms-notification",
    )

    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "ms-notification")
    return resp.json()


@app.get("/api/stats", tags=["stats"])
async def gateway_stats(
    authorization: str | None = Header(default=None),
    claims: dict[str, Any] = Depends(verify_jwt_and_get_claims),
) -> dict[str, Any]:
    roles = _extract_roles(claims)
    stats = {}

    try:
        if "admin" in roles:
            # Get users count
            resp = await _request_downstream(
                "GET",
                f"{IDENTITY_ADMIN_BASE_URL}/admin/users",
                params={"limit": 1000},
                headers={"Authorization": authorization or ""},
                service_name="identity-admin",
            )
            users = resp.json() if resp.status_code == 200 else []
            stats["total_users"] = len(users)
            stats["active_sessions"] = "Unknown"  # Not currently tracked
            stats["system_status"] = "Healthy"
            
        elif "teacher" in roles:
            # Get teacher courses
            resp = await _request_downstream(
                "GET",
                f"{COURSE_CONTENT_BASE_URL}/courses",
                headers={"Authorization": authorization or ""},
                service_name="course-content",
            )
            courses = resp.json() if resp.status_code == 200 else []
            stats["total_courses"] = len(courses)
            stats["total_students"] = "Unknown" 
            stats["recent_uploads"] = sum(len(c.get("assets", [])) for c in courses)

        elif "student" in roles:
            # Get available courses
            resp = await _request_downstream(
                "GET",
                f"{COURSE_ACCESS_BASE_URL}/courses",
                headers={"Authorization": authorization or ""},
                service_name="course-access",
            )
            courses = resp.json() if resp.status_code == 200 else []
            stats["enrolled_courses"] = len(courses)
            stats["upcoming_deadlines"] = 0
            stats["completed_credits"] = 0
            
    except Exception as e:
        # Graceful fallback if a downstream service is down
        pass
        
    return stats
