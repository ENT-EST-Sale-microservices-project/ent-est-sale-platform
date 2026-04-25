# MS-AI-Assistant

AI Assistant microservice using Ollama (Llama 3) for ENT EST Salé.

## Overview

This service provides:
- **Chat**: Conversational AI assistant with role-based context
- **Summarize**: Generate summaries of course content
- **FAQ Generate**: Auto-generate FAQs from course material

## Endpoints

| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | `/ai/health` | Health check | Public |
| POST | `/ai/chat` | Chat with AI | student, teacher, admin |
| POST | `/ai/summarize` | Summarize content | student, teacher, admin |
| POST | `/ai/faq/generate` | Generate FAQs | teacher, admin |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_CORE_BASE_URL` | `http://ms-auth-core:8000` | MS-Auth-Core URL |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama API URL |
| `OLLAMA_MODEL` | `llama3` | Ollama model name |
| `OLLAMA_TIMEOUT_SECONDS` | `120` | Ollama request timeout |
| `AI_MAX_TOKENS` | `2048` | Max tokens per response |
| `AI_RATE_LIMIT_PER_MIN` | `20` | Rate limit per user/minute |
| `RABBITMQ_URL` | `amqp://ent:ChangeMe_123!@rabbitmq:5672/` | RabbitMQ URL |
| `EVENTS_EXCHANGE` | `ent.events.topic` | RabbitMQ exchange |
| `AI_QUEUE` | `q.ai.context` | RabbitMQ queue for context |

## Ollama Setup

Ollama runs as a separate container (defined in docker-compose.yml) with Llama 3 pre-loaded.

### Manual Ollama Commands

```bash
# Pull model
ollama pull llama3

# Test model
ollama run llama3 "Hello"

# Check available models
curl http://localhost:11434/api/tags
```

## Security Features

- JWT authentication via MS-Auth-Core
- Prompt injection detection
- Rate limiting (20 req/min per user)
- PII redaction in logs
- Audit logging

## Example Usage

### Chat

```bash
curl -X POST http://localhost:8018/ai/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "user_id": "uuid",
    "role": "student",
    "question": "How do I submit my assignment?",
    "context_refs": ["course-uuid-1"]
  }'
```

### Summarize

```bash
curl -X POST http://localhost:8018/ai/summarize \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "course_id": "uuid",
    "content": "Course content text...",
    "max_length": 500
  }'
```

### Generate FAQ

```bash
curl -X POST http://localhost:8018/ai/faq/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "course_id": "uuid",
    "content": "Course content text...",
    "num_questions": 5
  }'
```

## Architecture

```
Frontend → Gateway → MS-AI-Assistant → Ollama (Llama 3)
                  ↳ RabbitMQ (context events)
```

## Local Development

```bash
# Run locally with Ollama
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama3
export AUTH_CORE_BASE_URL=http://localhost:8010

uvicorn app.main:app --reload --port 8018
```

## Port

Internal: `8018`