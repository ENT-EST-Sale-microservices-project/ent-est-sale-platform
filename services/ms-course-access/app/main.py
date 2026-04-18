from __future__ import annotations

import os
import asyncio
from typing import Any

import boto3
import httpx
from fastapi import Depends, Header, HTTPException, FastAPI, status
from pydantic import BaseModel, Field

from .runtime import setup_service_runtime

AUTH_CORE_BASE_URL = os.getenv("AUTH_CORE_BASE_URL", "http://ms-auth-core:8000")
COURSE_CONTENT_BASE_URL = os.getenv("COURSE_CONTENT_BASE_URL", "http://ms-course-content:8000")
INTERNAL_API_TOKEN = os.getenv("INTERNAL_API_TOKEN", "dev-internal-token")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("COURSE_ACCESS_TIMEOUT_SECONDS", "8"))
IDEMPOTENT_RETRIES = int(os.getenv("COURSE_ACCESS_IDEMPOTENT_RETRIES", "2"))

ALLOWED_ROLES = {
    role.strip()
    for role in os.getenv("COURSE_ACCESS_ALLOWED_ROLES", "student").split(",")
    if role.strip()
}

MINIO_SIGNING_ENDPOINT = os.getenv("MINIO_SIGNING_ENDPOINT", "http://localhost:9002")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER", "minio")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "ChangeMe_123!")
MINIO_COURSE_BUCKET = os.getenv("MINIO_COURSE_BUCKET", "ent-courses")
PRESIGNED_TTL_SECONDS = int(os.getenv("COURSE_DOWNLOAD_TTL_SECONDS", "180"))

s3_signer = boto3.client(
    "s3",
    endpoint_url=MINIO_SIGNING_ENDPOINT,
    aws_access_key_id=MINIO_ROOT_USER,
    aws_secret_access_key=MINIO_ROOT_PASSWORD,
    region_name="us-east-1",
)

app = FastAPI(
    title="MS-Course-Access",
    version="0.1.0",
    description="Student-facing course access and pre-signed download links.",
)
setup_service_runtime(app, "ms-course-access")


class DownloadLinkRequest(BaseModel):
    asset_id: str | None = Field(default=None)


class DownloadLinkResponse(BaseModel):
    course_id: str
    asset_id: str
    download_url: str
    expires_in_seconds: int


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


async def require_student(
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


async def _internal_get(path: str) -> Any:
    attempts = IDEMPOTENT_RETRIES + 1
    backoff = 0.15
    resp: httpx.Response | None = None
    for attempt in range(1, attempts + 1):
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                resp = await client.get(
                    f"{COURSE_CONTENT_BASE_URL}{path}",
                    headers={"x-internal-token": INTERNAL_API_TOKEN},
                )
            break
        except httpx.RequestError as exc:
            if attempt < attempts:
                await asyncio.sleep(backoff)
                backoff *= 2
                continue
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"course-content unavailable: {exc.__class__.__name__}",
            ) from exc

    assert resp is not None

    if resp.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    if resp.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="course-content returned an unexpected error",
        )

    return resp.json()


@app.get("/courses-access/health", tags=["course-access"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ms-course-access",
        "bucket": MINIO_COURSE_BUCKET,
    }


@app.get("/courses", tags=["course-access"])
async def list_courses(_: dict[str, Any] = Depends(require_student)) -> list[dict[str, Any]]:
    courses = await _internal_get("/internal/courses")
    return [
        {
            "course_id": course.get("course_id"),
            "title": course.get("title"),
            "description": course.get("description"),
            "module_code": course.get("module_code"),
            "tags": course.get("tags", []),
            "visibility": course.get("visibility"),
            "created_at": course.get("created_at"),
            "updated_at": course.get("updated_at"),
            "assets_count": len(course.get("assets", [])),
        }
        for course in courses
    ]


@app.get("/courses/{course_id}", tags=["course-access"])
async def get_course(
    course_id: str,
    _: dict[str, Any] = Depends(require_student),
) -> dict[str, Any]:
    course = await _internal_get(f"/internal/courses/{course_id}")
    return {
        "course_id": course.get("course_id"),
        "title": course.get("title"),
        "description": course.get("description"),
        "module_code": course.get("module_code"),
        "tags": course.get("tags", []),
        "visibility": course.get("visibility"),
        "created_at": course.get("created_at"),
        "updated_at": course.get("updated_at"),
        "assets": course.get("assets", []),
    }


@app.post(
    "/courses/{course_id}/download-links",
    response_model=DownloadLinkResponse,
    tags=["course-access"],
)
async def generate_download_link(
    course_id: str,
    payload: DownloadLinkRequest,
    _: dict[str, Any] = Depends(require_student),
) -> DownloadLinkResponse:
    course = await _internal_get(f"/internal/courses/{course_id}")
    assets = course.get("assets", [])
    if not assets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assets found for this course",
        )

    asset = None
    if payload.asset_id:
        for item in assets:
            if item.get("asset_id") == payload.asset_id:
                asset = item
                break
        if asset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requested asset not found",
            )
    else:
        asset = assets[0]

    object_key = asset["minio_object_key"]
    download_url = s3_signer.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": MINIO_COURSE_BUCKET,
            "Key": object_key,
        },
        ExpiresIn=PRESIGNED_TTL_SECONDS,
    )

    return DownloadLinkResponse(
        course_id=course_id,
        asset_id=asset["asset_id"],
        download_url=download_url,
        expires_in_seconds=PRESIGNED_TTL_SECONDS,
    )
