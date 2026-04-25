# ENT EST Salé — Documentation Technique Complète

## Document généré pour impression DOCX

---

# Table des Matières

1. [Vue d'Ensemble du Projet](#1-vue-ensemble-du-projet)
2. [Architecture Microservices](#2-architecture-microservices)
3. [Cartographie des Services](#3-cartographie-des-services)
4. [Infrastructure et Stack Technique](#4-infrastructure-et-stack-technique)
5. [Schémas de Communication](#5-schémas-de-communication)
6. [Modèles de Données (Cassandra)](#6-modèles-de-données-cassandra)
7. [Endpoints API Détaillés](#7-endpoints-api-détaillés)
8. [Sécurité et Authentification](#8-sécurité-et-authentification)
9. [Événements et Messaging (RabbitMQ)](#9-événements-et-messaging-rabbitmq)
10. [Frontend et Interface Utilisateur](#10-frontend-et-interface-utilisateur)
11. [Configuration Docker Compose](#11-configuration-docker-compose)
12. [Débogage et Maintenance](#12-débogage-et-maintenance)

---

# 1. Vue d'Ensemble du Projet

## 1.1 Objectif

Mise en place d'un **ENT (Espace Numérique de Travail)** pour l'EST Salé (École Supérieure de Technologie de Salé, Maroc), basé sur une architecture **microservices**, **sécurisée**, et **scalable**, déployée en cloud privé (VMware ESXi + Ubuntu + Kubernetes) avec une couche IA locale via **Ollama (Llama 3)**.

## 1.2 Fonctionnalités Principales

| Module | Description |
|--------|-------------|
| **Gestion Utilisateurs** | Inscription, authentification, rôles (étudiant, enseignant, admin) |
| **Gestion des Cours** | Création, upload de ressources, consultation, téléchargement |
| **Communication** | Notifications email/in-app, forum de discussion, chat temps réel |
| **Gestion Académique** | Calendrier, emplois du temps, examens/devoirs |
| **Assistant IA** | Chatbot conversationnel, résumé de documents, génération FAQ |

## 1.3 Rôles Utilisateurs

| Rôle | Droits |
|------|--------|
| **admin** | Gestion complète utilisateurs, supervision système |
| **teacher** | Création cours, upload ressources, publication devoirs, notation |
| **student** | Consultation cours, téléchargement, soumission devoirs, forum |

## 1.4 Informations Projet

- **Version**: 1.0.0
- **Stack Backend**: Python FastAPI
- **Stack Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Base de données**: Apache Cassandra 5.0
- **Object Storage**: MinIO
- **Message Broker**: RabbitMQ 4.1.3
- **IAM**: Keycloak 26.1.4
- **IA Runtime**: Ollama (Llama 3 8B Instruct)
- **Conteneurisation**: Docker + Docker Compose

---

# 2. Architecture Microservices

## 2.1 Principes Architecturales

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React SPA)                           │
│                          http://localhost:3000 (nginx)                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MS-API-GATEWAY/BFF (Port 8008)                       │
│                   Point d'entrée unique - JWT guard + routing               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          ▼                         ▼                         ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐
│ MS-AUTH-CORE     │  │ MS-IDENTITY-ADMIN│  │ MS-COURSE-CONTENT        │
│ (Port 8010)      │  │ (Port 8013)      │  │ (Port 8011)              │
│ JWT Validation   │  │ User Management  │  │ Course Creation + Upload │
└──────────────────┘  └──────────────────┘  └──────────────────────────┘
          │                         │                         │
          ▼                         ▼                         ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐
│ MS-COURSE-ACCESS │  │ MS-NOTIFICATION  │  │ MS-CALENDAR-SCHEDULE     │
│ (Port 8012)      │  │ (Port 8014)      │  │ (Port 8015)              │
│ Course Catalog   │  │ Event Consumer   │  │ Calendar Events          │
└──────────────────┘  └──────────────────┘  └──────────────────────────┘
                                    │                         │
          ┌─────────────────────────┼─────────────────────────┼────────────┐
          ▼                         ▼                         ▼            ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐
│ MS-FORUM-CHAT    │  │ MS-EXAM-ASSIGNMENT│  │ MS-AI-ASSISTANT  │  │ RABBITMQ     │
│ (Port 8016)      │  │ (Port 8017)       │  │ (Port 8018)      │  │ (5672/15672) │
│ Forum + WebSocket│  │ Assignments      │  │ Ollama Llama 3   │  │              │
└──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────┘
```

## 2.2 Diagramme d'Architecture Détaillé

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              INFRASTRUCTURE LAYER                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │ KEYCLOAK    │    │  POSTGRESQL │    │   RABBITMQ  │    │    MinIO    │   │
│  │  (8080)     │───▶│   (5432)    │    │ (5672/15672)│    │  (9000/9001)│   │
│  │  IAM/OIDC   │    │   Database  │    │   Messaging │    │   Object    │   │
│  └─────────────┘    └─────────────┘    └─────────────┘    │   Storage   │   │
│                                                          └─────────────┘   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │  CASSANDRA  │    │    REDIS     │    │   OLLAMA     │    │  MAILPIT    │   │
│  │   (9042)    │    │   (6379)     │    │   (11434)    │    │  (1025/8025)│   │
│  │  Database   │    │    Cache     │    │  AI Runtime  │    │   SMTP Dev  │   │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘   │
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                       │
│  │ PROMETHEUS  │    │   GRAFANA   │    │    DNS/      │                       │
│  │  (9090)     │    │   (3001)    │    │  Resolution  │                       │
│  │  Metrics    │    │ Dashboards  │    │              │                       │
│  └─────────────┘    └─────────────┘    └─────────────┘                       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 2.3 Flux de Données Principal

```
[User] ──▶ [Frontend] ──▶ [Gateway] ──▶ [MS-Auth-Core] ──▶ [Keycloak JWKS]
    │                                              │
    │◀────── JWT Validation ◀───────────────────────┘
    │
    ▼
[Service Backend] ──▶ [Cassandra/MinIO]
    │
    ▼
[RabbitMQ] ──▶ [Notification Consumer] ──▶ [Email/SMTP]
    │
    ▼
[AI Assistant] ──▶ [Ollama]
```

---

# 3. Cartographie des Services

## 3.1 Services Implémentés

| Service | Port | Description | Rôles |
|---------|------|-------------|-------|
| MS-Auth-Core | 8010 | Validation JWT + extraction identité | Public |
| MS-Identity-Admin | 8013 | Provisioning utilisateurs + rôles | Admin |
| MS-Course-Content | 8011 | Création cours + upload fichiers | Teacher, Admin |
| MS-Course-Access | 8012 | Catalogue étudiants + téléchargement | Student |
| MS-Notification | 8014 | Notifications email + in-app | All |
| MS-Calendar-Schedule | 8015 | Événements calendrier | All |
| MS-Forum-Chat | 8016 | Forum + Chat WebSocket | All |
| MS-Exam-Assignment | 8017 | Devoirs + soumissions + notation | All |
| MS-AI-Assistant | 8018 | Assistant IA (Ollama/Llama 3) | All |
| MS-API-Gateway | 8008 | Routing + CORS + Auth | All |
| Frontend | 3000 | Application React SPA | All |

## 3.2 Services d'Infrastructure

| Service | Image | Ports | Description |
|---------|-------|-------|-------------|
| Keycloak | keycloak:26.1.4 | 8080, 9000 | IAM (OAuth2/OIDC) |
| PostgreSQL | postgres:16 | 5432 | Keycloak database |
| RabbitMQ | rabbitmq:4.1.3 | 5672, 15672 | Message broker |
| MinIO | quay.io/minio/minio | 9000, 9001 | Object storage |
| Cassandra | cassandra:5.0 | 9042 | Distributed database |
| Redis | redis:7-alpine | 6379 | Cache/session |
| Mailpit | axllent/mailpit:v1.18 | 1025, 8025 | SMTP testing |
| Ollama | ollama/ollama | 11434 | AI runtime |
| Prometheus | prom/prometheus | 9090 | Metrics collection |
| Grafana | grafana/grafana | 3001 | Dashboards |

---

# 4. Infrastructure et Stack Technique

## 4.1 Versions et Dépendances

### Services Python (requirements.txt)

| Package | Version | Usage |
|---------|---------|-------|
| fastapi | >=0.111,<1.0 | Web framework |
| uvicorn[standard] | >=0.30,<1.0 | ASGI server |
| httpx | >=0.27,<1.0 | HTTP client |
| pydantic | >=2.7,<3.0 | Data validation |
| prometheus-client | >=0.20,<1.0 | Metrics |
| PyJWT | latest | JWT handling |
| cryptography | latest | Cryptographic operations |
| cassandra-driver | >=3.29,<4.0 | Cassandra client |
| boto3 | latest | AWS S3 (MinIO) |
| aio-pika | >=9.4,<10.0 | RabbitMQ async |
| aiosmtplib | >=3.0,<4.0 | Async SMTP |

### Frontend (package.json)

| Package | Version | Usage |
|---------|---------|-------|
| react | ^19.2.4 | UI framework |
| react-dom | ^19.2.4 | DOM rendering |
| react-router-dom | ^7.14.1 | Routing |
| @base-ui/react | ^1.4.0 | UI components |
| tailwindcss | ^4.2.2 | Styling |
| lucide-react | ^1.8.0 | Icons |
| shadcn | ^4.3.0 | Component library |

## 4.2 Configuration Environment Variables

### Variables Communes

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_CORE_BASE_URL` | `http://ms-auth-core:8000` | MS-Auth-Core URL |
| `AUTH_REALM` | `ent-est` | Keycloak realm |
| `AUTH_ISSUER` | `http://localhost:8080/realms/ent-est` | JWT issuer |
| `AUTH_JWKS_URL` | `http://keycloak:8080/realms/ent-est/protocol/openid-connect/certs` | JWKS endpoint |
| `CASSANDRA_CONTACT_POINTS` | `cassandra` | Cassandra hosts |
| `CASSANDRA_PORT` | `9042` | Cassandra port |
| `CASSANDRA_KEYSPACE` | `ent_est` | Keyspace name |
| `RABBITMQ_URL` | `amqp://ent:ChangeMe_123!@rabbitmq:5672/` | RabbitMQ URL |
| `EVENTS_EXCHANGE` | `ent.events.topic` | Event exchange name |

### Variables MinIO

| Variable | Default | Description |
|----------|---------|-------------|
| `MINIO_ENDPOINT` | `http://minio:9000` | MinIO endpoint |
| `MINIO_ROOT_USER` | `minio` | MinIO access key |
| `MINIO_ROOT_PASSWORD` | `ChangeMe_123!` | MinIO secret key |
| `MINIO_COURSE_BUCKET` | `ent-courses` | Course files bucket |
| `MINIO_SIGNING_ENDPOINT` | `http://localhost:9002` | Pre-signed URL endpoint |

### Variables Ollama

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama API URL |
| `OLLAMA_MODEL` | `llama3` | Model name |
| `OLLAMA_TIMEOUT_SECONDS` | `120` | Request timeout |
| `AI_MAX_TOKENS` | `2048` | Max response tokens |
| `AI_RATE_LIMIT_PER_MIN` | `20` | Rate limit per user |

---

# 5. Schémas de Communication

## 5.1 Communication Synchrone (REST)

```
┌──────────┐     REST/HTTP      ┌──────────┐
│ Frontend │ ─────────────────▶ │ Gateway  │
└──────────┘                    └──────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          ▼                        ▼                        ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ MS-AUTH-CORE     │  │ MS-COURSE-CONTENT│  │ MS-AI-ASSISTANT  │
│ /auth/me         │  │ /courses         │  │ /ai/chat         │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

## 5.2 Communication Asynchrone (RabbitMQ)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ MS-Course-Content│     │ MS-Exam-Assignment│    │ MS-Forum-Chat   │
│ course.created   │     │ assignment.pub   │     │ forum.message   │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌────────────────────────┐
                    │   RabbitMQ Exchange     │
                    │   ent.events.topic      │
                    │   (topic exchange)      │
                    └───────────┬─────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ q.notification  │  │ q.notification  │  │ q.ai.context    │
│ (user/course)   │  │ (assignment)    │  │ (AI context)    │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                     │                     │
         ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ MS-Notification │  │ MS-Notification │  │ MS-AI-Assistant │
│ Consumer        │  │ Consumer        │  │ Consumer        │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 5.3 Matrice de Communication Inter-Services

| Source | Type | Cible | Protocole | Contrat |
|--------|------|-------|-----------|---------|
| Frontend | HTTP | Gateway | REST/JSON | Unified API |
| Gateway | HTTP | Auth/Core | REST/JWT | Token validation |
| Gateway | HTTP | Course-Content | REST/JSON+Multipart | Course CRUD |
| Gateway | HTTP | Course-Access | REST/JSON | Course listing |
| Gateway | HTTP | Identity-Admin | REST/JSON | User management |
| Gateway | HTTP | AI-Assistant | REST/JSON | Chat/Summarize |
| MS-Course-Content | Event | RabbitMQ | AMQP Topic | course.created.v1 |
| MS-Exam-Assignment | Event | RabbitMQ | AMQP Topic | assignment.published.v1 |
| MS-Forum-Chat | Event | RabbitMQ | AMQP Topic | forum.message.posted.v1 |

## 5.4 Modèle Standard d'Événement

Tous les événements RabbitMQ suivent ce contrat :

```json
{
  "event_id": "uuid-v4",
  "event_type": "course.created.v1",
  "occurred_at": "2026-04-24T12:00:00Z",
  "producer": "ms-course-content",
  "correlation_id": "uuid-for-tracing",
  "payload": {
    "course_id": "uuid",
    "title": "string",
    "module_code": "string",
    "teacher_id": "uuid"
  }
}
```

### Routing Keys par Service

| Service | Routing Keys |
|---------|--------------|
| MS-Identity-Admin | `user.created`, `user.updated`, `user.role.assigned` |
| MS-Course-Content | `course.created`, `course.updated`, `course.deleted`, `asset.uploaded`, `asset.deleted` |
| MS-Exam-Assignment | `assignment.published`, `assignment.submitted`, `grade.published` |
| MS-Forum-Chat | `forum.thread.created`, `forum.message.posted` |
| MS-Calendar-Schedule | `calendar.event.created`, `calendar.event.updated` |

---

# 6. Modèles de Données (Cassandra)

## 6.1 Keyspace

```sql
CREATE KEYSPACE IF NOT EXISTS ent_est
WITH replication = {'class':'SimpleStrategy','replication_factor':1};
```

## 6.2 Tables

### user_profiles

```sql
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id       text PRIMARY KEY,
    username      text,
    email         text,
    full_name     text,
    role          text,
    status        text,
    created_at    timestamp,
    updated_at    timestamp
);
```

### courses

```sql
CREATE TABLE IF NOT EXISTS courses (
    course_id     text PRIMARY KEY,
    title         text,
    description   text,
    module_code   text,
    tags          list<text>,
    visibility    text,
    teacher_id    text,
    created_at    timestamp,
    updated_at    timestamp
);
```

### course_assets

```sql
CREATE TABLE IF NOT EXISTS course_assets (
    course_id        text,
    asset_id         text,
    filename         text,
    content_type     text,
    size_bytes       bigint,
    minio_bucket     text,
    minio_object_key text,
    created_at       timestamp,
    PRIMARY KEY (course_id, asset_id)
);
```

### notifications

```sql
CREATE TABLE IF NOT EXISTS notifications (
    user_id       text,
    created_at    timestamp,
    notif_id      text,
    event_type    text,
    title         text,
    body          text,
    correlation_id text,
    read          boolean,
    PRIMARY KEY (user_id, created_at, notif_id)
) WITH CLUSTERING ORDER BY (created_at DESC, notif_id ASC);
```

### calendar_events

```sql
CREATE TABLE IF NOT EXISTS calendar_events (
    event_id      text PRIMARY KEY,
    title         text,
    description   text,
    event_type    text,
    module_code   text,
    start_time    timestamp,
    end_time      timestamp,
    created_by    text,
    created_at    timestamp,
    updated_at    timestamp
);
```

### forum_threads

```sql
CREATE TABLE IF NOT EXISTS forum_threads (
    thread_id     text PRIMARY KEY,
    title         text,
    body          text,
    author_id     text,
    author_name   text,
    module_code   text,
    created_at    timestamp
);
```

### forum_messages

```sql
CREATE TABLE IF NOT EXISTS forum_messages (
    thread_id     text,
    created_at    timestamp,
    message_id    text,
    body          text,
    author_id     text,
    author_name   text,
    PRIMARY KEY (thread_id, created_at, message_id)
) WITH CLUSTERING ORDER BY (created_at ASC, message_id ASC);
```

### forum_thread_counters

```sql
CREATE TABLE IF NOT EXISTS forum_thread_counters (
    thread_id     text PRIMARY KEY,
    reply_count   counter
);
```

### assignments

```sql
CREATE TABLE IF NOT EXISTS assignments (
    assignment_id   text PRIMARY KEY,
    title           text,
    description     text,
    due_date        timestamp,
    module_code     text,
    created_by      text,
    created_by_name text,
    max_grade       float,
    status          text,
    created_at      timestamp
);
```

### submissions

```sql
CREATE TABLE IF NOT EXISTS submissions (
    submission_id    text PRIMARY KEY,
    assignment_id    text,
    student_id       text,
    student_name     text,
    submitted_at     timestamp,
    content_text     text,
    minio_object_key text,
    grade            float,
    feedback         text,
    graded_at        timestamp
);
```

### submissions_by_assignment

```sql
CREATE TABLE IF NOT EXISTS submissions_by_assignment (
    assignment_id  text,
    submitted_at   timestamp,
    submission_id  text,
    PRIMARY KEY (assignment_id, submitted_at, submission_id)
) WITH CLUSTERING ORDER BY (submitted_at DESC, submission_id ASC);
```

---

# 7. Endpoints API Détaillés

## 7.1 MS-Auth-Core (Port 8010)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/auth/health` | Health check | Public |
| GET | `/auth/me` | Get current user claims | Bearer |
| POST | `/auth/introspect` | Token introspection | Public |

## 7.2 MS-Identity-Admin (Port 8013)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/identity-admin/health` | Health check | Public |
| POST | `/admin/users` | Create user | Admin |
| GET | `/admin/users` | List users | Admin |
| GET | `/admin/users/{user_id}` | Get user | Admin |
| PATCH | `/admin/users/{user_id}/roles` | Update roles | Admin |

## 7.3 MS-Course-Content (Port 8011)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/courses-content/health` | Health check | Public |
| GET | `/courses` | List own courses | Teacher/Admin |
| POST | `/courses` | Create course | Teacher/Admin |
| GET | `/courses/{course_id}` | Get course | Teacher/Admin |
| PUT | `/courses/{course_id}` | Update course | Teacher/Admin |
| DELETE | `/courses/{course_id}` | Delete course | Teacher/Admin |
| POST | `/courses/{course_id}/assets` | Upload asset | Teacher/Admin |
| DELETE | `/courses/{course_id}/assets/{asset_id}` | Delete asset | Teacher/Admin |
| GET | `/internal/courses` | Internal listing | Internal token |
| GET | `/internal/courses/{course_id}` | Internal get | Internal token |

## 7.4 MS-Course-Access (Port 8012)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/courses-access/health` | Health check | Public |
| GET | `/courses` | List available courses | Student |
| GET | `/courses/{course_id}` | Get course details | Student |
| POST | `/courses/{course_id}/download-links` | Generate presigned URL | Student |

## 7.5 MS-Notification (Port 8014)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/notifications/health` | Health check | Public |
| POST | `/notifications/test` | Send test notification | Public |
| GET | `/notifications/{user_id}` | List notifications | Internal |
| PATCH | `/notifications/{user_id}/{notif_id}/read` | Mark read | Internal |
| PATCH | `/notifications/{user_id}/read-all` | Mark all read | Internal |

## 7.6 MS-Calendar-Schedule (Port 8015)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/calendar/health` | Health check | Public |
| POST | `/calendar/events` | Create event | Teacher/Admin |
| GET | `/calendar/events` | List events | All |
| GET | `/calendar/events/{event_id}` | Get event | All |
| PATCH | `/calendar/events/{event_id}` | Update event | Teacher/Admin |
| DELETE | `/calendar/events/{event_id}` | Delete event | Teacher/Admin |

## 7.7 MS-Forum-Chat (Port 8016)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/forum/health` | Health check | Public |
| POST | `/forum/threads` | Create thread | Authenticated |
| GET | `/forum/threads` | List threads | Authenticated |
| GET | `/forum/threads/{thread_id}` | Get thread with messages | Authenticated |
| POST | `/forum/threads/{thread_id}/messages` | Post message | Authenticated |
| WS | `/chat/ws?token=JWT&room=MODULE` | WebSocket chat | JWT |

## 7.8 MS-Exam-Assignment (Port 8017)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/exams/health` | Health check | Public |
| POST | `/assignments` | Create assignment | Teacher/Admin |
| GET | `/assignments` | List assignments | Authenticated |
| GET | `/assignments/{assignment_id}` | Get assignment | Authenticated |
| POST | `/assignments/{assignment_id}/submissions` | Submit work | Student |
| GET | `/assignments/{assignment_id}/submissions` | List submissions | Authenticated |
| POST | `/assignments/{assignment_id}/submissions/{submission_id}/grade` | Grade | Teacher/Admin |

## 7.9 MS-AI-Assistant (Port 8018)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/ai/health` | Health check + Ollama status | Public |
| POST | `/ai/chat` | Conversational chat | Authenticated |
| POST | `/ai/summarize` | Summarize content | Authenticated |
| POST | `/ai/faq/generate` | Generate FAQs | Authenticated |

## 7.10 MS-API-Gateway (Port 8008)

All routes proxy to above services:

| Method | Endpoint | Description | Target |
|--------|----------|-------------|--------|
| GET | `/gateway/health` | Gateway health | - |
| GET | `/api/me` | Current user | MS-Auth-Core |
| GET | `/api/protected/*` | Role-protected test endpoints | MS-Auth-Core |
| GET/POST | `/api/content/courses/*` | Course management | MS-Course-Content |
| GET | `/api/access/courses/*` | Course access | MS-Course-Access |
| GET/POST | `/api/admin/users/*` | User management | MS-Identity-Admin |
| GET/PATCH | `/api/notifications/*` | Notifications | MS-Notification |
| GET/POST | `/api/calendar/events/*` | Calendar | MS-Calendar-Schedule |
| GET/POST | `/api/forum/threads/*` | Forum | MS-Forum-Chat |
| GET/POST | `/api/assignments/*` | Assignments | MS-Exam-Assignment |
| GET/POST | `/api/ai/*` | AI Assistant | MS-AI-Assistant |
| GET | `/api/stats` | Role-based statistics | Aggregated |

---

# 8. Sécurité et Authentification

## 8.1 Flux d'Authentification

```
1. User ──▶ Login Page ──▶ Keycloak Direct Access Grant
2. Keycloak ──▶ JWT Access Token + Refresh Token
3. Frontend stores tokens in localStorage
4. Every API request: Authorization: Bearer <access_token>
5. Gateway validates token via MS-Auth-Core
6. MS-Auth-Core validates against Keycloak JWKS
```

## 8.2 JWT Structure

```json
{
  "sub": "user-uuid",
  "preferred_username": "johndoe",
  "email": "johndoe@est-salé.ma",
  "realm_access": {
    "roles": ["student", "default-roles-ent-est"]
  },
  "iss": "http://keycloak:8080/realms/ent-est",
  "aud": "ent-gateway,ent-frontend",
  "exp": 1714060800,
  "iat": 1714057200
}
```

## 8.3 Rôles et Permissions

| Rôle | Endpoints Autorisés |
|------|---------------------|
| **admin** | Tous les endpoints |
| **teacher** | Course CRUD, Assignment publish, Grade, Calendar events |
| **student** | Course access, Submit assignments, Forum, Calendar view |
| **authenticated** | Notifications, Forum read, Chat |

## 8.4 Mesures de Sécurité Implémentées

| Mesure | Implémentation |
|--------|----------------|
| JWT Validation | PyJWKClient + RS256 |
| RBAC | Role extraction from JWT claims |
| Rate Limiting | AI service: 20 req/min per user |
| Prompt Injection Detection | Regex patterns + blocked keywords |
| PII Redaction | Emails, dates, phones masked in logs |
| CORS | Configured origins in Gateway |
| Correlation ID | X-Request-ID header propagation |
| Audit Logging | JSON structured logs with request tracking |

## 8.5 Demo Accounts

| Username | Password | Rôle |
|----------|----------|------|
| admin | Admin_123! | admin |
| teacher | Teacher_123! | teacher |
| student | Student_123! | student |

---

# 9. Événements et Messaging (RabbitMQ)

## 9.1 Exchange Configuration

- **Name**: `ent.events.topic`
- **Type**: Topic
- **Durable**: true

## 9.2 Queue Bindings

| Queue | Binding Keys | Consumer |
|-------|--------------|----------|
| q.notification.user | user.* | MS-Notification |
| q.notification.course | course.* | MS-Notification |
| q.notification.assignment | assignment.* | MS-Notification |
| q.notification.grade | grade.* | MS-Notification |
| q.notification.forum | forum.* | MS-Notification |
| q.notification.calendar | calendar.* | MS-Notification |
| q.ai.context | course.*, assignment.* | MS-AI-Assistant |

## 9.3 Types d'Événements

| Event Type | Producer | Payload Keys |
|------------|----------|--------------|
| `user.created.v1` | MS-Identity-Admin | user_id, email, role |
| `user.updated.v1` | MS-Identity-Admin | user_id, changes |
| `user.role.assigned.v1` | MS-Identity-Admin | user_id, role, assigned_by |
| `course.created.v1` | MS-Course-Content | course_id, title, module_code, teacher_id |
| `course.updated.v1` | MS-Course-Content | course_id, changes |
| `course.deleted.v1` | MS-Course-Content | course_id |
| `asset.uploaded.v1` | MS-Course-Content | course_id, asset_id, filename, size_bytes |
| `asset.deleted.v1` | MS-Course-Content | course_id, asset_id |
| `assignment.published.v1` | MS-Exam-Assignment | assignment_id, title, module_code, due_date |
| `assignment.submitted.v1` | MS-Exam-Assignment | submission_id, assignment_id, student_id |
| `grade.published.v1` | MS-Exam-Assignment | submission_id, assignment_id, student_id, grade |
| `forum.thread.created.v1` | MS-Forum-Chat | thread_id, title, module_code, author_id |
| `forum.message.posted.v1` | MS-Forum-Chat | message_id, thread_id, author_id |

---

# 10. Frontend et Interface Utilisateur

## 10.1 Pages Implémentées

| Page | Route | Rôles | Description |
|------|-------|-------|-------------|
| Login | `/login` | Public | Connexion utilisateur |
| Dashboard | `/app` | All | Statistiques par rôle |
| Admin | `/app/admin` | admin | Gestion utilisateurs |
| Teacher | `/app/teacher` | teacher, admin | Création cours, upload |
| Student | `/app/student` | student | Catalogue cours, téléchargements |
| Calendar | `/app/calendar` | All | Calendrier académique |
| Forum | `/app/forum` | All | Discussions |
| Exams | `/app/exams` | All | Devoirs et soumissions |
| AI Assistant | `/app/assistant` | All | Chatbot IA |
| Notifications | `/app/notifications` | All | Centre de notifications |
| Profile | `/app/profile` | All | Profil utilisateur |
| Not Found | `*` | Public | Page 404 |
| Unauthorized | `/unauthorized` | Public | Page 403 |

## 10.2 Structure du Frontend

```
frontend/
├── src/
│   ├── main.tsx                 # Entry point
│   ├── App.tsx                  # Routes configuration
│   ├── index.css                # Global styles
│   ├── components/
│   │   ├── app-shell.tsx        # Main layout (sidebar + header)
│   │   ├── route-guards.tsx     # Protected routes
│   │   └── ui/                   # shadcn/ui components
│   ├── context/
│   │   ├── auth-context.tsx      # Auth state + apiFetch
│   │   └── theme-context.tsx     # Dark/light mode
│   ├── lib/
│   │   └── auth.ts              # Keycloak integration
│   └── pages/
│       ├── login-page.tsx
│       ├── dashboard-page.tsx
│       ├── admin-page.tsx
│       ├── teacher-page.tsx
│       ├── student-page.tsx
│       ├── calendar-page.tsx
│       ├── forum-page.tsx
│       ├── exam-page.tsx
│       ├── assistant-page.tsx
│       ├── notifications-page.tsx
│       ├── profile-page.tsx
│       ├── not-found-page.tsx
│       └── unauthorized-page.tsx
├── Dockerfile                   # Nginx-based production build
├── vite.config.ts
├── package.json
└── tailwind.config.js
```

## 10.3 Technologies UI

| Technologie | Version | Usage |
|------------|---------|-------|
| React | 19.2.4 | UI framework |
| TypeScript | ~6.0.2 | Type safety |
| Tailwind CSS | 4.2.2 | Styling |
| shadcn/ui | 4.3.0 | Component library |
| lucide-react | 1.8.0 | Icons |
| react-router-dom | 7.14.1 | Routing |

## 10.4 API Integration

Le frontend utilise `apiFetch` depuis `AuthContext` pour toutes les requêtes :

```typescript
const response = await apiFetch<T>('/api/endpoint', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
});
```

Cette méthode :
1. Auto-refresh le token si expiré
2. Ajoute `Authorization: Bearer <token>`
3. Parse la réponse JSON
4. Throw une erreur si non-OK

---

# 11. Configuration Docker Compose

## 11.1 Structure des Services

```yaml
services:
  # Infrastructure
  postgres-keycloak:  # PostgreSQL pour Keycloak
  keycloak:           # IAM
  keycloak-realm-bootstrap:  # Setup realm
  keycloak-users-bootstrap:  # Demo users
  rabbitmq:           # Message broker
  minio:              # Object storage
  minio-init:         # Bucket setup
  cassandra:          # Database
  cassandra-init:     # Schema setup
  redis:              # Cache
  mailpit:            # SMTP dev server
  
  # Microservices
  ms-auth-core:
  ms-api-gateway:
  ms-identity-admin:
  ms-course-content:
  ms-course-access:
  ms-notification:
  ms-calendar-schedule:
  ms-forum-chat:
  ms-exam-assignment:
  ms-ai-assistant:
  
  # Frontend
  frontend:
  
  # Observability
  prometheus:
  grafana:
```

## 11.2 Variables d'Environnement Importantes

```env
COMPOSE_PROJECT_NAME=ent-est-platform
TZ=Africa/Casablanca

# Keycloak
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=ChangeMe_123!
KEYCLOAK_HOSTNAME=localhost
KEYCLOAK_DB_PASSWORD=ChangeMe_123!

# RabbitMQ
RABBITMQ_USER=ent
RABBITMQ_PASSWORD=ChangeMe_123!

# MinIO
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=ChangeMe_123!
MINIO_DEFAULT_BUCKETS=ent-courses,ent-uploads,ent-logs

# Cassandra
CASSANDRA_PASSWORD=ChangeMe_123!
CASSANDRA_KEYSPACE=ent_est

# Redis
REDIS_PASSWORD=ChangeMe_123!

# Ollama (AI)
OLLAMA_PORT=11434
OLLAMA_MODEL=llama3

# Service Ports
MS_AUTH_CORE_PORT=8010
MS_API_GATEWAY_PORT=8008
MS_IDENTITY_ADMIN_PORT=8013
MS_COURSE_CONTENT_PORT=8011
MS_COURSE_ACCESS_PORT=8012
MS_NOTIFICATION_PORT=8014
MS_CALENDAR_PORT=8015
MS_FORUM_PORT=8016
MS_EXAM_PORT=8017
MS_AI_PORT=8018
FRONTEND_PORT=3000
GRAFANA_PORT=3001
```

## 11.3 Profiles

Le profile `ai` active Ollama :

```bash
docker compose --profile ai up -d
```

Services avec profile `ai` :
- `ollama`: Runtime Ollama (port 11434)
- `ollama-pull`: Télécharge modèle llama3 au premier démarrage

## 11.4 Volumes

```yaml
volumes:
  keycloak_postgres_data:  # PostgreSQL data
  rabbitmq_data:           # RabbitMQ data
  minio_data:              # MinIO data
  cassandra_data:          # Cassandra data
  redis_data:              # Redis data
  grafana_data:            # Grafana data
  ollama_data:              # Ollama models (persiste llama3)
```

---

# 12. Débogage et Maintenance

## 12.1 Commandes Utiles

### Démarrage

```bash
# Tous services (sans IA)
docker compose up -d

# Avec IA (Ollama)
docker compose --profile ai up -d

# Vérifier statut
docker compose ps
```

### Logs

```bash
# Tous les services
docker compose logs -f

# Service spécifique
docker compose logs -f ms-ai-assistant
docker compose logs -f gateway

# Errors only
docker compose logs -f --tail=100 | grep ERROR
```

### Accès aux Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Login via Keycloak |
| Keycloak Admin | http://localhost:8080/admin | admin / ChangeMe_123! |
| RabbitMQ | http://localhost:15672 | ent / ChangeMe_123! |
| MinIO Console | http://localhost:9001 | minio / ChangeMe_123! |
| Grafana | http://localhost:3001 | admin / ChangeMe_123! |
| Prometheus | http://localhost:9090 | - |
| Mailpit | http://localhost:8025 | - |

### Tests API

```bash
# Health checks
curl http://localhost:8008/gateway/health
curl http://localhost:8010/auth/health
curl http://localhost:8018/ai/health

# Avec authentification
TOKEN=$(curl -s -X POST http://localhost:8080/realms/ent-est/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&client_id=ent-frontend&username=student&password=Student_123!" \
  | jq -r '.access_token')

# Test via gateway
curl -H "Authorization: Bearer $TOKEN" http://localhost:8008/api/me
```

## 12.2 Reconstruction des Services

```bash
# Rebuild un service
docker compose build ms-ai-assistant
docker compose up -d ms-ai-assistant

# Rebuild tous
docker compose build
docker compose up -d

# Clean restart
docker compose down -v
docker compose up -d --build
```

## 12.3 Commandes Cassandra CQL

```bash
docker exec -it ent-cassandra cqlsh -u cassandra -p ChangeMe_123!

# Lister keyspaces
DESCRIBE KEYSPACES;

# Utiliser keyspace
USE ent_est;

# Lister tables
DESCRIBE TABLES;

# Voir données
SELECT * FROM courses LIMIT 10;
SELECT * FROM user_profiles;
```

## 12.4 Surveillance

```bash
# Métriques Prometheus targets
curl http://localhost:9090/api/v1/targets

# Vérifier santé Ollama
docker exec ent-ollama ollama list
docker exec ent-ollama curl http://localhost:11434/api/tags

# Statistiques RabbitMQ
docker exec ent-rabbitmq rabbitmq-diagnostics -q all
```

## 12.5 Rollback

```bash
# Revenir à une version précédente
docker compose pull
docker compose up -d

# Stopper un service
docker compose stop ms-ai-assistant

# Redémarrer un service
docker compose restart ms-ai-assistant
```

---

# Annexe A: Structure Repository

```
ent-est-sale-platform/
├── services/
│   ├── ms-auth-core/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── README.md
│   │   └── app/
│   │       ├── __init__.py
│   │       ├── main.py
│   │       └── runtime.py
│   ├── ms-identity-admin/
│   ├── ms-course-content/
│   ├── ms-course-access/
│   ├── ms-notification/
│   ├── ms-calendar-schedule/
│   ├── ms-forum-chat/
│   ├── ms-exam-assignment/
│   └── ms-ai-assistant/
├── gateway/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── README.md
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       └── runtime.py
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── components/
│       ├── context/
│       ├── lib/
│       └── pages/
├── infra/
│   ├── compose/
│   │   ├── cassandra/
│   │   ├── keycloak/
│   │   ├── minio/
│   │   ├── prometheus/
│   │   └── grafana/
│   ├── manifests/
│   │   ├── k8s/
│   │   └── namespaces.yaml
│   └── README.md
├── docs/
│   ├── README-compose.md
│   ├── plan-ms-ai-assistant.md
│   └── sprint-0-close-checklist.md
├── docker-compose.yml
├── kind-config.yaml
├── README.md
├── README-k8.md
└── .github/
    └── workflows/
        ├── app-ci.yml
        └── infra-ci.yml
```

---

# Annexe B: Flux Bout-en-Bout

## Flux 1: Création d'un cours (Teacher)

```
1. Teacher login → JWT issued
2. Teacher → Frontend → Create Course form
3. Frontend → Gateway → POST /api/content/courses
4. Gateway → MS-Course-Content → Validate JWT
5. MS-Course-Content → Cassandra → Insert course
6. MS-Course-Content → MinIO → Create bucket if needed
7. MS-Course-Content → RabbitMQ → Publish course.created.v1
8. RabbitMQ → MS-Notification → Consume event
9. MS-Notification → Store notification + Send email
10. Response returned to teacher
```

## Flux 2: Téléchargement d'un cours (Student)

```
1. Student login → JWT issued
2. Student → Frontend → Course Catalog
3. Frontend → Gateway → GET /api/access/courses
4. Gateway → MS-Course-Access → Validate JWT (student role)
5. MS-Course-Access → MS-Course-Content (internal) → Fetch courses
6. MS-Course-Access → Gateway → Return course list
7. Student selects course → Request download link
8. Frontend → Gateway → POST /api/access/courses/{id}/download-links
9. Gateway → MS-Course-Access → Generate presigned URL
10. MS-Course-Access → MinIO → Generate presigned URL (TTL 180s)
11. Gateway → Frontend → Return presigned URL
12. Student → MinIO direct → Download file
```

## Flux 3: Soumission d'un devoir (Student)

```
1. Student → Frontend → View Assignment
2. Frontend → Gateway → GET /api/assignments/{id}
3. Student uploads file + text → Submit
4. Frontend → Gateway → POST /api/assignments/{id}/submissions
5. Gateway → MS-Exam-Assignment → Validate JWT
6. MS-Exam-Assignment → MinIO → Upload file
7. MS-Exam-Assignment → Cassandra → Insert submission
8. MS-Exam-Assignment → RabbitMQ → Publish assignment.submitted.v1
9. RabbitMQ → MS-Notification → Notify teacher
10. Response → Student (submission confirmation)
```

## Flux 4: Chat avec l'Assistant IA

```
1. User → Frontend → AI Assistant page
2. User types question → Send
3. Frontend → Gateway → POST /api/ai/chat
4. Gateway → MS-Auth-Core → Validate JWT
5. Gateway → MS-AI-Assistant → Forward request
6. MS-AI-Assistant → RabbitMQ → Check context store
7. MS-AI-Assistant → Ollama → Generate response (Llama 3)
8. Ollama → MS-AI-Assistant → Return response
9. MS-AI-Assistant → Log (audit + PII redaction)
10. Response → Frontend → Display chat bubble
```

---

# Annexe C: Glossaire

| Terme | Définition |
|-------|------------|
| ENT | Espace Numérique de Travail - Portail numérique éducatif |
| EST Salé | École Supérieure de Technologie de Salé, Maroc |
| Microservices | Architecture logicielle décomposant l'application en services indépendants |
| RBAC | Role-Based Access Control - Contrôle d'accès basé sur les rôles |
| JWT | JSON Web Token - Standard pour l'authentification stateless |
| JWKS | JSON Web Key Set - Ensemble de clés publiques pour valider JWT |
| OIDC | OpenID Connect - Protocole d'authentification basé sur OAuth 2.0 |
| Cassandra | Base de données NoSQL distribuée, optimisée pour写入 |
| MinIO | Stockage objet compatible S3, auto-hébergé |
| RabbitMQ | Message broker implémentant AMQP |
| AMQP | Advanced Message Queuing Protocol |
| Topic Exchange | Type d'exchange RabbitMQ routant par pattern de routing key |
| Presigned URL | URL temporaire avec signature pour accès sécurisé à MinIO |
| PKCE | Proof Key for Code Exchange - Extension OAuth 2.0 pour sécurité |
| Ollama | Runtime local pour modèles LLM (Llama, Mistral, etc.) |
| LLM | Large Language Model - Modèle de langage volumineux |
| Prompt Injection | Attaque tentant de modifier le comportement d'un LLM |
| shadcn/ui | Bibliothèque de composants React accessibles et personnalisables |

---

*Document généré le 24 avril 2026*
*Projet ENT EST Salé - Architecture Microservices*
*Version 1.0.0*