from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import aio_pika
import httpx
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from cassandra.policies import RoundRobinPolicy
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from .runtime import extract_request_id, setup_service_runtime


@dataclass(frozen=True)
class Settings:
    auth_core_base_url: str = os.getenv("AUTH_CORE_BASE_URL", "http://ms-auth-core:8000")
    timeout_seconds: float = float(os.getenv("CALENDAR_TIMEOUT_SECONDS", "8"))
    idempotent_retries: int = int(os.getenv("CALENDAR_IDEMPOTENT_RETRIES", "2"))

    cassandra_contact_points: tuple[str, ...] = tuple(
        h.strip()
        for h in os.getenv("CASSANDRA_CONTACT_POINTS", "cassandra").split(",")
        if h.strip()
    )
    cassandra_port: int = int(os.getenv("CASSANDRA_PORT", "9042"))
    cassandra_username: str = os.getenv("CASSANDRA_USERNAME", "cassandra")
    cassandra_password: str = os.getenv("CASSANDRA_PASSWORD", "ChangeMe_123!")
    cassandra_keyspace: str = os.getenv("CASSANDRA_KEYSPACE", "ent_est")
    events_table: str = os.getenv("CALENDAR_EVENTS_TABLE", "calendar_events")


settings = Settings()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://ent:ChangeMe_123!@rabbitmq:5672/")
EVENTS_EXCHANGE = os.getenv("EVENTS_EXCHANGE", "ent.events.topic")
ENABLE_EVENT_PUBLISHING = os.getenv("ENABLE_EVENT_PUBLISHING", "true").lower() in {
    "1", "true", "yes", "on",
}

WRITE_ROLES: frozenset[str] = frozenset(
    r.strip()
    for r in os.getenv("CALENDAR_WRITE_ROLES", "teacher,admin").split(",")
    if r.strip()
)

app = FastAPI(
    title="MS-Calendar-Schedule",
    version="0.1.0",
    description="Academic calendar and schedule management for ENT EST Salé.",
)
setup_service_runtime(app, "ms-calendar-schedule")

# ── Cassandra globals ────────────────────────────────────────────────────────
cluster: Cluster | None = None
db_session = None
insert_event_stmt = None
select_event_stmt = None
select_all_events_stmt = None
delete_event_stmt = None


# ── Pydantic models ──────────────────────────────────────────────────────────

class CreateEventRequest(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=2000)
    event_type: str = Field(default="course", description="course | exam | deadline | other")
    start_time: datetime
    end_time: datetime
    module_code: str = Field(default="all", max_length=50)
    target_group: str = Field(default="all", max_length=100)


class PatchEventRequest(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    event_type: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    module_code: str | None = Field(default=None, max_length=50)
    target_group: str | None = Field(default=None, max_length=100)


class CalendarEventResponse(BaseModel):
    event_id: str
    title: str
    description: str
    event_type: str
    start_time: str
    end_time: str
    module_code: str
    target_group: str
    created_by: str
    created_at: str


# ── Helpers ──────────────────────────────────────────────────────────────────

def _now() -> datetime:
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


async def _http_get(url: str, *, headers: dict[str, str]) -> httpx.Response:
    attempts = settings.idempotent_retries + 1
    backoff = 0.15
    for attempt in range(1, attempts + 1):
        try:
            async with httpx.AsyncClient(timeout=settings.timeout_seconds) as client:
                return await client.get(url, headers=headers)
        except httpx.RequestError as exc:
            if attempt < attempts:
                await asyncio.sleep(backoff)
                backoff *= 2
                continue
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"auth-core unavailable: {exc.__class__.__name__}",
            ) from exc
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="auth-core unavailable")


async def _get_claims(authorization: str | None) -> dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _unauthorized("Missing bearer token")
    resp = await _http_get(
        f"{settings.auth_core_base_url}/auth/me",
        headers={"Authorization": authorization},
    )
    if resp.status_code == status.HTTP_401_UNAUTHORIZED:
        raise _unauthorized("Invalid or expired token")
    if resp.status_code >= 400:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="auth-core error")
    return resp.json()


async def require_auth(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    return await _get_claims(authorization)


async def require_write(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    claims = await _get_claims(authorization)
    if not _extract_roles(claims).intersection(WRITE_ROLES):
        raise _forbidden(f"Requires one of roles: {', '.join(sorted(WRITE_ROLES))}")
    return claims


async def _publish_event(event_type: str, payload: dict[str, Any], correlation_id: str | None) -> None:
    if not ENABLE_EVENT_PUBLISHING:
        return
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                EVENTS_EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True,
            )
            envelope = {
                "event_id": str(uuid4()),
                "event_type": event_type,
                "occurred_at": _now().isoformat(),
                "producer": "ms-calendar-schedule",
                "correlation_id": correlation_id,
                "payload": payload,
            }
            routing_key = ".".join(event_type.split(".")[:2])
            await exchange.publish(
                aio_pika.Message(
                    body=json.dumps(envelope).encode(),
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=routing_key,
            )
    except Exception:
        pass  # event publishing failure must not break the main flow


# ── Cassandra setup ──────────────────────────────────────────────────────────

def _ensure_db() -> None:
    global cluster, db_session, insert_event_stmt, select_event_stmt
    global select_all_events_stmt, delete_event_stmt

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
        f"CREATE KEYSPACE IF NOT EXISTS {settings.cassandra_keyspace} "
        "WITH replication = {'class':'SimpleStrategy','replication_factor':1};"
    )
    db_session.set_keyspace(settings.cassandra_keyspace)

    db_session.execute(
        f"CREATE TABLE IF NOT EXISTS {settings.events_table} ("
        "event_id     text PRIMARY KEY,"
        "title        text,"
        "description  text,"
        "event_type   text,"
        "start_time   timestamp,"
        "end_time     timestamp,"
        "module_code  text,"
        "target_group text,"
        "created_by   text,"
        "created_at   timestamp"
        ");"
    )

    insert_event_stmt = db_session.prepare(
        f"INSERT INTO {settings.events_table} "
        "(event_id, title, description, event_type, start_time, end_time, "
        "module_code, target_group, created_by, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    select_event_stmt = db_session.prepare(
        f"SELECT event_id, title, description, event_type, start_time, end_time, "
        f"module_code, target_group, created_by, created_at "
        f"FROM {settings.events_table} WHERE event_id = ?"
    )
    select_all_events_stmt = db_session.prepare(
        f"SELECT event_id, title, description, event_type, start_time, end_time, "
        f"module_code, target_group, created_by, created_at "
        f"FROM {settings.events_table}"
    )
    delete_event_stmt = db_session.prepare(
        f"DELETE FROM {settings.events_table} WHERE event_id = ?"
    )


def _row_to_response(row: Any) -> CalendarEventResponse:
    return CalendarEventResponse(
        event_id=row.event_id,
        title=row.title or "",
        description=row.description or "",
        event_type=row.event_type or "course",
        start_time=row.start_time.isoformat() if row.start_time else "",
        end_time=row.end_time.isoformat() if row.end_time else "",
        module_code=row.module_code or "all",
        target_group=row.target_group or "all",
        created_by=row.created_by or "",
        created_at=row.created_at.isoformat() if row.created_at else "",
    )


# ── Lifecycle ────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup() -> None:
    _ensure_db()


@app.on_event("shutdown")
def shutdown() -> None:
    if cluster is not None:
        cluster.shutdown()


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/calendar/health", tags=["calendar"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ms-calendar-schedule"}


@app.post("/calendar/events", response_model=CalendarEventResponse, status_code=201, tags=["calendar"])
async def create_event(
    request: Request,
    payload: CreateEventRequest,
    claims: dict[str, Any] = Depends(require_write),
) -> CalendarEventResponse:
    if payload.end_time <= payload.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_time must be after start_time",
        )

    _ensure_db()
    event_id = str(uuid4())
    now = _now()
    creator = claims.get("sub") or "unknown"

    db_session.execute(
        insert_event_stmt,
        (
            event_id,
            payload.title,
            payload.description,
            payload.event_type,
            payload.start_time,
            payload.end_time,
            payload.module_code,
            payload.target_group,
            creator,
            now,
        ),
    )

    await _publish_event(
        "calendar.event.created.v1",
        {
            "event_id": event_id,
            "title": payload.title,
            "event_type": payload.event_type,
            "start_time": payload.start_time.isoformat(),
            "module_code": payload.module_code,
            "created_by": creator,
        },
        extract_request_id(request),
    )

    row = db_session.execute(select_event_stmt, (event_id,)).one()
    return _row_to_response(row)


@app.get("/calendar/events", response_model=list[CalendarEventResponse], tags=["calendar"])
async def list_events(
    month: str | None = Query(default=None, description="Filter by month: YYYY-MM"),
    module_code: str | None = Query(default=None, max_length=50),
    _: dict[str, Any] = Depends(require_auth),
) -> list[CalendarEventResponse]:
    _ensure_db()
    rows = db_session.execute(select_all_events_stmt).all()

    results = []
    for row in rows:
        if module_code and row.module_code not in (module_code, "all"):
            continue
        if month and row.start_time:
            row_month = row.start_time.strftime("%Y-%m")
            if row_month != month:
                continue
        results.append(_row_to_response(row))

    results.sort(key=lambda e: e.start_time)
    return results


@app.get("/calendar/events/{event_id}", response_model=CalendarEventResponse, tags=["calendar"])
async def get_event(
    event_id: str,
    _: dict[str, Any] = Depends(require_auth),
) -> CalendarEventResponse:
    _ensure_db()
    row = db_session.execute(select_event_stmt, (event_id,)).one()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return _row_to_response(row)


@app.patch("/calendar/events/{event_id}", response_model=CalendarEventResponse, tags=["calendar"])
async def patch_event(
    event_id: str,
    payload: PatchEventRequest,
    claims: dict[str, Any] = Depends(require_write),
) -> CalendarEventResponse:
    _ensure_db()
    row = db_session.execute(select_event_stmt, (event_id,)).one()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    new_start = payload.start_time or row.start_time
    new_end = payload.end_time or row.end_time
    if new_end <= new_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_time must be after start_time",
        )

    db_session.execute(
        insert_event_stmt,
        (
            event_id,
            payload.title if payload.title is not None else row.title,
            payload.description if payload.description is not None else (row.description or ""),
            payload.event_type if payload.event_type is not None else row.event_type,
            new_start,
            new_end,
            payload.module_code if payload.module_code is not None else row.module_code,
            payload.target_group if payload.target_group is not None else row.target_group,
            row.created_by,
            row.created_at,
        ),
    )

    updated = db_session.execute(select_event_stmt, (event_id,)).one()
    return _row_to_response(updated)


@app.delete("/calendar/events/{event_id}", status_code=204, tags=["calendar"])
async def delete_event(
    event_id: str,
    claims: dict[str, Any] = Depends(require_write),
) -> None:
    _ensure_db()
    row = db_session.execute(select_event_stmt, (event_id,)).one()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    db_session.execute(delete_event_stmt, (event_id,))
