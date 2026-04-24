# Plan: MS-AI-Assistant (Ollama Llama 3)

## 1. Service Overview

**Rôle**: Assistant IA conversationnel ENT via Ollama (Llama 3 8B Instruct)

**Endpoints**:
- `POST /ai/chat` — Chat contextuel
- `POST /ai/summarize` — Résumé de document/cours
- `POST /ai/faq/generate` — Génération FAQ
- `GET /ai/health` — Health check

**Sécurité**:
- JWT verification via MS-Auth-Core
- RBAC: `student`, `teacher`, `admin`
- Rate limiting & prompt injection guardrails

---

## 2. Architecture

```
Frontend ──► Gateway ──► MS-AI-Assistant ──► Ollama (Llama 3)
                                │
                           RabbitMQ (consomme course.created pour contexte)
```

---

## 3. Structure du Service

```
services/ms-ai-assistant/
├── Dockerfile
├── requirements.txt
├── README.md
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app + endpoints
│   └── runtime.py       # logging, observability
└── tests/
    └── test_main.py
```

---

## 4. Endpoints Détaillés

### 4.1 `POST /ai/chat`
**Input**:
```json
{
  "user_id": "uuid",
  "role": "student|teacher|admin",
  "question": "string",
  "context_refs": ["course_id", ...] // optionnel
}
```
**Output**:
```json
{
  "answer": "string",
  "sources": ["document refs"],
  "model": "llama3",
  "tokens_used": 150
}
```

### 4.2 `POST /ai/summarize`
**Input**:
```json
{
  "course_id": "uuid",
  "max_length": 500 // tokens
}
```
**Output**:
```json
{
  "summary": "string",
  "key_points": ["..."]
}
```

### 4.3 `POST /ai/faq/generate`
**Input**:
```json
{
  "course_id": "uuid",
  "num_questions": 5
}
```
**Output**:
```json
{
  "faqs": [{"q": "...", "a": "..."}]
}
```

---

## 5. Intégration Ollama

- **Base URL**: `OLLAMA_BASE_URL` (défaut: `http://localhost:11434`)
- **Model**: `llama3` (configurable via `OLLAMA_MODEL`)
- **Timeout**: 60s par requête
- **Streaming**: désactivé pour MVP, activable plus tard

---

## 6. Intégration RabbitMQ

**Consumer**: Écoute `course.created.v1` events pour construire un index de contexte local (optionnel pour MVP).

**Exchange**: `ent.events.topic`
**Queue**: `q.ai.context`

---

## 7. Sécurité & Guardrails

1. **Prompt Injection Filter**: blacklist patterns (`Ignore previous instructions`, etc.)
2. **Max tokens**: limit configurable (défaut: 2048)
3. **Rate limit**: 20 req/min par utilisateur (via Redis ou en mémoire)
4. **Audit log**: tous les prompts + réponses logués avec correlation_id
5. **PII Redaction**: masker emails, téléphones dans les logs

---

## 8. Configuration Environment

```env
AUTH_CORE_BASE_URL=http://ms-auth-core:8000
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_TIMEOUT_SECONDS=60
AI_MAX_TOKENS=2048
AI_RATE_LIMIT_PER_MIN=20
RABBITMQ_URL=amqp://ent:ChangeMe_123!@rabbitmq:5672/
EVENTS_EXCHANGE=ent.events.topic
AI_QUEUE=q.ai.context
```

---

## 9. Intégration Gateway

Ajouter au `docker-compose.yml` et `gateway/main.py`:

```python
AI_BASE_URL = os.getenv("GATEWAY_AI_URL", "http://ms-ai-assistant:8000")
```

Routes gateway:
```python
@app.post("/api/ai/chat", ...)
@app.post("/api/ai/summarize", ...)
@app.post("/api/ai/faq/generate", ...)
```

---

## 10. Intégration docker-compose.yml

```yaml
ms-ai-assistant:
  <<: *common
  build:
    context: ./services/ms-ai-assistant
    dockerfile: Dockerfile
  container_name: ent-ms-ai-assistant
  environment:
    AUTH_CORE_BASE_URL: ${AUTH_CORE_BASE_URL:-http://ms-auth-core:8000}
    OLLAMA_BASE_URL: ${OLLAMA_BASE_URL:-http://host.docker.internal:11434}
    OLLAMA_MODEL: ${OLLAMA_MODEL:-llama3}
    OLLAMA_TIMEOUT_SECONDS: ${OLLAMA_TIMEOUT_SECONDS:-60}
    AI_MAX_TOKENS: ${AI_MAX_TOKENS:-2048}
    AI_RATE_LIMIT_PER_MIN: ${AI_RATE_LIMIT_PER_MIN:-20}
    RABBITMQ_URL: ${NOTIFICATION_RABBITMQ_URL:-amqp://ent:ChangeMe_123!@rabbitmq:5672/}
    EVENTS_EXCHANGE: ${EVENTS_EXCHANGE:-ent.events.topic}
    AI_QUEUE: ${AI_QUEUE:-q.ai.context}
    TZ: ${TZ:-Africa/Casablanca}
  ports:
    - "${MS_AI_PORT:-8018}:8000"
  depends_on:
    ms-auth-core:
      condition: service_healthy
    rabbitmq:
      condition: service_healthy
```

---

## 11. Installation Locale Ollama

```bash
# Ubuntu/Debian
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3
ollama serve
```

Ou Docker:
```bash
docker run -d --name ollama -p 11434:11434 ollama/ollama:latest
ollama pull llama3
```

---

## 12. Checklist Implémentation

- [ ] Créer structure `services/ms-ai-assistant/`
- [ ] `requirements.txt` (fastapi, httpx, pydantic, aio-pika)
- [ ] `Dockerfile`
- [ ] `app/main.py` avec endpoints /ai/chat, /ai/summarize, /ai/faq/generate
- [ ] Integration MS-Auth-Core (JWT validation)
- [ ] Client Ollama (appel HTTP API)
- [ ] Guardrails (prompt injection, rate limit, audit log)
- [ ] Consumer RabbitMQ (optionnel pour MVP)
- [ ] Health check endpoint
- [ ] Tests unitaires
- [ ] README.md
- [ ] Ajouter service au docker-compose.yml
- [ ] Ajouter routes au gateway/main.py
- [ ] Vérifier end-to-end avec frontend

---

## 13. Ordre de Réalisation

1. **Setup projet**: structure + deps + Dockerfile
2. **Client Ollama**: abstraction HTTP vers Ollama API
3. **Auth**: intégration JWT avec MS-Auth-Core
4. **Endpoints**: implémenter /ai/chat, /ai/summarize, /ai/faq
5. **Sécurité**: guardrails + rate limit + audit
6. **RabbitMQ**: consumer contexte (optionnel)
7. **Docker Compose**: intégration complète
8. **Gateway**: ajouter routes AI
9. **Tests**: unitaires + intégration
10. **Doc**: README + openapi.yaml

---

## 14. Livrables Attendus

1. Code service FastAPI complet
2. Dockerfile
3. `openapi.yaml`
4. Service int�gr� au `docker-compose.yml`
5. Routes gateway AI
6. Tests passants
7. README.md documenté