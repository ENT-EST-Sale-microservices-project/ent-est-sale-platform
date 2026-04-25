from __future__ import annotations

import os
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from .runtime import setup_service_runtime

AUTH_CORE_BASE_URL = os.getenv("AUTH_CORE_BASE_URL", "http://ms-auth-core:8000")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("GATEWAY_TIMEOUT_SECONDS", "8"))
IDEMPOTENT_RETRIES = int(os.getenv("GATEWAY_IDEMPOTENT_RETRIES", "2"))
COURSE_CONTENT_BASE_URL = os.getenv("GATEWAY_COURSE_CONTENT_URL", "http://ms-course-content:8000")
COURSE_ACCESS_BASE_URL = os.getenv("GATEWAY_COURSE_ACCESS_URL", "http://ms-course-access:8000")
IDENTITY_ADMIN_BASE_URL = os.getenv("GATEWAY_IDENTITY_ADMIN_URL", "http://ms-identity-admin:8000")
NOTIFICATION_BASE_URL = os.getenv("GATEWAY_NOTIFICATION_URL", "http://ms-notification:8000")
CALENDAR_BASE_URL = os.getenv("GATEWAY_CALENDAR_URL", "http://ms-calendar-schedule:8000")
FORUM_BASE_URL = os.getenv("GATEWAY_FORUM_URL", "http://ms-forum-chat:8000")
EXAM_BASE_URL = os.getenv("GATEWAY_EXAM_URL", "http://ms-exam-assignment:8000")

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
    if resp.status_code == status.HTTP_400_BAD_REQUEST:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=_extract_detail(resp))
    if resp.status_code == status.HTTP_401_UNAUTHORIZED:
        return _unauthorized(_extract_detail(resp))
    if resp.status_code == status.HTTP_403_FORBIDDEN:
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_extract_detail(resp))
    if resp.status_code == status.HTTP_404_NOT_FOUND:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_extract_detail(resp))
    if resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=_extract_detail(resp))
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


@app.patch("/api/notifications/{notif_id}/read", tags=["notifications"])
async def gateway_mark_one_notification_read(
    notif_id: str,
    claims: dict[str, Any] = Depends(verify_jwt_and_get_claims),
) -> Any:
    user_id = claims.get("sub")
    if not user_id:
        raise _unauthorized("Invalid token claims")

    resp = await _request_downstream(
        "PATCH",
        f"{NOTIFICATION_BASE_URL}/notifications/{user_id}/{notif_id}/read",
        service_name="ms-notification",
    )

    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "ms-notification")
    return resp.json()


@app.patch("/api/notifications/read-all", tags=["notifications"])
async def gateway_mark_notifications_read(
    claims: dict[str, Any] = Depends(verify_jwt_and_get_claims),
) -> Any:
    user_id = claims.get("sub")
    if not user_id:
        raise _unauthorized("Invalid token claims")

    resp = await _request_downstream(
        "PATCH",
        f"{NOTIFICATION_BASE_URL}/notifications/{user_id}/read-all",
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
            courses_resp = await _request_downstream(
                "GET",
                f"{COURSE_CONTENT_BASE_URL}/courses",
                headers={"Authorization": authorization or ""},
                service_name="course-content",
            )
            courses = courses_resp.json() if courses_resp.status_code == 200 else []
            stats["total_courses"] = len(courses)
            stats["recent_uploads"] = sum(len(c.get("assets", [])) for c in courses)

            # Count published assignments
            assign_resp = await _request_downstream(
                "GET",
                f"{EXAM_BASE_URL}/assignments",
                headers={"Authorization": authorization or ""},
                service_name="exam",
            )
            assignments = assign_resp.json() if assign_resp.status_code == 200 else []
            stats["total_students"] = len([a for a in assignments if a.get("status") == "published"])

        elif "student" in roles:
            # Get available courses
            courses_resp = await _request_downstream(
                "GET",
                f"{COURSE_ACCESS_BASE_URL}/courses",
                headers={"Authorization": authorization or ""},
                service_name="course-access",
            )
            courses = courses_resp.json() if courses_resp.status_code == 200 else []
            stats["enrolled_courses"] = len(courses)

            # Get upcoming deadlines from exam service
            assign_resp = await _request_downstream(
                "GET",
                f"{EXAM_BASE_URL}/assignments",
                params={"status": "published"},
                headers={"Authorization": authorization or ""},
                service_name="exam",
            )
            assignments = assign_resp.json() if assign_resp.status_code == 200 else []
            now = datetime.now(timezone.utc)
            week_ahead = now + timedelta(days=7)
            upcoming = []
            for a in assignments:
                due = a.get("due_date")
                if due:
                    try:
                        due_dt = datetime.fromisoformat(due.replace("Z", "+00:00"))
                        if now < due_dt <= week_ahead:
                            upcoming.append(a)
                    except ValueError:
                        pass
            stats["upcoming_deadlines"] = len(upcoming)
            stats["completed_credits"] = 0
            
    except Exception as e:
        # Graceful fallback if a downstream service is down
        pass

    return stats


# ── Calendar routes ──────────────────────────────────────────────────────────

@app.post("/api/calendar/events", tags=["calendar"], status_code=201)
async def gateway_create_calendar_event(
    payload: dict[str, Any],
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(require_roles("teacher", "admin")),
) -> Any:
    resp = await _request_downstream(
        "POST",
        f"{CALENDAR_BASE_URL}/calendar/events",
        json_payload=payload,
        headers={"Authorization": authorization or ""},
        service_name="calendar",
    )
    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "calendar")
    return resp.json()


@app.get("/api/calendar/events", tags=["calendar"])
async def gateway_list_calendar_events(
    month: str | None = Query(default=None, description="Filter YYYY-MM"),
    module_code: str | None = Query(default=None),
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(verify_jwt_and_get_claims),
) -> Any:
    params: dict[str, Any] = {}
    if month:
        params["month"] = month
    if module_code:
        params["module_code"] = module_code

    resp = await _request_downstream(
        "GET",
        f"{CALENDAR_BASE_URL}/calendar/events",
        params=params,
        headers={"Authorization": authorization or ""},
        service_name="calendar",
    )
    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "calendar")
    return resp.json()


@app.get("/api/calendar/events/{event_id}", tags=["calendar"])
async def gateway_get_calendar_event(
    event_id: str,
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(verify_jwt_and_get_claims),
) -> Any:
    resp = await _request_downstream(
        "GET",
        f"{CALENDAR_BASE_URL}/calendar/events/{event_id}",
        headers={"Authorization": authorization or ""},
        service_name="calendar",
    )
    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "calendar")
    return resp.json()


@app.patch("/api/calendar/events/{event_id}", tags=["calendar"])
async def gateway_patch_calendar_event(
    event_id: str,
    payload: dict[str, Any],
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(require_roles("teacher", "admin")),
) -> Any:
    resp = await _request_downstream(
        "PATCH",
        f"{CALENDAR_BASE_URL}/calendar/events/{event_id}",
        json_payload=payload,
        headers={"Authorization": authorization or ""},
        service_name="calendar",
    )
    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "calendar")
    return resp.json()


@app.delete("/api/calendar/events/{event_id}", tags=["calendar"], status_code=204)
async def gateway_delete_calendar_event(
    event_id: str,
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(require_roles("teacher", "admin")),
) -> None:
    resp = await _request_downstream(
        "DELETE",
        f"{CALENDAR_BASE_URL}/calendar/events/{event_id}",
        headers={"Authorization": authorization or ""},
        service_name="calendar",
    )
    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "calendar")


# ── Forum routes ─────────────────────────────────────────────────────────────
# WebSocket chat connects directly to ms-forum-chat:
#   ws://localhost:8016/chat/ws?token=<jwt>&room=<module_code>
# The gateway cannot transparently proxy WebSocket upgrades, so the frontend
# targets the forum service port directly for real-time chat.

@app.post("/api/forum/threads", tags=["forum"], status_code=201)
async def gateway_create_thread(
    payload: dict[str, Any],
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(verify_jwt_and_get_claims),
) -> Any:
    resp = await _request_downstream(
        "POST",
        f"{FORUM_BASE_URL}/forum/threads",
        json_payload=payload,
        headers={"Authorization": authorization or ""},
        service_name="forum",
    )
    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "forum")
    return resp.json()


@app.get("/api/forum/threads", tags=["forum"])
async def gateway_list_threads(
    module_code: str | None = Query(default=None),
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(verify_jwt_and_get_claims),
) -> Any:
    params: dict[str, Any] = {}
    if module_code:
        params["module_code"] = module_code

    resp = await _request_downstream(
        "GET",
        f"{FORUM_BASE_URL}/forum/threads",
        params=params,
        headers={"Authorization": authorization or ""},
        service_name="forum",
    )
    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "forum")
    return resp.json()


@app.get("/api/forum/threads/{thread_id}", tags=["forum"])
async def gateway_get_thread(
    thread_id: str,
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(verify_jwt_and_get_claims),
) -> Any:
    resp = await _request_downstream(
        "GET",
        f"{FORUM_BASE_URL}/forum/threads/{thread_id}",
        headers={"Authorization": authorization or ""},
        service_name="forum",
    )
    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "forum")
    return resp.json()


@app.post("/api/forum/threads/{thread_id}/messages", tags=["forum"], status_code=201)
async def gateway_post_message(
    thread_id: str,
    payload: dict[str, Any],
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(verify_jwt_and_get_claims),
) -> Any:
    resp = await _request_downstream(
        "POST",
        f"{FORUM_BASE_URL}/forum/threads/{thread_id}/messages",
        json_payload=payload,
        headers={"Authorization": authorization or ""},
        service_name="forum",
    )
    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "forum")
    return resp.json()


# ── Exam / Assignment routes ─────────────────────────────────────────────────

@app.post("/api/assignments", tags=["exams"], status_code=201)
async def gateway_create_assignment(
    payload: dict[str, Any],
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(require_roles("teacher", "admin")),
) -> Any:
    resp = await _request_downstream(
        "POST",
        f"{EXAM_BASE_URL}/assignments",
        json_payload=payload,
        headers={"Authorization": authorization or ""},
        service_name="exam",
    )
    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "exam")
    return resp.json()


@app.get("/api/assignments", tags=["exams"])
async def gateway_list_assignments(
    module_code: str | None = Query(default=None),
    status: str | None = Query(default=None),
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(verify_jwt_and_get_claims),
) -> Any:
    params: dict[str, Any] = {}
    if module_code:
        params["module_code"] = module_code
    if status:
        params["status"] = status

    resp = await _request_downstream(
        "GET",
        f"{EXAM_BASE_URL}/assignments",
        params=params,
        headers={"Authorization": authorization or ""},
        service_name="exam",
    )
    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "exam")
    return resp.json()


@app.get("/api/assignments/{assignment_id}", tags=["exams"])
async def gateway_get_assignment(
    assignment_id: str,
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(verify_jwt_and_get_claims),
) -> Any:
    resp = await _request_downstream(
        "GET",
        f"{EXAM_BASE_URL}/assignments/{assignment_id}",
        headers={"Authorization": authorization or ""},
        service_name="exam",
    )
    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "exam")
    return resp.json()


@app.post("/api/assignments/{assignment_id}/submissions", tags=["exams"], status_code=201)
async def gateway_submit_assignment(
    assignment_id: str,
    file: UploadFile | None = File(default=None),
    content_text: str = Form(default=""),
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(require_roles("student")),
) -> Any:
    if file is not None:
        content = await file.read()
        files = {"file": (file.filename, content, file.content_type or "application/octet-stream")}
        resp = await _request_downstream(
            "POST",
            f"{EXAM_BASE_URL}/assignments/{assignment_id}/submissions",
            files=files,
            params={"content_text": content_text},
            headers={"Authorization": authorization or ""},
            service_name="exam",
        )
    else:
        # text-only submission via form data
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            resp = await client.post(
                f"{EXAM_BASE_URL}/assignments/{assignment_id}/submissions",
                data={"content_text": content_text},
                headers={"Authorization": authorization or ""},
            )
    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "exam")
    return resp.json()


@app.get("/api/assignments/{assignment_id}/submissions", tags=["exams"])
async def gateway_list_submissions(
    assignment_id: str,
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(verify_jwt_and_get_claims),
) -> Any:
    resp = await _request_downstream(
        "GET",
        f"{EXAM_BASE_URL}/assignments/{assignment_id}/submissions",
        headers={"Authorization": authorization or ""},
        service_name="exam",
    )
    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "exam")
    return resp.json()


@app.post("/api/assignments/{assignment_id}/submissions/{submission_id}/grade", tags=["exams"])
async def gateway_grade_submission(
    assignment_id: str,
    submission_id: str,
    payload: dict[str, Any],
    authorization: str | None = Header(default=None),
    _: dict[str, Any] = Depends(require_roles("teacher", "admin")),
) -> Any:
    resp = await _request_downstream(
        "POST",
        f"{EXAM_BASE_URL}/assignments/{assignment_id}/submissions/{submission_id}/grade",
        json_payload=payload,
        headers={"Authorization": authorization or ""},
        service_name="exam",
    )
    if resp.status_code >= 400:
        raise _map_downstream_error(resp, "exam")
    return resp.json()
