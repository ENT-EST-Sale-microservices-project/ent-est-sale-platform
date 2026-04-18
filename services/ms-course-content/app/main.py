from __future__ import annotations

import os
import asyncio
import json
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
from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field

from .runtime import extract_request_id, setup_service_runtime

AUTH_CORE_BASE_URL = os.getenv("AUTH_CORE_BASE_URL", "http://ms-auth-core:8000")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("COURSE_CONTENT_TIMEOUT_SECONDS", "8"))
IDEMPOTENT_RETRIES = int(os.getenv("COURSE_CONTENT_IDEMPOTENT_RETRIES", "2"))
ALLOWED_ROLES = {
    role.strip()
    for role in os.getenv("COURSE_CONTENT_ALLOWED_ROLES", "teacher,admin").split(",")
    if role.strip()
}

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER", "minio")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "ChangeMe_123!")
MINIO_COURSE_BUCKET = os.getenv("MINIO_COURSE_BUCKET", "ent-courses")
INTERNAL_API_TOKEN = os.getenv("INTERNAL_API_TOKEN", "dev-internal-token")

CASSANDRA_CONTACT_POINTS = [
    host.strip() for host in os.getenv("CASSANDRA_CONTACT_POINTS", "cassandra").split(",") if host.strip()
]
CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_USERNAME = os.getenv("CASSANDRA_USERNAME", "cassandra")
CASSANDRA_PASSWORD = os.getenv("CASSANDRA_PASSWORD", "ChangeMe_123!")
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "ent_est")
COURSES_TABLE = os.getenv("COURSE_CONTENT_COURSES_TABLE", "courses")
ASSETS_TABLE = os.getenv("COURSE_CONTENT_ASSETS_TABLE", "course_assets")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://ent:ChangeMe_123!@rabbitmq:5672/")
EVENTS_EXCHANGE = os.getenv("EVENTS_EXCHANGE", "ent.events.topic")
ENABLE_EVENT_PUBLISHING = os.getenv("ENABLE_EVENT_PUBLISHING", "true").lower() in {
    "1",
    "true",
    "yes",
    "on",
}

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ROOT_USER,
    aws_secret_access_key=MINIO_ROOT_PASSWORD,
    region_name="us-east-1",
)

app = FastAPI(
    title="MS-Course-Content",
    version="0.1.0",
    description="Teacher/Admin course content creation and asset upload service.",
)
setup_service_runtime(app, "ms-course-content")

cluster: Cluster | None = None
db_session = None
insert_course_stmt = None
update_course_updated_at_stmt = None
select_course_stmt = None
select_courses_stmt = None
insert_asset_stmt = None
select_assets_by_course_stmt = None
update_course_stmt = None
select_asset_stmt = None
delete_asset_stmt = None


class CreateCourseRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3, max_length=4000)
    module_code: str = Field(min_length=2, max_length=50)
    tags: list[str] = Field(default_factory=list)
    visibility: str = Field(default="public_class")


class CreateCourseResponse(BaseModel):
    course_id: str
    title: str
    description: str
    module_code: str
    tags: list[str]
    visibility: str
    teacher_id: str | None
    created_at: str
    updated_at: str


class UploadAssetResponse(BaseModel):
    asset_id: str
    course_id: str
    filename: str
    content_type: str
    size_bytes: int
    minio_bucket: str
    minio_object_key: str


class CourseWithAssetsResponse(CreateCourseResponse):
    assets: list[dict[str, Any]]


class UpdateCourseRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3, max_length=4000)
    module_code: str = Field(min_length=2, max_length=50)
    tags: list[str] = Field(default_factory=list)
    visibility: str = Field(default="public_class")


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


def _require_internal_token(x_internal_token: str | None = Header(default=None)) -> None:
    if x_internal_token != INTERNAL_API_TOKEN:
        raise _unauthorized("Invalid internal token")


async def require_teacher_or_admin(
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _unauthorized("Missing bearer token")

    attempts = IDEMPOTENT_RETRIES + 1
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


def _ensure_bucket_exists() -> None:
    try:
        s3.head_bucket(Bucket=MINIO_COURSE_BUCKET)
    except ClientError:
        s3.create_bucket(Bucket=MINIO_COURSE_BUCKET)


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
                "producer": "ms-course-content",
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
        pass


def _ensure_db() -> None:
    global cluster, db_session
    global insert_course_stmt, update_course_updated_at_stmt, select_course_stmt, select_courses_stmt
    global insert_asset_stmt, select_assets_by_course_stmt
    global update_course_stmt, select_asset_stmt, delete_asset_stmt

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
        f"{COURSES_TABLE} ("
        "course_id text PRIMARY KEY,"
        "title text,"
        "description text,"
        "module_code text,"
        "tags list<text>,"
        "visibility text,"
        "teacher_id text,"
        "created_at timestamp,"
        "updated_at timestamp"
        ");"
    )
    db_session.execute(
        "CREATE TABLE IF NOT EXISTS "
        f"{ASSETS_TABLE} ("
        "course_id text,"
        "asset_id text,"
        "filename text,"
        "content_type text,"
        "size_bytes bigint,"
        "minio_bucket text,"
        "minio_object_key text,"
        "created_at timestamp,"
        "PRIMARY KEY (course_id, asset_id)"
        ");"
    )

    insert_course_stmt = db_session.prepare(
        "INSERT INTO "
        f"{COURSES_TABLE} "
        "(course_id, title, description, module_code, tags, visibility, teacher_id, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    update_course_updated_at_stmt = db_session.prepare(
        "UPDATE " + COURSES_TABLE + " SET updated_at = ? WHERE course_id = ?"
    )
    select_course_stmt = db_session.prepare(
        "SELECT course_id, title, description, module_code, tags, visibility, teacher_id, created_at, updated_at "
        "FROM " + COURSES_TABLE + " WHERE course_id = ?"
    )
    select_courses_stmt = db_session.prepare(
        "SELECT course_id, title, description, module_code, tags, visibility, teacher_id, created_at, updated_at "
        "FROM " + COURSES_TABLE
    )
    insert_asset_stmt = db_session.prepare(
        "INSERT INTO "
        f"{ASSETS_TABLE} "
        "(course_id, asset_id, filename, content_type, size_bytes, minio_bucket, minio_object_key, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    )
    select_assets_by_course_stmt = db_session.prepare(
        "SELECT course_id, asset_id, filename, content_type, size_bytes, minio_bucket, minio_object_key "
        "FROM " + ASSETS_TABLE + " WHERE course_id = ?"
    )
    update_course_stmt = db_session.prepare(
        "UPDATE "
        + COURSES_TABLE
        + " SET title = ?, description = ?, module_code = ?, tags = ?, visibility = ?, updated_at = ? WHERE course_id = ?"
    )
    select_asset_stmt = db_session.prepare(
        "SELECT course_id, asset_id, filename, content_type, size_bytes, minio_bucket, minio_object_key "
        "FROM " + ASSETS_TABLE + " WHERE course_id = ? AND asset_id = ?"
    )
    delete_asset_stmt = db_session.prepare(
        "DELETE FROM " + ASSETS_TABLE + " WHERE course_id = ? AND asset_id = ?"
    )


def _serialize_asset(row: Any) -> dict[str, Any]:
    return {
        "asset_id": row.asset_id,
        "course_id": row.course_id,
        "filename": row.filename,
        "content_type": row.content_type,
        "size_bytes": int(row.size_bytes or 0),
        "minio_bucket": row.minio_bucket,
        "minio_object_key": row.minio_object_key,
    }


def _load_assets(course_id: str) -> list[dict[str, Any]]:
    _ensure_db()
    rows = db_session.execute(select_assets_by_course_stmt, (course_id,))
    return [_serialize_asset(row) for row in rows]


def _serialize_course(row: Any, assets: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "course_id": row.course_id,
        "title": row.title,
        "description": row.description,
        "module_code": row.module_code,
        "tags": list(row.tags or []),
        "visibility": row.visibility,
        "teacher_id": row.teacher_id,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
        "assets": assets,
    }


def _get_course_or_none(course_id: str) -> dict[str, Any] | None:
    _ensure_db()
    row = db_session.execute(select_course_stmt, (course_id,)).one()
    if row is None:
        return None
    assets = _load_assets(course_id)
    return _serialize_course(row, assets)


@app.on_event("startup")
def startup() -> None:
    _ensure_db()
    _ensure_bucket_exists()


@app.on_event("shutdown")
def shutdown() -> None:
    if cluster is not None:
        cluster.shutdown()


@app.get("/courses-content/health", tags=["course-content"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ms-course-content",
    }


@app.get("/courses", response_model=list[CourseWithAssetsResponse], tags=["course-content"])
def list_courses(
    claims: dict[str, Any] = Depends(require_teacher_or_admin),
) -> list[CourseWithAssetsResponse]:
    _ensure_db()
    rows = db_session.execute(select_courses_stmt)
    user_id = claims.get("sub")
    is_admin = "admin" in _extract_roles(claims)
    
    results = []
    for row in rows:
        if is_admin or row.teacher_id == user_id:
            assets = _load_assets(row.course_id)
            results.append(CourseWithAssetsResponse(**_serialize_course(row, assets)))
    return results


@app.post("/courses", response_model=CreateCourseResponse, tags=["course-content"])
async def create_course(
    request: Request,
    payload: CreateCourseRequest,
    claims: dict[str, Any] = Depends(require_teacher_or_admin),
) -> CreateCourseResponse:
    _ensure_db()
    course_id = str(uuid4())
    now = _timestamp()
    db_session.execute(
        insert_course_stmt,
        (
            course_id,
            payload.title,
            payload.description,
            payload.module_code,
            payload.tags,
            payload.visibility,
            claims.get("sub"),
            now,
            now,
        ),
    )
    response = CreateCourseResponse(
        course_id=course_id,
        title=payload.title,
        description=payload.description,
        module_code=payload.module_code,
        tags=payload.tags,
        visibility=payload.visibility,
        teacher_id=claims.get("sub"),
        created_at=now.isoformat(),
        updated_at=now.isoformat(),
    )
    await _publish_event(
        "course.created.v1",
        {
            "course_id": course_id,
            "teacher_id": claims.get("sub"),
            "title": payload.title,
            "module_code": payload.module_code,
        },
        extract_request_id(request),
    )
    return response


@app.post(
    "/courses/{course_id}/assets",
    response_model=UploadAssetResponse,
    tags=["course-content"],
)
async def upload_course_asset(
    request: Request,
    course_id: str,
    file: UploadFile = File(...),
    _: dict[str, Any] = Depends(require_teacher_or_admin),
) -> UploadAssetResponse:
    _ensure_db()
    course = _get_course_or_none(course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    asset_id = str(uuid4())
    object_key = f"{course_id}/{asset_id}/{file.filename}"
    payload = file.file.read()
    size_bytes = len(payload)

    s3.put_object(
        Bucket=MINIO_COURSE_BUCKET,
        Key=object_key,
        Body=payload,
        ContentType=file.content_type or "application/octet-stream",
    )

    created_at = _timestamp()
    db_session.execute(
        insert_asset_stmt,
        (
            course_id,
            asset_id,
            file.filename,
            file.content_type or "application/octet-stream",
            size_bytes,
            MINIO_COURSE_BUCKET,
            object_key,
            created_at,
        ),
    )
    db_session.execute(update_course_updated_at_stmt, (_timestamp(), course_id))

    response = UploadAssetResponse(
        asset_id=asset_id,
        course_id=course_id,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        minio_bucket=MINIO_COURSE_BUCKET,
        minio_object_key=object_key,
    )
    await _publish_event(
        "asset.uploaded.v1",
        {
            "course_id": course_id,
            "asset_id": asset_id,
            "filename": file.filename,
            "size_bytes": size_bytes,
        },
        extract_request_id(request),
    )
    return response


@app.get(
    "/courses/{course_id}",
    response_model=CourseWithAssetsResponse,
    tags=["course-content"],
)
def get_course(
    course_id: str,
    _: dict[str, Any] = Depends(require_teacher_or_admin),
) -> CourseWithAssetsResponse:
    course = _get_course_or_none(course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return CourseWithAssetsResponse(**course)


@app.put("/courses/{course_id}", response_model=CreateCourseResponse, tags=["course-content"])
async def update_course(
    request: Request,
    course_id: str,
    payload: UpdateCourseRequest,
    _: dict[str, Any] = Depends(require_teacher_or_admin),
) -> CreateCourseResponse:
    _ensure_db()
    current = _get_course_or_none(course_id)
    if current is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    now = _timestamp()
    db_session.execute(
        update_course_stmt,
        (
            payload.title,
            payload.description,
            payload.module_code,
            payload.tags,
            payload.visibility,
            now,
            course_id,
        ),
    )
    updated = _get_course_or_none(course_id)
    response = CreateCourseResponse(
        course_id=updated["course_id"],
        title=updated["title"],
        description=updated["description"],
        module_code=updated["module_code"],
        tags=updated["tags"],
        visibility=updated["visibility"],
        teacher_id=updated["teacher_id"],
        created_at=updated["created_at"],
        updated_at=updated["updated_at"],
    )
    await _publish_event(
        "course.updated.v1",
        {
            "course_id": course_id,
            "title": payload.title,
            "module_code": payload.module_code,
        },
        extract_request_id(request),
    )
    return response


@app.delete("/courses/{course_id}/assets/{asset_id}", tags=["course-content"])
async def delete_course_asset(
    request: Request,
    course_id: str,
    asset_id: str,
    _: dict[str, Any] = Depends(require_teacher_or_admin),
) -> dict[str, str]:
    _ensure_db()
    row = db_session.execute(select_asset_stmt, (course_id, asset_id)).one()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    try:
        s3.delete_object(Bucket=row.minio_bucket, Key=row.minio_object_key)
    except ClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to delete object from MinIO: {exc.__class__.__name__}",
        ) from exc

    db_session.execute(delete_asset_stmt, (course_id, asset_id))
    db_session.execute(update_course_updated_at_stmt, (_timestamp(), course_id))
    await _publish_event(
        "asset.deleted.v1",
        {
            "course_id": course_id,
            "asset_id": asset_id,
        },
        extract_request_id(request),
    )
    return {"status": "deleted"}


@app.delete("/courses/{course_id}", tags=["course-content"])
async def delete_course(
    request: Request,
    course_id: str,
    _: dict[str, Any] = Depends(require_teacher_or_admin),
) -> dict[str, str]:
    _ensure_db()
    course = _get_course_or_none(course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    # Delete all assets from MinIO + Cassandra
    assets = _load_assets(course_id)
    for asset in assets:
        try:
            s3.delete_object(Bucket=asset["minio_bucket"], Key=asset["minio_object_key"])
        except ClientError:
            pass  # Best effort — log but don't block course deletion
        db_session.execute(delete_asset_stmt, (course_id, asset["asset_id"]))

    # Delete course metadata
    db_session.execute(
        db_session.prepare("DELETE FROM " + COURSES_TABLE + " WHERE course_id = ?"),
        (course_id,),
    )

    await _publish_event(
        "course.deleted.v1",
        {
            "course_id": course_id,
            "title": course.get("title"),
            "teacher_id": course.get("teacher_id"),
        },
        extract_request_id(request),
    )
    return {"status": "deleted"}


@app.get("/internal/courses", tags=["internal"])
def list_courses_internal(_: None = Depends(_require_internal_token)) -> list[dict[str, Any]]:
    _ensure_db()
    rows = db_session.execute(select_courses_stmt)
    return [_serialize_course(row, _load_assets(row.course_id)) for row in rows]


@app.get("/internal/courses/{course_id}", tags=["internal"])
def get_course_internal(
    course_id: str,
    _: None = Depends(_require_internal_token),
) -> dict[str, Any]:
    course = _get_course_or_none(course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course
