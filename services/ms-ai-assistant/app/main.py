from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import aio_pika
import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from .runtime import setup_service_runtime

# ── Configuration ───────────────────────────────────────────────────────────────
AUTH_CORE_BASE_URL = os.getenv("AUTH_CORE_BASE_URL", "http://ms-auth-core:8000")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "2048"))
AI_RATE_LIMIT_PER_MIN = int(os.getenv("AI_RATE_LIMIT_PER_MIN", "20"))
AI_TIMEOUT_SECONDS = int(os.getenv("AI_TIMEOUT_SECONDS", "8"))

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://ent:ChangeMe_123!@rabbitmq:5672/")
EVENTS_EXCHANGE = os.getenv("EVENTS_EXCHANGE", "ent.events.topic")
AI_QUEUE = os.getenv("AI_QUEUE", "q.ai.context")

INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(previous|all)\s+(instructions?|orders?|directions?)", re.IGNORECASE),
    re.compile(r"(forget|disregard)\s+(everything|all|previous)", re.IGNORECASE),
    re.compile(r"you\s+are\s+(now\s+)?(a|an)\s+(different|new|evil)", re.IGNORECASE),
    re.compile(r"system\s*prompt\s*(leak|extract|reveal)", re.IGNORECASE),
    re.compile(r"---\s*system\s*prompt", re.IGNORECASE),
    re.compile(r"#?\s*system\s*:\s*", re.IGNORECASE),
    re.compile(r"\[\s*INST\s*\].*\[\s*/\s*INST\s*\]", re.IGNORECASE),
    re.compile(r"act\s+as\s+(if\s+)?you\s+(are\s+)?(a\s+)?(different|new| jailbreak)", re.IGNORECASE),
]

PROMPT_INJECTION_PATTERNS = [
    "sudo",
    "rm -rf",
    "delete all",
    "drop table",
    "exec(",
    "eval(",
]

logger = logging.getLogger("ms-ai-assistant")
logging.basicConfig(level=logging.INFO)

# ── Rate Limiter ────────────────────────────────────────────────────────────────
class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, user_id: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        self._requests[user_id] = [t for t in self._requests[user_id] if t > window_start]
        if len(self._requests[user_id]) >= self.max_requests:
            return False
        self._requests[user_id].append(now)
        return True


rate_limiter = RateLimiter(max_requests=AI_RATE_LIMIT_PER_MIN, window_seconds=60)

# ── App ─────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="MS-AI-Assistant",
    version="0.1.0",
    description="AI Assistant microservice using Ollama (Llama 3) for ENT EST Salé.",
)
setup_service_runtime(app, "ms-ai-assistant")

# ── RabbitMQ ────────────────────────────────────────────────────────────────────
rabbitmq_connection: aio_pika.abc.AbstractRobustConnection | None = None
consumer_task: asyncio.Task | None = None
context_store: dict[str, Any] = defaultdict(list)

# ── Request Models ──────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1)
    role: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=4000)
    context_refs: list[str] | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    model: str
    tokens_used: int | None = None


class SummarizeRequest(BaseModel):
    course_id: str = Field(min_length=1)
    content: str = Field(min_length=10, max_length=50000)
    max_length: int = Field(default=500, ge=50, le=2000)


class SummarizeResponse(BaseModel):
    summary: str
    key_points: list[str]


class FAQGenerateRequest(BaseModel):
    course_id: str = Field(min_length=1)
    content: str = Field(min_length=10, max_length=50000)
    num_questions: int = Field(default=5, ge=1, le=20)


class FAQItem(BaseModel):
    q: str
    a: str


class FAQGenerateResponse(BaseModel):
    faqs: list[FAQItem]


# ── Auth Helper ─────────────────────────────────────────────────────────────────
async def verify_token(authorization: str | None) -> dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        async with httpx.AsyncClient(timeout=AI_TIMEOUT_SECONDS) as client:
            resp = await client.get(
                f"{AUTH_CORE_BASE_URL}/auth/me",
                headers={"Authorization": authorization},
            )
        if resp.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if resp.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="auth-core returned an unexpected error",
            )
        return resp.json()
    except httpx.RequestError as exc:
        logger.warning(json.dumps({"event": "auth.verify.failed", "error": str(exc)}))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="auth-core unavailable",
        )


def get_current_user(
    authorization: str | None = None,
) -> dict[str, Any]:
    return asyncio.run(verify_token(authorization))


async def async_get_current_user(authorization: str | None = None) -> dict[str, Any]:
    return await verify_token(authorization)


# ── Guardrails ─────────────────────────────────────────────────────────────────
def _check_prompt_injection(prompt: str) -> bool:
    prompt_lower = prompt.lower()
    for pattern in INJECTION_PATTERNS:
        if pattern.search(prompt):
            return True
    for blocked in PROMPT_INJECTION_PATTERNS:
        if blocked in prompt_lower:
            return True
    return False


def _redact_pii(text: str) -> str:
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[EMAIL_REDACTED]", text)
    text = re.sub(r"\b\d{2}/\d{2}/\d{4}\b", "[DATE_REDACTED]", text)
    text = re.sub(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE_REDACTED]", text)
    return text


# ── Ollama Client ───────────────────────────────────────────────────────────────
async def _call_ollama(prompt: str, system: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": AI_MAX_TOKENS,
            "temperature": 0.7,
        },
    }
    if system:
        payload["system"] = system

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT_SECONDS) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload,
            )
        if resp.status_code >= 400:
            error_detail = resp.text
            logger.error(json.dumps({
                "event": "ollama.error",
                "status": resp.status_code,
                "detail": error_detail,
            }))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Ollama error: {error_detail[:200]}",
            )
        return resp.json()
    except httpx.RequestError as exc:
        logger.error(json.dumps({"event": "ollama.connection.failed", "error": str(exc)}))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama service unavailable",
        )


def _build_context_for_role(role: str) -> str:
    role_context = {
        "admin": "You are an AI assistant for an ENT (Espace Numérique de Travail) platform for EST Salé university. The user is an administrator. You can help with system management, user management, and reporting.",
        "teacher": "You are an AI assistant for an ENT (Espace Numérique de Travail) platform for EST Salé university. The user is a teacher. You can help with course management, student interaction, and academic tasks.",
        "student": "You are an AI assistant for an ENT (Espace Numérique de Travail) platform for EST Salé university. The user is a student. You can help with course content, assignments, and academic questions.",
    }
    return role_context.get(role, role_context["student"])


# ── RabbitMQ Consumer ──────────────────────────────────────────────────────────
async def _consume_context_events() -> None:
    global rabbitmq_connection, context_store
    rabbitmq_connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await rabbitmq_connection.channel()
    exchange = await channel.declare_exchange(
        EVENTS_EXCHANGE,
        aio_pika.ExchangeType.TOPIC,
        durable=True,
    )
    queue = await channel.declare_queue(AI_QUEUE, durable=True)
    await queue.bind(exchange, "course.*")
    await queue.bind(exchange, "assignment.*")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                payload = json.loads(message.body.decode("utf-8"))
                event_type = payload.get("event_type", "")
                event_payload = payload.get("payload", {})

                if event_type.startswith("course."):
                    course_id = event_payload.get("course_id")
                    if course_id:
                        context_store[f"course:{course_id}"].append({
                            "type": event_type,
                            "title": event_payload.get("title", ""),
                            "description": event_payload.get("description", ""),
                            "timestamp": payload.get("occurred_at"),
                        })

                logger.info(json.dumps({
                    "event": "context.updated",
                    "event_type": event_type,
                    "context_store_keys": len(context_store),
                }))


# ── Health Check ────────────────────────────────────────────────────────────────
async def _check_ollama_health() -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                return {"ollama": "ok", "model": OLLAMA_MODEL}
            return {"ollama": "error", "status": resp.status_code}
    except Exception as exc:
        return {"ollama": "unavailable", "error": str(exc)[:100]}


# ── Lifecycle ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup() -> None:
    global consumer_task
    try:
        consumer_task = asyncio.create_task(_consume_context_events())
    except Exception as exc:
        logger.warning(json.dumps({
            "event": "rabbitmq.consumer.skip",
            "reason": str(exc),
        }))


@app.on_event("shutdown")
async def shutdown() -> None:
    global consumer_task, rabbitmq_connection
    if consumer_task is not None:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
    if rabbitmq_connection is not None:
        await rabbitmq_connection.close()


# ── Endpoints ───────────────────────────────────────────────────────────────────
@app.get("/ai/health", tags=["ai"])
async def ai_health() -> dict[str, Any]:
    ollama_status = await _check_ollama_health()
    return {
        "status": "ok",
        "service": "ms-ai-assistant",
        "model": OLLAMA_MODEL,
        "ollama": ollama_status,
    }


@app.post("/ai/chat", response_model=ChatResponse, tags=["ai"])
async def chat(
    payload: ChatRequest,
    authorization: str | None = Header(default=None),
) -> ChatResponse:
    claims = await async_get_current_user(authorization)

    if not rate_limiter.is_allowed(claims.get("sub", "anonymous")):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait before sending more messages.",
        )

    if _check_prompt_injection(payload.question):
        logger.warning(json.dumps({
            "event": "prompt.injection.detected",
            "user_id": payload.user_id,
            "question": _redact_pii(payload.question[:100]),
        }))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your question contains potentially unsafe content. Please rephrase.",
        )

    logger.info(json.dumps({
        "event": "ai.chat.request",
        "user_id": payload.user_id,
        "role": payload.role,
        "question_length": len(payload.question),
        "correlation_id": extract_request_id_from_context(payload),
    }))

    role_context = _build_context_for_role(payload.role)
    context_info = ""
    if payload.context_refs:
        for ref in payload.context_refs:
            if ref in context_store:
                context_info += f"\nContext: {json.dumps(context_store[ref])}"

    full_prompt = f"{role_context}{context_info}\n\nUser question: {payload.question}\n\nAnswer:"

    try:
        response = await _call_ollama(full_prompt)
        answer = response.get("response", "I apologize, I couldn't generate a response.")
        tokens_used = response.get("context", {}).get("tokens_predicted") if isinstance(response.get("context"), dict) else None

        logger.info(json.dumps({
            "event": "ai.chat.response",
            "user_id": payload.user_id,
            "answer_length": len(answer),
            "tokens_used": tokens_used,
        }))

        return ChatResponse(
            answer=answer,
            sources=[f"context:{ref}" for ref in (payload.context_refs or [])],
            model=OLLAMA_MODEL,
            tokens_used=tokens_used,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(json.dumps({
            "event": "ai.chat.error",
            "user_id": payload.user_id,
            "error": str(exc),
        }))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate AI response",
        )


@app.post("/ai/summarize", response_model=SummarizeResponse, tags=["ai"])
async def summarize(
    payload: SummarizeRequest,
    authorization: str | None = Header(default=None),
) -> SummarizeResponse:
    claims = await async_get_current_user(authorization)

    if not rate_limiter.is_allowed(claims.get("sub", "anonymous")):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded.",
        )

    if _check_prompt_injection(payload.content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content contains potentially unsafe content.",
        )

    logger.info(json.dumps({
        "event": "ai.summarize.request",
        "course_id": payload.course_id,
        "content_length": len(payload.content),
    }))

    system_prompt = f"You are a helpful assistant. Summarize the following content in approximately {payload.max_length} tokens. Provide a clear summary followed by 3-5 key points."
    full_prompt = f"{system_prompt}\n\nContent to summarize:\n{payload.content}\n\nSummary:"

    try:
        response = await _call_ollama(full_prompt)
        result_text = response.get("response", "")

        lines = result_text.split("\n")
        summary_lines = []
        key_points = []
        is_key_points = False

        for line in lines:
            line = line.strip()
            if "key point" in line.lower() or "important" in line.lower() or "- " in line:
                is_key_points = True
            if is_key_points and line and line not in summary_lines:
                key_points.append(line.lstrip("- *").strip())
            elif line:
                summary_lines.append(line)

        summary = "\n".join(summary_lines[:5]) if summary_lines else result_text[:500]
        if not key_points:
            key_points = [line for line in summary_lines[5:10] if line]

        return SummarizeResponse(
            summary=summary,
            key_points=key_points[:5],
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(json.dumps({
            "event": "ai.summarize.error",
            "course_id": payload.course_id,
            "error": str(exc),
        }))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate summary",
        )


@app.post("/ai/faq/generate", response_model=FAQGenerateResponse, tags=["ai"])
async def generate_faq(
    payload: FAQGenerateRequest,
    authorization: str | None = Header(default=None),
) -> FAQGenerateResponse:
    claims = await async_get_current_user(authorization)

    if not rate_limiter.is_allowed(claims.get("sub", "anonymous")):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded.",
        )

    if _check_prompt_injection(payload.content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content contains potentially unsafe content.",
        )

    logger.info(json.dumps({
        "event": "ai.faq.request",
        "course_id": payload.course_id,
        "num_questions": payload.num_questions,
    }))

    system_prompt = f"You are a helpful educational assistant. Generate exactly {payload.num_questions} FAQ items based on the content below. Format each as: Q: [question]\nA: [answer]"
    full_prompt = f"{system_prompt}\n\nContent:\n{payload.content[:10000]}\n\nFAQs:"

    try:
        response = await _call_ollama(full_prompt)
        result_text = response.get("response", "")

        faqs: list[FAQItem] = []
        current_q = ""
        current_a = ""
        capturing = "q"

        for line in result_text.split("\n"):
            line = line.strip()
            if line.lower().startswith("q:") or line.lower().startswith("question:"):
                if current_q and current_a:
                    faqs.append(FAQItem(q=current_q.strip(), a=current_a.strip()))
                current_q = line.split(":", 1)[1].strip() if ":" in line else line
                current_a = ""
                capturing = "a"
            elif line.lower().startswith("a:") or line.lower().startswith("answer:"):
                current_a = line.split(":", 1)[1].strip() if ":" in line else line
            elif capturing == "a" and line:
                current_a += " " + line

        if current_q and current_a:
            faqs.append(FAQItem(q=current_q.strip(), a=current_a.strip()))

        if not faqs:
            faqs.append(FAQItem(
                q="What is this course about?",
                a=result_text[:500] if result_text else "FAQ generation failed."
            ))

        return FAQGenerateResponse(faqs=faqs[:payload.num_questions])
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(json.dumps({
            "event": "ai.faq.error",
            "course_id": payload.course_id,
            "error": str(exc),
        }))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate FAQ",
        )


def extract_request_id_from_context(payload: Any) -> str | None:
    try:
        return None
    except Exception:
        return None