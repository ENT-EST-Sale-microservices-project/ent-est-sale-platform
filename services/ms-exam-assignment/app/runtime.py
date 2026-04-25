from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.exceptions import HTTPException as StarletteHTTPException

REQUEST_COUNTER = Counter(
    "ent_http_requests_total",
    "Total HTTP requests",
    ["service", "method", "path", "status"],
)
REQUEST_DURATION = Histogram(
    "ent_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["service", "method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.2, 0.4, 0.8, 1.5, 3, 6),
)


def _status_code_to_error(status_code: int) -> str:
    if status_code == 400:
        return "BAD_REQUEST"
    if status_code == 401:
        return "UNAUTHENTICATED"
    if status_code == 403:
        return "FORBIDDEN"
    if status_code == 404:
        return "NOT_FOUND"
    if status_code == 409:
        return "CONFLICT"
    if status_code == 422:
        return "VALIDATION_ERROR"
    if status_code == 429:
        return "RATE_LIMITED"
    if 500 <= status_code:
        return "INTERNAL_ERROR"
    return "REQUEST_ERROR"


def setup_service_runtime(app: FastAPI, service_name: str) -> None:
    logger = logging.getLogger(service_name)
    logging.basicConfig(level=logging.INFO)

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        path = request.url.path
        method = request.method

        try:
            response = await call_next(request)
        except Exception:
            duration = time.perf_counter() - started
            REQUEST_COUNTER.labels(service_name, method, path, "500").inc()
            REQUEST_DURATION.labels(service_name, method, path).observe(duration)
            logger.exception(
                json.dumps(
                    {
                        "event": "request.failed",
                        "service": service_name,
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "duration_ms": round(duration * 1000, 2),
                    }
                )
            )
            raise

        duration = time.perf_counter() - started
        status = str(response.status_code)
        REQUEST_COUNTER.labels(service_name, method, path, status).inc()
        REQUEST_DURATION.labels(service_name, method, path).observe(duration)

        response.headers["x-request-id"] = request_id
        response.headers.setdefault("x-correlation-id", request_id)

        logger.info(
            json.dumps(
                {
                    "event": "request.completed",
                    "service": service_name,
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                }
            )
        )
        return response

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        request_id = getattr(request.state, "request_id", "unknown")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": _status_code_to_error(exc.status_code),
                    "message": str(exc.detail),
                },
                "request_id": request_id,
            },
            headers={"x-request-id": request_id},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", "unknown")
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": exc.errors(),
                },
                "request_id": request_id,
            },
            headers={"x-request-id": request_id},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.exception(
            json.dumps(
                {
                    "event": "exception.unhandled",
                    "service": service_name,
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "error": str(exc),
                }
            )
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Unexpected server error",
                },
                "request_id": request_id,
            },
            headers={"x-request-id": request_id},
        )

    @app.get("/metrics", tags=["observability"])
    def metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def extract_request_id(obj: Any) -> str | None:
    try:
        return str(getattr(obj.state, "request_id", "")) or None
    except Exception:
        return None
