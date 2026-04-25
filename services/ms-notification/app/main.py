from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Any
from uuid import uuid4

import aio_pika
import aiosmtplib
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from cassandra.policies import RoundRobinPolicy
from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

from .runtime import setup_service_runtime

# ── Configuration ───────────────────────────────────────────────────────────────
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://ent:ChangeMe_123!@rabbitmq:5672/")
EVENTS_EXCHANGE = os.getenv("EVENTS_EXCHANGE", "ent.events.topic")
NOTIF_QUEUE = os.getenv("NOTIF_QUEUE", "q.notification.user")
ENABLE_CONSUMER = os.getenv("NOTIFICATION_ENABLE_CONSUMER", "true").lower() in {
    "1",
    "true",
    "yes",
    "on",
}

SMTP_HOST = os.getenv("SMTP_HOST", "mailpit")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@ent-est.local")
ENABLE_SMTP = os.getenv("NOTIFICATION_ENABLE_SMTP", "true").lower() in {
    "1",
    "true",
    "yes",
    "on",
}

CASSANDRA_CONTACT_POINTS = [
    host.strip()
    for host in os.getenv("CASSANDRA_CONTACT_POINTS", "cassandra").split(",")
    if host.strip()
]
CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_USERNAME = os.getenv("CASSANDRA_USERNAME", "cassandra")
CASSANDRA_PASSWORD = os.getenv("CASSANDRA_PASSWORD", "ChangeMe_123!")
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "ent_est")
NOTIFICATIONS_TABLE = os.getenv("NOTIFICATIONS_TABLE", "notifications")

logger = logging.getLogger("ms-notification")
logging.basicConfig(level=logging.INFO)

# ── App ─────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="MS-Notification",
    version="0.1.0",
    description="Notification service consuming ENT domain events — persists to Cassandra and sends SMTP.",
)
setup_service_runtime(app, "ms-notification")

# ── Cassandra ───────────────────────────────────────────────────────────────────
cluster: Cluster | None = None
db_session = None
insert_notif_stmt = None
select_notifs_by_user_stmt = None
select_notifs_all_stmt = None
update_notif_read_stmt = None

connection: aio_pika.abc.AbstractRobustConnection | None = None
consumer_task: asyncio.Task | None = None


class NotificationTestRequest(BaseModel):
    user_id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1, max_length=4000)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _ensure_db() -> None:
    global cluster, db_session, insert_notif_stmt, select_notifs_by_user_stmt, select_notifs_all_stmt, update_notif_read_stmt

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
        f"{NOTIFICATIONS_TABLE} ("
        "user_id text,"
        "created_at timestamp,"
        "notif_id text,"
        "event_type text,"
        "title text,"
        "body text,"
        "correlation_id text,"
        "read boolean,"
        "PRIMARY KEY (user_id, created_at, notif_id)"
        ") WITH CLUSTERING ORDER BY (created_at DESC, notif_id ASC);"
    )

    insert_notif_stmt = db_session.prepare(
        "INSERT INTO "
        f"{NOTIFICATIONS_TABLE} "
        "(user_id, created_at, notif_id, event_type, title, body, correlation_id, read) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    )
    select_notifs_by_user_stmt = db_session.prepare(
        "SELECT user_id, created_at, notif_id, event_type, title, body, correlation_id, read "
        f"FROM {NOTIFICATIONS_TABLE} WHERE user_id = ? LIMIT ?"
    )
    select_notifs_all_stmt = db_session.prepare(
        "SELECT user_id, created_at, notif_id, event_type, title, body, correlation_id, read "
        f"FROM {NOTIFICATIONS_TABLE} LIMIT ?"
    )
    update_notif_read_stmt = db_session.prepare(
        f"UPDATE {NOTIFICATIONS_TABLE} SET read = true WHERE user_id = ? AND created_at = ? AND notif_id = ?"
    )


def _store_notification(
    *,
    user_id: str,
    notif_id: str,
    event_type: str,
    title: str,
    body: str,
    correlation_id: str | None,
) -> None:
    _ensure_db()
    db_session.execute(
        insert_notif_stmt,
        (user_id, _now(), notif_id, event_type, title, body, correlation_id, False),
    )


def _get_notifications(user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    _ensure_db()
    rows = db_session.execute(select_notifs_by_user_stmt, (user_id, limit))
    return [
        {
            "id": row.notif_id,
            "user_id": row.user_id,
            "event_type": row.event_type,
            "title": row.title,
            "body": row.body,
            "created_at": row.created_at.isoformat() if row.created_at else _now_iso(),
            "correlation_id": row.correlation_id,
            "read": row.read or False,
        }
        for row in rows
    ]


def _serialize_row(row: Any) -> dict[str, Any]:
    return {
        "id": row.notif_id,
        "user_id": row.user_id,
        "event_type": row.event_type,
        "title": row.title,
        "body": row.body,
        "created_at": row.created_at.isoformat() if row.created_at else _now_iso(),
        "correlation_id": row.correlation_id,
        "read": row.read or False,
    }


# ── SMTP ────────────────────────────────────────────────────────────────────────
_EVENT_SUBJECT_MAP = {
    "user.created.v1": "Welcome to ENT EST Salé!",
    "course.created.v1": "New Course Available",
    "course.updated.v1": "Course Updated",
    "course.deleted.v1": "Course Removed",
    "asset.uploaded.v1": "New Course Material",
    "user.role.assigned.v1": "Role Updated",
    "assignment.published.v1": "New Assignment Published",
    "assignment.submitted.v1": "Assignment Submission Received",
    "grade.published.v1": "Your Assignment Has Been Graded",
}


async def _send_email(to_address: str, subject: str, body_text: str) -> None:
    if not ENABLE_SMTP:
        return
    try:
        msg = EmailMessage()
        msg["From"] = SMTP_FROM
        msg["To"] = to_address
        msg["Subject"] = subject
        msg.set_content(body_text)
        await aiosmtplib.send(msg, hostname=SMTP_HOST, port=SMTP_PORT)
        logger.info(json.dumps({"event": "email.sent", "to": to_address, "subject": subject}))
    except Exception as exc:
        logger.warning(
            json.dumps({"event": "email.failed", "to": to_address, "error": str(exc)})
        )


# ── Broadcast helpers ────────────────────────────────────────────────────────────
# Broadcast channels: "broadcast:all-students", "broadcast:all-teachers", "broadcast:all-users"
# These are special user_ids that any user with matching role can read.

def _broadcast_targets_for_event(event_type: str, event_payload: dict) -> list[str]:
    """Return list of user_ids (real or broadcast) that should receive this notification."""
    targets: list[str] = []

    if event_type == "user.created.v1":
        uid = event_payload.get("user_id")
        if uid:
            targets.append(uid)

    elif event_type == "user.role.assigned.v1":
        uid = event_payload.get("user_id")
        if uid:
            targets.append(uid)

    elif event_type in ("course.created.v1", "course.updated.v1"):
        # Notify the teacher who owns the course AND all students
        teacher_id = event_payload.get("teacher_id") or event_payload.get("created_by")
        if teacher_id:
            targets.append(teacher_id)
        targets.append("broadcast:all-students")

    elif event_type == "course.deleted.v1":
        targets.append("broadcast:all-students")
        teacher_id = event_payload.get("teacher_id") or event_payload.get("created_by")
        if teacher_id:
            targets.append(teacher_id)

    elif event_type == "asset.uploaded.v1":
        # Notify all students
        targets.append("broadcast:all-students")
        teacher_id = event_payload.get("uploaded_by") or event_payload.get("teacher_id")
        if teacher_id:
            targets.append(teacher_id)

    elif event_type == "assignment.published.v1":
        # Notify all students
        targets.append("broadcast:all-students")
        creator = event_payload.get("created_by")
        if creator:
            targets.append(creator)

    elif event_type == "assignment.submitted.v1":
        # Notify the teacher (creator of the assignment) + the student
        student_id = event_payload.get("student_id") or event_payload.get("submitted_by")
        teacher_id = event_payload.get("teacher_id") or event_payload.get("assignment_owner")
        if student_id:
            targets.append(student_id)
        if teacher_id:
            targets.append(teacher_id)
        if not targets:
            targets.append("broadcast:all-teachers")

    elif event_type == "grade.published.v1":
        # Notify the specific student
        student_id = event_payload.get("student_id")
        if student_id:
            targets.append(student_id)
        teacher_id = event_payload.get("graded_by")
        if teacher_id:
            targets.append(teacher_id)

    elif event_type == "forum.thread.created.v1":
        # Notify all users (broadcast)
        targets.append("broadcast:all-users")
        author_id = event_payload.get("author_id") or event_payload.get("created_by")
        if author_id:
            # Don't double-notify the author via broadcast; store personal copy
            targets = [t for t in targets if t != "broadcast:all-users"]
            targets.append("broadcast:all-users")

    elif event_type == "forum.message.posted.v1":
        # Notify thread participants
        thread_author = event_payload.get("thread_author_id")
        msg_author = event_payload.get("author_id")
        if thread_author and thread_author != msg_author:
            targets.append(thread_author)
        if msg_author:
            targets.append(msg_author)
        if not targets:
            targets.append("broadcast:all-users")

    elif event_type == "calendar.event.created.v1":
        # Notify all users (everyone sees the calendar)
        targets.append("broadcast:all-users")
        creator = event_payload.get("created_by")
        if creator:
            targets.append(creator)

    elif event_type == "calendar.event.updated.v1" or event_type == "calendar.event.deleted.v1":
        targets.append("broadcast:all-users")

    else:
        uid = event_payload.get("user_id")
        if uid:
            targets.append(uid)

    # Deduplicate preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for t in targets:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique


# ── RabbitMQ Consumer ───────────────────────────────────────────────────────────
async def _consume_events() -> None:
    global connection
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    exchange = await channel.declare_exchange(
        EVENTS_EXCHANGE,
        aio_pika.ExchangeType.TOPIC,
        durable=True,
    )
    queue = await channel.declare_queue(NOTIF_QUEUE, durable=True)
    await queue.bind(exchange, "user.*")
    await queue.bind(exchange, "course.*")
    await queue.bind(exchange, "asset.*")
    await queue.bind(exchange, "assignment.*")
    await queue.bind(exchange, "grade.*")
    await queue.bind(exchange, "forum.*")
    await queue.bind(exchange, "calendar.*")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                payload = json.loads(message.body.decode("utf-8"))
                event_type = payload.get("event_type", "")
                event_payload = payload.get("payload", {})
                correlation_id = payload.get("correlation_id")
                notif_id_base = payload.get("event_id") or str(uuid4())

                subject = _EVENT_SUBJECT_MAP.get(event_type, f"Platform Update: {event_type.replace('.', ' ').title()}")
                body_text = json.dumps(event_payload, indent=2, default=str)

                targets = _broadcast_targets_for_event(event_type, event_payload)
                if not targets:
                    logger.info(json.dumps({"event": "notification.skipped", "event_type": event_type, "reason": "no targets"}))
                    continue

                for i, target_id in enumerate(targets):
                    notif_id = f"{notif_id_base}-{i}" if i > 0 else notif_id_base
                    _store_notification(
                        user_id=target_id,
                        notif_id=notif_id,
                        event_type=event_type,
                        title=subject,
                        body=body_text,
                        correlation_id=correlation_id,
                    )
                    logger.info(json.dumps({
                        "event": "notification.stored",
                        "user_id": target_id,
                        "event_type": event_type,
                    }))

                # Send email if user has an email in the payload
                email_addr = event_payload.get("email")
                if email_addr:
                    await _send_email(email_addr, subject, body_text)


# ── Lifecycle ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup() -> None:
    global consumer_task
    _ensure_db()
    if ENABLE_CONSUMER:
        consumer_task = asyncio.create_task(_consume_events())


@app.on_event("shutdown")
async def shutdown() -> None:
    if consumer_task is not None:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
    if connection is not None:
        await connection.close()
    if cluster is not None:
        cluster.shutdown()


# ── Endpoints ───────────────────────────────────────────────────────────────────
@app.get("/notifications/health", tags=["notification"])
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "ms-notification",
        "consumer_enabled": ENABLE_CONSUMER,
        "smtp_enabled": ENABLE_SMTP,
    }


@app.post("/notifications/test", tags=["notification"])
def send_test_notification(payload: NotificationTestRequest) -> dict[str, Any]:
    notif_id = f"test-{int(_now().timestamp())}"
    _store_notification(
        user_id=payload.user_id,
        notif_id=notif_id,
        event_type="notification.test.v1",
        title=payload.title,
        body=payload.body,
        correlation_id=None,
    )
    return {"status": "queued", "notification_id": notif_id}


@app.get("/notifications/{user_id}", tags=["notification"])
def list_notifications(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict[str, Any]]:
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required")
    return _get_notifications(user_id, limit=limit)


@app.patch("/notifications/{user_id}/{notif_id}/read", tags=["notification"])
def mark_one_read(user_id: str, notif_id: str) -> dict[str, Any]:
    if not user_id or not notif_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id and notif_id are required")
    _ensure_db()
    rows = list(db_session.execute(select_notifs_by_user_stmt, (user_id, 200)))
    for row in rows:
        if row.notif_id == notif_id:
            if not row.read:
                db_session.execute(update_notif_read_stmt, (user_id, row.created_at, row.notif_id))
            return {"marked_read": not row.read}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")


@app.patch("/notifications/{user_id}/read-all", tags=["notification"])
def mark_all_read(user_id: str) -> dict[str, Any]:
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required")
    _ensure_db()
    rows = list(db_session.execute(select_notifs_by_user_stmt, (user_id, 200)))
    count = 0
    for row in rows:
        if not row.read:
            db_session.execute(update_notif_read_stmt, (user_id, row.created_at, row.notif_id))
            count += 1
    return {"marked_read": count}
