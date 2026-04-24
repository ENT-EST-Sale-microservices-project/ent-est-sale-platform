from __future__ import annotations

import asyncio
import json
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import aio_pika
import httpx
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from cassandra.policies import RoundRobinPolicy
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

from .runtime import extract_request_id, setup_service_runtime


@dataclass(frozen=True)
class Settings:
    auth_core_base_url: str = os.getenv("AUTH_CORE_BASE_URL", "http://ms-auth-core:8000")
    timeout_seconds: float = float(os.getenv("FORUM_TIMEOUT_SECONDS", "8"))
    idempotent_retries: int = int(os.getenv("FORUM_IDEMPOTENT_RETRIES", "2"))

    cassandra_contact_points: tuple[str, ...] = tuple(
        h.strip()
        for h in os.getenv("CASSANDRA_CONTACT_POINTS", "cassandra").split(",")
        if h.strip()
    )
    cassandra_port: int = int(os.getenv("CASSANDRA_PORT", "9042"))
    cassandra_username: str = os.getenv("CASSANDRA_USERNAME", "cassandra")
    cassandra_password: str = os.getenv("CASSANDRA_PASSWORD", "ChangeMe_123!")
    cassandra_keyspace: str = os.getenv("CASSANDRA_KEYSPACE", "ent_est")
    threads_table: str = os.getenv("FORUM_THREADS_TABLE", "forum_threads")
    messages_table: str = os.getenv("FORUM_MESSAGES_TABLE", "forum_messages")
    counters_table: str = os.getenv("FORUM_COUNTERS_TABLE", "forum_thread_counters")


settings = Settings()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://ent:ChangeMe_123!@rabbitmq:5672/")
EVENTS_EXCHANGE = os.getenv("EVENTS_EXCHANGE", "ent.events.topic")
ENABLE_EVENT_PUBLISHING = os.getenv("ENABLE_EVENT_PUBLISHING", "true").lower() in {
    "1", "true", "yes", "on",
}

app = FastAPI(
    title="MS-Forum-Chat",
    version="0.1.0",
    description="Forum threads + real-time WebSocket chat for ENT EST Salé.",
)
setup_service_runtime(app, "ms-forum-chat")


# ── In-memory WebSocket room manager ────────────────────────────────────────

class ConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, room: str, ws: WebSocket) -> None:
        await ws.accept()
        self._rooms[room].append(ws)

    def disconnect(self, room: str, ws: WebSocket) -> None:
        conns = self._rooms.get(room, [])
        if ws in conns:
            conns.remove(ws)

    async def broadcast(self, room: str, message: str) -> None:
        dead: list[WebSocket] = []
        for conn in list(self._rooms.get(room, [])):
            try:
                await conn.send_text(message)
            except Exception:
                dead.append(conn)
        for d in dead:
            self.disconnect(room, d)


manager = ConnectionManager()


# ── Cassandra globals ────────────────────────────────────────────────────────

cluster: Cluster | None = None
db_session = None
insert_thread_stmt = None
select_thread_stmt = None
select_all_threads_stmt = None
insert_message_stmt = None
select_messages_stmt = None
increment_counter_stmt = None
select_counter_stmt = None


# ── Pydantic models ──────────────────────────────────────────────────────────

class CreateThreadRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    body: str = Field(min_length=1, max_length=10000)
    module_code: str = Field(default="general", max_length=50)


class PostMessageRequest(BaseModel):
    body: str = Field(min_length=1, max_length=10000)


class MessageResponse(BaseModel):
    message_id: str
    thread_id: str
    body: str
    author_id: str
    author_name: str
    created_at: str


class ThreadResponse(BaseModel):
    thread_id: str
    title: str
    body: str
    author_id: str
    author_name: str
    module_code: str
    reply_count: int
    created_at: str


class ThreadDetailResponse(ThreadResponse):
    messages: list[MessageResponse]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


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


async def _validate_token(token: str) -> dict[str, Any]:
    resp = await _http_get(
        f"{settings.auth_core_base_url}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp.status_code == status.HTTP_401_UNAUTHORIZED:
        raise _unauthorized("Invalid or expired token")
    if resp.status_code >= 400:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="auth-core error")
    return resp.json()


async def require_auth(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _unauthorized("Missing bearer token")
    return await _validate_token(authorization.split(" ", 1)[1])


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
                "producer": "ms-forum-chat",
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
        pass


# ── Cassandra setup ──────────────────────────────────────────────────────────

def _ensure_db() -> None:
    global cluster, db_session
    global insert_thread_stmt, select_thread_stmt, select_all_threads_stmt
    global insert_message_stmt, select_messages_stmt
    global increment_counter_stmt, select_counter_stmt

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

    # Threads table
    db_session.execute(
        f"CREATE TABLE IF NOT EXISTS {settings.threads_table} ("
        "thread_id   text PRIMARY KEY,"
        "title       text,"
        "body        text,"
        "author_id   text,"
        "author_name text,"
        "module_code text,"
        "created_at  timestamp"
        ");"
    )

    # Reply counters — must be a dedicated counter table in Cassandra
    db_session.execute(
        f"CREATE TABLE IF NOT EXISTS {settings.counters_table} ("
        "thread_id   text PRIMARY KEY,"
        "reply_count counter"
        ");"
    )

    # Messages table — partitioned by thread_id for efficient per-thread queries
    db_session.execute(
        f"CREATE TABLE IF NOT EXISTS {settings.messages_table} ("
        "thread_id   text,"
        "created_at  timestamp,"
        "message_id  text,"
        "body        text,"
        "author_id   text,"
        "author_name text,"
        "PRIMARY KEY (thread_id, created_at, message_id)"
        ") WITH CLUSTERING ORDER BY (created_at ASC, message_id ASC);"
    )

    insert_thread_stmt = db_session.prepare(
        f"INSERT INTO {settings.threads_table} "
        "(thread_id, title, body, author_id, author_name, module_code, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)"
    )
    select_thread_stmt = db_session.prepare(
        f"SELECT thread_id, title, body, author_id, author_name, module_code, created_at "
        f"FROM {settings.threads_table} WHERE thread_id = ?"
    )
    select_all_threads_stmt = db_session.prepare(
        f"SELECT thread_id, title, body, author_id, author_name, module_code, created_at "
        f"FROM {settings.threads_table}"
    )
    insert_message_stmt = db_session.prepare(
        f"INSERT INTO {settings.messages_table} "
        "(thread_id, created_at, message_id, body, author_id, author_name) "
        "VALUES (?, ?, ?, ?, ?, ?)"
    )
    select_messages_stmt = db_session.prepare(
        f"SELECT thread_id, created_at, message_id, body, author_id, author_name "
        f"FROM {settings.messages_table} WHERE thread_id = ?"
    )
    increment_counter_stmt = db_session.prepare(
        f"UPDATE {settings.counters_table} SET reply_count = reply_count + 1 WHERE thread_id = ?"
    )
    select_counter_stmt = db_session.prepare(
        f"SELECT reply_count FROM {settings.counters_table} WHERE thread_id = ?"
    )


def _get_reply_count(thread_id: str) -> int:
    row = db_session.execute(select_counter_stmt, (thread_id,)).one()
    return int(row.reply_count) if row and row.reply_count else 0


def _thread_row_to_response(row: Any) -> ThreadResponse:
    count = _get_reply_count(row.thread_id)
    return ThreadResponse(
        thread_id=row.thread_id,
        title=row.title or "",
        body=row.body or "",
        author_id=row.author_id or "",
        author_name=row.author_name or "",
        module_code=row.module_code or "general",
        reply_count=count,
        created_at=row.created_at.isoformat() if row.created_at else "",
    )


def _message_row_to_response(row: Any) -> MessageResponse:
    return MessageResponse(
        message_id=row.message_id,
        thread_id=row.thread_id,
        body=row.body or "",
        author_id=row.author_id or "",
        author_name=row.author_name or "",
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


# ── REST Endpoints ───────────────────────────────────────────────────────────

@app.get("/forum/health", tags=["forum"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ms-forum-chat"}


@app.post("/forum/threads", response_model=ThreadResponse, status_code=201, tags=["forum"])
async def create_thread(
    request: Request,
    payload: CreateThreadRequest,
    claims: dict[str, Any] = Depends(require_auth),
) -> ThreadResponse:
    _ensure_db()
    thread_id = str(uuid4())
    now = _now()
    author_id = claims.get("sub") or "unknown"
    author_name = claims.get("preferred_username") or claims.get("email") or author_id

    db_session.execute(
        insert_thread_stmt,
        (thread_id, payload.title, payload.body, author_id, author_name, payload.module_code, now),
    )

    await _publish_event(
        "forum.thread.created.v1",
        {
            "thread_id": thread_id,
            "title": payload.title,
            "module_code": payload.module_code,
            "author_id": author_id,
        },
        extract_request_id(request),
    )

    row = db_session.execute(select_thread_stmt, (thread_id,)).one()
    return _thread_row_to_response(row)


@app.get("/forum/threads", response_model=list[ThreadResponse], tags=["forum"])
async def list_threads(
    module_code: str | None = Query(default=None, max_length=50),
    _: dict[str, Any] = Depends(require_auth),
) -> list[ThreadResponse]:
    _ensure_db()
    rows = db_session.execute(select_all_threads_stmt).all()

    results = []
    for row in rows:
        if module_code and row.module_code != module_code:
            continue
        results.append(_thread_row_to_response(row))

    results.sort(key=lambda t: t.created_at, reverse=True)
    return results


@app.get("/forum/threads/{thread_id}", response_model=ThreadDetailResponse, tags=["forum"])
async def get_thread(
    thread_id: str,
    _: dict[str, Any] = Depends(require_auth),
) -> ThreadDetailResponse:
    _ensure_db()
    row = db_session.execute(select_thread_stmt, (thread_id,)).one()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")

    msg_rows = db_session.execute(select_messages_stmt, (thread_id,)).all()
    messages = [_message_row_to_response(m) for m in msg_rows]
    count = _get_reply_count(thread_id)

    return ThreadDetailResponse(
        thread_id=row.thread_id,
        title=row.title or "",
        body=row.body or "",
        author_id=row.author_id or "",
        author_name=row.author_name or "",
        module_code=row.module_code or "general",
        reply_count=count,
        created_at=row.created_at.isoformat() if row.created_at else "",
        messages=messages,
    )


@app.post("/forum/threads/{thread_id}/messages", response_model=MessageResponse, status_code=201, tags=["forum"])
async def post_message(
    request: Request,
    thread_id: str,
    payload: PostMessageRequest,
    claims: dict[str, Any] = Depends(require_auth),
) -> MessageResponse:
    _ensure_db()
    thread_row = db_session.execute(select_thread_stmt, (thread_id,)).one()
    if thread_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")

    message_id = str(uuid4())
    now = _now()
    author_id = claims.get("sub") or "unknown"
    author_name = claims.get("preferred_username") or claims.get("email") or author_id

    db_session.execute(
        insert_message_stmt,
        (thread_id, now, message_id, payload.body, author_id, author_name),
    )
    db_session.execute(increment_counter_stmt, (thread_id,))

    await _publish_event(
        "forum.message.posted.v1",
        {
            "message_id": message_id,
            "thread_id": thread_id,
            "author_id": author_id,
        },
        extract_request_id(request),
    )

    return MessageResponse(
        message_id=message_id,
        thread_id=thread_id,
        body=payload.body,
        author_id=author_id,
        author_name=author_name,
        created_at=now.isoformat(),
    )


# ── WebSocket endpoint ───────────────────────────────────────────────────────

@app.websocket("/chat/ws")
async def websocket_chat(
    ws: WebSocket,
    token: str = Query(..., description="JWT access token"),
    room: str = Query(default="general", max_length=50, description="Chat room / module_code"),
) -> None:
    # Validate JWT before accepting the connection
    try:
        claims = await _validate_token(token)
    except HTTPException:
        await ws.close(code=4001)
        return

    username = claims.get("preferred_username") or claims.get("sub") or "anonymous"
    user_id = claims.get("sub") or "unknown"

    await manager.connect(room, ws)
    join_msg = json.dumps({
        "type": "system",
        "room": room,
        "text": f"{username} joined the chat",
        "user_id": user_id,
        "username": username,
    })
    await manager.broadcast(room, join_msg)

    try:
        while True:
            data = await ws.receive_text()
            # Expect plain text or JSON {"text": "..."} from the client
            try:
                body = json.loads(data).get("text", data)
            except (json.JSONDecodeError, AttributeError):
                body = data

            if not body or not str(body).strip():
                continue

            message = json.dumps({
                "type": "message",
                "room": room,
                "text": str(body).strip(),
                "user_id": user_id,
                "username": username,
            })
            await manager.broadcast(room, message)

    except WebSocketDisconnect:
        manager.disconnect(room, ws)
        leave_msg = json.dumps({
            "type": "system",
            "room": room,
            "text": f"{username} left the chat",
            "user_id": user_id,
            "username": username,
        })
        await manager.broadcast(room, leave_msg)
