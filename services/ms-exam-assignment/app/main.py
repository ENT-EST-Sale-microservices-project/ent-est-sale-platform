from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import aio_pika
import boto3
import httpx
from botocore.exceptions import ClientError
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from cassandra.policies import RoundRobinPolicy
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, Request, UploadFile, status
from pydantic import BaseModel, Field

from .runtime import extract_request_id, setup_service_runtime


@dataclass(frozen=True)
class Settings:
    auth_core_base_url: str = os.getenv("AUTH_CORE_BASE_URL", "http://ms-auth-core:8000")
    timeout_seconds: float = float(os.getenv("EXAM_TIMEOUT_SECONDS", "8"))
    idempotent_retries: int = int(os.getenv("EXAM_IDEMPOTENT_RETRIES", "2"))

    cassandra_contact_points: tuple[str, ...] = tuple(
        h.strip()
        for h in os.getenv("CASSANDRA_CONTACT_POINTS", "cassandra").split(",")
        if h.strip()
    )
    cassandra_port: int = int(os.getenv("CASSANDRA_PORT", "9042"))
    cassandra_username: str = os.getenv("CASSANDRA_USERNAME", "cassandra")
    cassandra_password: str = os.getenv("CASSANDRA_PASSWORD", "ChangeMe_123!")
    cassandra_keyspace: str = os.getenv("CASSANDRA_KEYSPACE", "ent_est")
    assignments_table: str = os.getenv("EXAM_ASSIGNMENTS_TABLE", "assignments")
    submissions_table: str = os.getenv("EXAM_SUBMISSIONS_TABLE", "submissions")
    submissions_by_assignment_table: str = os.getenv("EXAM_SUBMISSIONS_BY_ASSIGNMENT_TABLE", "submissions_by_assignment")

    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
    minio_signing_endpoint: str = os.getenv("MINIO_SIGNING_ENDPOINT", "http://localhost:9002")
    minio_root_user: str = os.getenv("MINIO_ROOT_USER", "minio")
    minio_root_password: str = os.getenv("MINIO_ROOT_PASSWORD", "ChangeMe_123!")
    minio_bucket: str = os.getenv("MINIO_SUBMISSIONS_BUCKET", "ent-uploads")
    presigned_ttl: int = int(os.getenv("SUBMISSION_DOWNLOAD_TTL_SECONDS", "180"))
    max_file_bytes: int = int(os.getenv("EXAM_MAX_FILE_BYTES", str(50 * 1024 * 1024)))  # 50 MB


settings = Settings()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://ent:ChangeMe_123!@rabbitmq:5672/")
EVENTS_EXCHANGE = os.getenv("EVENTS_EXCHANGE", "ent.events.topic")
ENABLE_EVENT_PUBLISHING = os.getenv("ENABLE_EVENT_PUBLISHING", "true").lower() in {
    "1", "true", "yes", "on",
}

TEACHER_ROLES: frozenset[str] = frozenset(
    r.strip()
    for r in os.getenv("EXAM_TEACHER_ROLES", "teacher,admin").split(",")
    if r.strip()
)
STUDENT_ROLES: frozenset[str] = frozenset(
    r.strip()
    for r in os.getenv("EXAM_STUDENT_ROLES", "student").split(",")
    if r.strip()
)

# MinIO clients
s3_upload = boto3.client(
    "s3",
    endpoint_url=settings.minio_endpoint,
    aws_access_key_id=settings.minio_root_user,
    aws_secret_access_key=settings.minio_root_password,
    region_name="us-east-1",
)
s3_sign = boto3.client(
    "s3",
    endpoint_url=settings.minio_signing_endpoint,
    aws_access_key_id=settings.minio_root_user,
    aws_secret_access_key=settings.minio_root_password,
    region_name="us-east-1",
)

app = FastAPI(
    title="MS-Exam-Assignment",
    version="0.1.0",
    description="Assignment publication, student submissions, and grading for ENT EST Salé.",
)
setup_service_runtime(app, "ms-exam-assignment")

# ── Cassandra globals ────────────────────────────────────────────────────────
cluster: Cluster | None = None
db_session = None
insert_assignment_stmt = None
select_assignment_stmt = None
select_all_assignments_stmt = None
insert_submission_stmt = None
insert_submission_by_assignment_stmt = None
select_submission_stmt = None
select_submissions_by_assignment_stmt = None
update_grade_stmt = None


# ── Pydantic models ──────────────────────────────────────────────────────────

class CreateAssignmentRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=1, max_length=5000)
    due_date: datetime
    module_code: str = Field(min_length=1, max_length=50)
    max_grade: float = Field(default=20.0, ge=0)
    status: str = Field(default="published", description="draft | published")


class AssignmentResponse(BaseModel):
    assignment_id: str
    title: str
    description: str
    due_date: str
    module_code: str
    created_by: str
    created_by_name: str
    max_grade: float
    status: str
    created_at: str


class GradeRequest(BaseModel):
    grade: float = Field(ge=0)
    feedback: str = Field(default="", max_length=5000)


class SubmissionResponse(BaseModel):
    submission_id: str
    assignment_id: str
    student_id: str
    student_name: str
    submitted_at: str
    content_text: str
    has_file: bool
    download_url: str | None
    grade: float | None
    feedback: str | None
    graded_at: str | None


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


async def require_teacher(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    claims = await _get_claims(authorization)
    if not _extract_roles(claims).intersection(TEACHER_ROLES):
        raise _forbidden(f"Requires one of roles: {', '.join(sorted(TEACHER_ROLES))}")
    return claims


async def require_student(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    claims = await _get_claims(authorization)
    if not _extract_roles(claims).intersection(STUDENT_ROLES):
        raise _forbidden(f"Requires one of roles: {', '.join(sorted(STUDENT_ROLES))}")
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
                "producer": "ms-exam-assignment",
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


# ── MinIO helpers ────────────────────────────────────────────────────────────

def _ensure_bucket() -> None:
    try:
        s3_upload.head_bucket(Bucket=settings.minio_bucket)
    except ClientError:
        s3_upload.create_bucket(Bucket=settings.minio_bucket)


def _upload_file(content: bytes, object_key: str, content_type: str) -> None:
    s3_upload.put_object(
        Bucket=settings.minio_bucket,
        Key=object_key,
        Body=content,
        ContentType=content_type,
    )


def _presigned_url(object_key: str) -> str:
    return s3_sign.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.minio_bucket, "Key": object_key},
        ExpiresIn=settings.presigned_ttl,
    )


# ── Cassandra setup ──────────────────────────────────────────────────────────

def _ensure_db() -> None:
    global cluster, db_session
    global insert_assignment_stmt, select_assignment_stmt, select_all_assignments_stmt
    global insert_submission_stmt, insert_submission_by_assignment_stmt
    global select_submission_stmt, select_submissions_by_assignment_stmt, update_grade_stmt

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

    # Assignments table
    db_session.execute(
        f"CREATE TABLE IF NOT EXISTS {settings.assignments_table} ("
        "assignment_id   text PRIMARY KEY,"
        "title           text,"
        "description     text,"
        "due_date        timestamp,"
        "module_code     text,"
        "created_by      text,"
        "created_by_name text,"
        "max_grade       float,"
        "status          text,"
        "created_at      timestamp"
        ");"
    )

    # Submissions keyed by submission_id (for grading by ID)
    db_session.execute(
        f"CREATE TABLE IF NOT EXISTS {settings.submissions_table} ("
        "submission_id    text PRIMARY KEY,"
        "assignment_id    text,"
        "student_id       text,"
        "student_name     text,"
        "submitted_at     timestamp,"
        "content_text     text,"
        "minio_object_key text,"
        "grade            float,"
        "feedback         text,"
        "graded_at        timestamp"
        ");"
    )

    # Submissions by assignment — efficient listing of all submissions per assignment
    db_session.execute(
        f"CREATE TABLE IF NOT EXISTS {settings.submissions_by_assignment_table} ("
        "assignment_id  text,"
        "submitted_at   timestamp,"
        "submission_id  text,"
        "PRIMARY KEY (assignment_id, submitted_at, submission_id)"
        ") WITH CLUSTERING ORDER BY (submitted_at DESC, submission_id ASC);"
    )

    insert_assignment_stmt = db_session.prepare(
        f"INSERT INTO {settings.assignments_table} "
        "(assignment_id, title, description, due_date, module_code, created_by, created_by_name, max_grade, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    select_assignment_stmt = db_session.prepare(
        f"SELECT assignment_id, title, description, due_date, module_code, created_by, created_by_name, max_grade, status, created_at "
        f"FROM {settings.assignments_table} WHERE assignment_id = ?"
    )
    select_all_assignments_stmt = db_session.prepare(
        f"SELECT assignment_id, title, description, due_date, module_code, created_by, created_by_name, max_grade, status, created_at "
        f"FROM {settings.assignments_table}"
    )
    insert_submission_stmt = db_session.prepare(
        f"INSERT INTO {settings.submissions_table} "
        "(submission_id, assignment_id, student_id, student_name, submitted_at, content_text, minio_object_key, grade, feedback, graded_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    insert_submission_by_assignment_stmt = db_session.prepare(
        f"INSERT INTO {settings.submissions_by_assignment_table} "
        "(assignment_id, submitted_at, submission_id) VALUES (?, ?, ?)"
    )
    select_submission_stmt = db_session.prepare(
        f"SELECT submission_id, assignment_id, student_id, student_name, submitted_at, "
        f"content_text, minio_object_key, grade, feedback, graded_at "
        f"FROM {settings.submissions_table} WHERE submission_id = ?"
    )
    select_submissions_by_assignment_stmt = db_session.prepare(
        f"SELECT submission_id FROM {settings.submissions_by_assignment_table} WHERE assignment_id = ?"
    )
    update_grade_stmt = db_session.prepare(
        f"UPDATE {settings.submissions_table} "
        "SET grade = ?, feedback = ?, graded_at = ? WHERE submission_id = ?"
    )


def _row_to_assignment(row: Any) -> AssignmentResponse:
    return AssignmentResponse(
        assignment_id=row.assignment_id,
        title=row.title or "",
        description=row.description or "",
        due_date=row.due_date.isoformat() if row.due_date else "",
        module_code=row.module_code or "",
        created_by=row.created_by or "",
        created_by_name=row.created_by_name or "",
        max_grade=float(row.max_grade) if row.max_grade is not None else 20.0,
        status=row.status or "published",
        created_at=row.created_at.isoformat() if row.created_at else "",
    )


def _row_to_submission(row: Any) -> SubmissionResponse:
    has_file = bool(row.minio_object_key)
    download_url: str | None = None
    if has_file:
        try:
            download_url = _presigned_url(row.minio_object_key)
        except Exception:
            download_url = None

    return SubmissionResponse(
        submission_id=row.submission_id,
        assignment_id=row.assignment_id,
        student_id=row.student_id or "",
        student_name=row.student_name or "",
        submitted_at=row.submitted_at.isoformat() if row.submitted_at else "",
        content_text=row.content_text or "",
        has_file=has_file,
        download_url=download_url,
        grade=float(row.grade) if row.grade is not None else None,
        feedback=row.feedback,
        graded_at=row.graded_at.isoformat() if row.graded_at else None,
    )


# ── Lifecycle ────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup() -> None:
    _ensure_db()
    try:
        _ensure_bucket()
    except Exception:
        pass  # bucket may already exist; errors handled at upload time


@app.on_event("shutdown")
def shutdown() -> None:
    if cluster is not None:
        cluster.shutdown()


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/exams/health", tags=["exams"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ms-exam-assignment"}


@app.post("/assignments", response_model=AssignmentResponse, status_code=201, tags=["exams"])
async def create_assignment(
    request: Request,
    payload: CreateAssignmentRequest,
    claims: dict[str, Any] = Depends(require_teacher),
) -> AssignmentResponse:
    _ensure_db()
    assignment_id = str(uuid4())
    now = _now()
    creator_id = claims.get("sub") or "unknown"
    creator_name = claims.get("preferred_username") or claims.get("email") or creator_id

    db_session.execute(
        insert_assignment_stmt,
        (
            assignment_id,
            payload.title,
            payload.description,
            payload.due_date,
            payload.module_code,
            creator_id,
            creator_name,
            payload.max_grade,
            payload.status,
            now,
        ),
    )

    await _publish_event(
        "assignment.published.v1",
        {
            "assignment_id": assignment_id,
            "title": payload.title,
            "module_code": payload.module_code,
            "due_date": payload.due_date.isoformat(),
            "created_by": creator_id,
            "user_id": creator_id,
        },
        extract_request_id(request),
    )

    row = db_session.execute(select_assignment_stmt, (assignment_id,)).one()
    return _row_to_assignment(row)


@app.get("/assignments", response_model=list[AssignmentResponse], tags=["exams"])
async def list_assignments(
    module_code: str | None = Query(default=None, max_length=50),
    assignment_status: str | None = Query(default=None, alias="status"),
    _: dict[str, Any] = Depends(require_auth),
) -> list[AssignmentResponse]:
    _ensure_db()
    rows = db_session.execute(select_all_assignments_stmt).all()

    results = []
    for row in rows:
        if module_code and row.module_code != module_code:
            continue
        if assignment_status and row.status != assignment_status:
            continue
        results.append(_row_to_assignment(row))

    results.sort(key=lambda a: a.created_at, reverse=True)
    return results


@app.get("/assignments/{assignment_id}", response_model=AssignmentResponse, tags=["exams"])
async def get_assignment(
    assignment_id: str,
    _: dict[str, Any] = Depends(require_auth),
) -> AssignmentResponse:
    _ensure_db()
    row = db_session.execute(select_assignment_stmt, (assignment_id,)).one()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    return _row_to_assignment(row)


@app.post("/assignments/{assignment_id}/submissions", response_model=SubmissionResponse, status_code=201, tags=["exams"])
async def submit_assignment(
    request: Request,
    assignment_id: str,
    content_text: str = Form(default=""),
    file: UploadFile | None = File(default=None),
    claims: dict[str, Any] = Depends(require_student),
) -> SubmissionResponse:
    _ensure_db()
    assignment_row = db_session.execute(select_assignment_stmt, (assignment_id,)).one()
    if assignment_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    if assignment_row.status != "published":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assignment is not published")

    if not content_text.strip() and file is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Submission must include text content or a file",
        )

    student_id = claims.get("sub") or "unknown"
    student_name = claims.get("preferred_username") or claims.get("email") or student_id
    submission_id = str(uuid4())
    now = _now()
    minio_key: str | None = None

    # Upload file to MinIO if provided
    if file is not None:
        content = await file.read()
        if len(content) > settings.max_file_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum size of {settings.max_file_bytes // (1024*1024)} MB",
            )
        minio_key = f"submissions/{assignment_id}/{student_id}/{file.filename or submission_id}"
        try:
            _upload_file(content, minio_key, file.content_type or "application/octet-stream")
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"File upload failed: {exc}",
            ) from exc

    db_session.execute(
        insert_submission_stmt,
        (submission_id, assignment_id, student_id, student_name, now, content_text, minio_key, None, None, None),
    )
    db_session.execute(
        insert_submission_by_assignment_stmt,
        (assignment_id, now, submission_id),
    )

    await _publish_event(
        "assignment.submitted.v1",
        {
            "submission_id": submission_id,
            "assignment_id": assignment_id,
            "student_id": student_id,
            "user_id": student_id,
        },
        extract_request_id(request),
    )

    row = db_session.execute(select_submission_stmt, (submission_id,)).one()
    return _row_to_submission(row)


@app.get("/assignments/{assignment_id}/submissions", response_model=list[SubmissionResponse], tags=["exams"])
async def list_submissions(
    assignment_id: str,
    claims: dict[str, Any] = Depends(require_auth),
) -> list[SubmissionResponse]:
    _ensure_db()
    assignment_row = db_session.execute(select_assignment_stmt, (assignment_id,)).one()
    if assignment_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    roles = _extract_roles(claims)
    is_teacher = bool(roles.intersection(TEACHER_ROLES))
    student_id = claims.get("sub") or "unknown"

    # Get all submission_ids for this assignment
    id_rows = db_session.execute(select_submissions_by_assignment_stmt, (assignment_id,)).all()
    results: list[SubmissionResponse] = []

    for id_row in id_rows:
        sub_row = db_session.execute(select_submission_stmt, (id_row.submission_id,)).one()
        if sub_row is None:
            continue
        # Students can only see their own submissions
        if not is_teacher and sub_row.student_id != student_id:
            continue
        results.append(_row_to_submission(sub_row))

    return results


@app.post(
    "/assignments/{assignment_id}/submissions/{submission_id}/grade",
    response_model=SubmissionResponse,
    tags=["exams"],
)
async def grade_submission(
    request: Request,
    assignment_id: str,
    submission_id: str,
    payload: GradeRequest,
    claims: dict[str, Any] = Depends(require_teacher),
) -> SubmissionResponse:
    _ensure_db()
    assignment_row = db_session.execute(select_assignment_stmt, (assignment_id,)).one()
    if assignment_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    sub_row = db_session.execute(select_submission_stmt, (submission_id,)).one()
    if sub_row is None or sub_row.assignment_id != assignment_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    if payload.grade > float(assignment_row.max_grade or 20.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Grade {payload.grade} exceeds max_grade {assignment_row.max_grade}",
        )

    graded_at = _now()
    db_session.execute(
        update_grade_stmt,
        (payload.grade, payload.feedback, graded_at, submission_id),
    )

    await _publish_event(
        "grade.published.v1",
        {
            "submission_id": submission_id,
            "assignment_id": assignment_id,
            "student_id": sub_row.student_id,
            "user_id": sub_row.student_id,
            "grade": payload.grade,
            "max_grade": float(assignment_row.max_grade or 20.0),
        },
        extract_request_id(request),
    )

    updated = db_session.execute(select_submission_stmt, (submission_id,)).one()
    return _row_to_submission(updated)
