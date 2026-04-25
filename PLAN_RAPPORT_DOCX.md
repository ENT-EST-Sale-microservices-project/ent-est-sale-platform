# PLAN COMPLET — RAPPORT WORD (.docx) — ENT EST Salé

> **Consigne à Claude Design :** Génère un fichier Word `.docx` professionnel, moderne et complet en **français** à partir de ce plan. Utilise `python-docx`. Chaque section doit être incluse sans omission. Design sobre et élégant : palette bleu marine (#0F294D) + bleu accent (#1A56DB) + vert (#059669) + blanc. Police principale : Calibri 11pt. Marges : 2.5cm haut/bas, 2.8cm gauche, 2.5cm droite. Tableaux avec en-têtes colorés et lignes alternées. Page de couverture stylisée sans contenu de corps. Table des matières manuelle. Sauvegarder sous `Rapport_ENT_EST_Sale_FINAL.docx`.

---

## INFORMATIONS GÉNÉRALES DU PROJET

- **Nom complet** : ENT-EST-Salé — Espace Numérique de Travail
- **Établissement** : École Supérieure de Technologie de Salé (EST Salé)
- **Université** : Université Mohammed V, Rabat
- **Filière** : Ingénierie des Applications Web et Mobile
- **Module** : DevOps et Cloud
- **Groupe** : 5 étudiants + encadrant
- **Année universitaire** : 2025–2026
- **Date** : Avril 2026

---

## STRUCTURE DU DOCUMENT (15 sections)

### PAGE DE COUVERTURE
- Logo/titre stylisé centré avec fond bleu marine
- Titre : **ENT-EST-Salé** (grand, blanc sur fond bleu)
- Sous-titre : **Plateforme Numérique de Travail — Architecture Microservices**
- Tableau : Université, École, Filière, Module, Année
- Tableau : 5 membres du groupe (laisser les noms vides avec placeholder "Prénom NOM")
- Encadrant : placeholder
- Date : Avril 2026

### TABLE DES MATIÈRES
Manuelle, 15 entrées avec numéro de page indicatif.

---

## SECTION 1 — RÉSUMÉ EXÉCUTIF

Paragraphes suivants (écrire chaque paragraphe en plein) :

**Paragraphe 1 :**
Le projet ENT-EST-Salé est une plateforme numérique de travail académique complète développée dans le cadre du module DevOps et Cloud à l'École Supérieure de Technologie de Salé (Université Mohammed V, Rabat). Il s'agit d'un Espace Numérique de Travail (ENT) destiné à couvrir l'ensemble des besoins numériques d'un établissement d'enseignement supérieur : gestion des cours et contenus pédagogiques, organisation des examens et devoirs, communication via forum et chat en temps réel, planification via un calendrier académique partagé, et notifications automatiques.

**Paragraphe 2 :**
Sur le plan technique, la plateforme est construite selon une architecture microservices avec dix services Python FastAPI indépendants, orchestrés par Docker Compose et exposés via un API Gateway unifié sécurisé par JWT. L'identité et l'autorisation sont gérées par Keycloak (OpenID Connect), la persistance par Apache Cassandra, la messagerie asynchrone par RabbitMQ, le stockage d'objets par MinIO, et le cache par Redis. L'interface utilisateur est une Single Page Application React 18 + TypeScript avec le design system shadcn/ui. La stack d'observabilité complète repose sur Prometheus + Grafana.

**Points clés :**
- 10 microservices Python FastAPI pleinement opérationnels
- 9 composants d'infrastructure conteneurisés
- Interface React 18 avec 11 pages rôle-adaptatives
- Authentification OAuth2/OIDC avec RBAC 3 rôles
- Chat WebSocket temps-réel
- 8 scripts de smoke-test couvrant tous les flux fonctionnels
- Déploiement one-command via Docker Compose

---

## SECTION 2 — CONTEXTE ET OBJECTIFS

### 2.1 Contexte Académique
Expliquer : projet de fin de module DevOps et Cloud. Groupe de 5 étudiants de la filière Ingénierie des Applications Web et Mobile à l'EST Salé. Objectif pédagogique : mettre en pratique les compétences en conteneurisation, architecture distribuée, CI/CD, sécurité cloud et observabilité en réalisant une application réelle à forte valeur ajoutée.

### 2.2 Problématique
Les établissements d'enseignement supérieur manquent souvent d'une plateforme numérique unifiée. Les solutions existantes sont soit trop génériques, soit non adaptées au contexte marocain. L'ENT-EST-Salé répond à ce besoin en proposant une plateforme moderne, sécurisée et scalable, spécifiquement conçue pour l'EST Salé, qui regroupe :
- Gestion centralisée des cours et contenus pédagogiques
- Système de devoirs et d'examens avec soumission en ligne
- Forum académique et chat en temps réel par module
- Calendrier académique partagé
- Système de notifications automatiques par email et in-app

### 2.3 Objectifs Techniques
**Liste numérotée :**
1. Concevoir et implémenter une architecture microservices découplée et maintenable
2. Sécuriser l'accès via OAuth2/OIDC avec Keycloak et RBAC à 3 rôles (admin, teacher, student)
3. Assurer la persistance des données avec Apache Cassandra (base NoSQL distribuée)
4. Gérer le stockage de fichiers avec MinIO (S3-compatible)
5. Implémenter la messagerie asynchrone avec RabbitMQ (pattern event-driven)
6. Développer une interface utilisateur React 18 moderne et accessible
7. Implémenter le chat temps-réel via WebSocket (ms-forum-chat)
8. Déployer l'ensemble via Docker Compose avec healthchecks et dépendances déclaratives
9. Instrumenter tous les services avec Prometheus et visualiser via Grafana
10. Écrire des scripts de smoke-test couvrant tous les flux fonctionnels end-to-end

---

## SECTION 3 — ARCHITECTURE GÉNÉRALE

### 3.1 Vue d'ensemble — Architecture en Couches

**Texte d'introduction :**
La plateforme adopte une architecture microservices à quatre couches distinctes, chacune jouant un rôle précis. Tous les composants sont conteneurisés via Docker et interconnectés dans le réseau interne Docker `ent-network` (bridge).

**TABLEAU des 4 couches (3 colonnes : Couche | Composants | Rôle) :**

| Couche | Composants | Rôle |
|--------|-----------|------|
| Présentation | React 18 + TypeScript + Vite, Tailwind CSS + shadcn/ui, React Router v6, WebSocket natif | Interface utilisateur SPA, navigation par rôle, chat temps-réel |
| API / Gateway | ms-api-gateway (port 8008) | Point d'entrée unique, validation JWT, CORS, proxy vers microservices |
| Microservices | 9 services Python FastAPI (ports 8010–8018) | Logique métier isolée par domaine fonctionnel |
| Infrastructure | Keycloak, Cassandra, RabbitMQ, MinIO, Redis, Mailpit, PostgreSQL, Prometheus, Grafana | Identité, persistance, messagerie, stockage, observabilité |

### 3.2 Schéma d'Architecture ASCII (à reproduire dans le document)

```
┌─────────────────────────────────────────────────────────────────┐
│                    NAVIGATEUR (React SPA)                       │
│         HTTP/REST ──────────────── WebSocket                    │
└──────────────┬──────────────────────────────┬──────────────────┘
               │ HTTP :8008                   │ WS :8016
               ▼                              ▼
┌─────────────────────────┐     ┌─────────────────────────────┐
│    MS-API-GATEWAY       │     │    MS-FORUM-CHAT (WS)       │
│    FastAPI + JWT Guard   │     │    ConnectionManager        │
│    CORS + Retry          │     │    Rooms par module_code    │
└──────────────┬──────────┘     └─────────────────────────────┘
               │ validates via
               ▼
┌─────────────────────────┐
│    MS-AUTH-CORE          │◄── JWKS ── Keycloak :8080
│    PyJWT + PyJWKClient   │
└──────────────┬──────────┘
               │ proxifie vers
    ┌──────────┼─────────────────────────────────────────┐
    ▼          ▼          ▼          ▼          ▼         ▼
  identity  course    course    notif.   calendar  exam    ai
  -admin    -content  -access            -sched.   -assign asst.
  :8013     :8011     :8012     :8014    :8015     :8017  :8018
    │          │                  ▲          │        │
    │          │    ┌─────────────┘          │        │
    ▼          ▼    │                        ▼        ▼
┌────────────────────────────────────────────────────────────────┐
│                    RABBITMQ (Exchange: ent.events.topic)        │
│  user.*  course.*  asset.*  calendar.*  forum.*  assignment.*   │
│  grade.*                                                        │
└────────────────────────────────────────────────────────────────┘
    │          │                   │
    ▼          ▼                   ▼
┌────────┐  ┌──────┐         ┌──────────┐  ┌───────┐  ┌───────┐
│Keycloak│  │Cassnd│         │  MinIO   │  │ Redis │  │Mailpit│
│ :8080  │  │:9042 │         │:9001/9002│  │ :6379 │  │:1025  │
└────────┘  └──────┘         └──────────┘  └───────┘  └───────┘
                   │
         ┌─────────┴──────────┐
         ▼                    ▼
    ┌──────────┐        ┌──────────┐
    │Prometheus│        │ Grafana  │
    │  :9090   │──────► │  :3001   │
    └──────────┘        └──────────┘
```

### 3.3 Patterns de Communication

**Communication Synchrone (REST/HTTP) :**
Le frontend appelle le gateway → le gateway valide le JWT auprès de ms-auth-core (GET /auth/me) → si autorisé, le gateway proxifie la requête vers le microservice cible avec le header `Authorization: Bearer <JWT>` préservé → le microservice retourne la réponse → le gateway la propage au client.

**Communication Asynchrone (AMQP) :**
Les microservices publient des événements sur l'exchange RabbitMQ `ent.events.topic` (type topic, durable). ms-notification consomme tous les événements (patterns : `user.*`, `course.*`, `asset.*`, `assignment.*`, `grade.*`, `forum.*`, `calendar.*`) via la queue durable `q.notification.user`. ms-ai-assistant consomme `course.*` et `assignment.*` via la queue `q.ai.context` pour construire son contexte.

**Communication Inter-Services (interne) :**
ms-course-access appelle ms-course-content via le token interne `INTERNAL_API_TOKEN` (header `x-internal-token`) pour accéder aux endpoints `/internal/courses` et `/internal/courses/{id}` sans JWT utilisateur.

### 3.4 Enveloppe Standard d'Événement RabbitMQ

Tous les événements publiés suivent ce format standardisé (JSON, UTF-8) :

```json
{
  "event_id":       "uuid4 généré par le producteur",
  "event_type":     "domain.action.v1  (ex: course.created.v1)",
  "occurred_at":    "ISO-8601 UTC  (ex: 2026-04-24T10:00:00+00:00)",
  "producer":       "nom du microservice  (ex: ms-course-content)",
  "correlation_id": "x-request-id de la requête HTTP déclenchante",
  "payload":        { "données métier spécifiques à l'événement" }
}
```

La clé de routage = les 2 premiers segments du `event_type` (ex: `course.created` pour `course.created.v1`).

**TABLEAU — Catalogue complet des événements (4 colonnes : Producteur | Type | Routing Key | Payload principal) :**

| Producteur | Type d'Événement | Routing Key | Payload |
|-----------|-----------------|-------------|---------|
| ms-identity-admin | user.created.v1 | user.created | user_id, username, email, role, status |
| ms-identity-admin | user.role.assigned.v1 | user.role | user_id, role |
| ms-course-content | course.created.v1 | course.created | course_id, teacher_id, title, module_code |
| ms-course-content | course.updated.v1 | course.updated | course_id, title, module_code |
| ms-course-content | course.deleted.v1 | course.deleted | course_id, title, teacher_id |
| ms-course-content | asset.uploaded.v1 | asset.uploaded | course_id, asset_id, filename, size_bytes |
| ms-course-content | asset.deleted.v1 | asset.deleted | course_id, asset_id |
| ms-calendar-schedule | calendar.event.created.v1 | calendar.event | event_id, title, event_type, start_time, module_code, created_by |
| ms-forum-chat | forum.thread.created.v1 | forum.thread | thread_id, title, module_code, author_id |
| ms-forum-chat | forum.message.posted.v1 | forum.message | message_id, thread_id, author_id |
| ms-exam-assignment | assignment.published.v1 | assignment.published | assignment_id, title, module_code, due_date, created_by |
| ms-exam-assignment | assignment.submitted.v1 | assignment.submitted | submission_id, assignment_id, student_id |
| ms-exam-assignment | grade.published.v1 | grade.published | submission_id, assignment_id, student_id, grade, max_grade |

---

## SECTION 4 — INFRASTRUCTURE TECHNIQUE

### 4.1 Vue d'Ensemble des Composants

**Texte d'intro :** L'infrastructure est entièrement définie dans un fichier `docker-compose.yml` unique de 766 lignes. Elle comprend 25+ services Docker avec healthchecks, dépendances conditionnelles et volumes persistants. Les variables d'environnement sont centralisées dans `.env.compose`.

**GRAND TABLEAU infrastructure (5 colonnes : Composant | Image Docker | Port(s) Exposé(s) | Volume Persistant | Rôle Détaillé) :**

| Composant | Image Docker | Ports | Volume | Rôle |
|-----------|-------------|-------|--------|------|
| PostgreSQL 16 | postgres:16 | 5432 | keycloak_postgres_data | Backend relationnel exclusif de Keycloak (stockage IAM) |
| Keycloak 26.1.4 | quay.io/keycloak/keycloak:26.1.4 | 8080, 9000 | — | Serveur IAM OpenID Connect. Realm ent-est, 3 rôles, 2 clients OIDC |
| keycloak-realm-bootstrap | curlimages/curl:8.7.1 | — | — | Bootstrap automatique du realm ent-est via bootstrap-realm.sh |
| keycloak-users-bootstrap | curlimages/curl:8.7.1 | — | — | Création des 3 utilisateurs de dev (admin1, teacher1, student1) |
| Apache Cassandra 5.0 | cassandra:5.0 | 9042 | cassandra_data | Base NoSQL large-colonne. Keyspace ent_est, 11 tables applicatives |
| cassandra-init | cassandra:5.0 | — | — | Script init-cassandra.sh : création du keyspace ent_est |
| RabbitMQ 4.1.3 | rabbitmq:4.1.3-management | 5672, 15672 | rabbitmq_data | Broker AMQP. Exchange topic ent.events.topic. UI management sur 15672 |
| MinIO (latest) | quay.io/minio/minio:latest | 9001, 9002 | minio_data | Stockage objet S3-compatible. Console :9001, API :9002 |
| minio-init | quay.io/minio/mc:latest | — | — | Création des 3 buckets : ent-courses, ent-uploads, ent-logs |
| Redis 7-alpine | redis:7-alpine | 6379 | redis_data | Cache distribué, sessions. Auth par mot de passe |
| Mailpit v1.18 | axllent/mailpit:v1.18 | 1025, 8025 | — | SMTP sandbox. Capture emails sans envoi réel. UI sur 8025 |
| Ollama (latest) | ollama/ollama:latest | 11434 | ollama_data | Runtime LLM local. Profil Docker ai. GPU Nvidia optionnel |
| Prometheus | prom/prometheus:latest | 9090 | — | Collecte métriques /metrics, scrape_interval 15s, 9 services |
| Grafana | grafana/grafana:latest | 3001 | grafana_data | Dashboards. Datasource Prometheus auto-provisionnée |

### 4.2 Keycloak — Gestion des Identités (IAM)

**Realm ent-est :**
- **3 rôles realm** : `admin`, `teacher`, `student`
- **2 clients OIDC** :
  - `ent-gateway` : confidentiel (secret: ent-gateway-secret), service accounts, no directAccess
  - `ent-frontend` : public, StandardFlow activé, DirectAccessGrants activé, redirectUris: localhost:3000/*, localhost:5173/*
- **Utilisateurs de développement** :
  - admin1 / Admin_123! → rôle admin
  - teacher1 / Teacher_123! → rôle teacher
  - student1 / Student_123! → rôle student
- **Endpoint JWKS** : `http://keycloak:8080/realms/ent-est/protocol/openid-connect/certs`
- **Bootstrap** : scripts bootstrap-realm.sh et bootstrap-users.sh (curlimages/curl) exécutés comme `one-shot containers` au démarrage (restart: "no")

### 4.3 Apache Cassandra — Persistance NoSQL

**Keyspace :** `ent_est` — SimpleStrategy, replication_factor=1

**TABLEAU des 11 tables Cassandra (4 colonnes : Table | Service Propriétaire | Clé Primaire | Colonnes Principales) :**

| Table | Service | Clé Primaire | Colonnes Principales |
|-------|---------|-------------|---------------------|
| user_profiles | ms-identity-admin | user_id (PK) | username, email, full_name, role, status, created_at, updated_at |
| courses | ms-course-content | course_id (PK) | title, description, module_code, tags (list<text>), visibility, teacher_id, created_at, updated_at |
| course_assets | ms-course-content | (course_id, asset_id) | filename, content_type, size_bytes, minio_bucket, minio_object_key, created_at |
| notifications | ms-notification | (user_id, created_at DESC, notif_id) | event_type, title, body, correlation_id, read (boolean) |
| calendar_events | ms-calendar-schedule | event_id (PK) | title, description, event_type, start_time, end_time, module_code, target_group, created_by, created_at |
| forum_threads | ms-forum-chat | thread_id (PK) | title, body, author_id, author_name, module_code, created_at |
| forum_thread_counters | ms-forum-chat | thread_id (PK, COUNTER) | reply_count (counter) |
| forum_messages | ms-forum-chat | (thread_id, created_at ASC, message_id) | body, author_id, author_name |
| assignments | ms-exam-assignment | assignment_id (PK) | title, description, due_date, module_code, created_by, created_by_name, max_grade, status, created_at |
| submissions | ms-exam-assignment | submission_id (PK) | assignment_id, student_id, student_name, submitted_at, content_text, minio_object_key, grade, feedback, graded_at |
| submissions_by_assignment | ms-exam-assignment | (assignment_id, submitted_at DESC, submission_id) | (index pour lister les soumissions par devoir) |

**Pattern _ensure_db() :** Initialisation paresseuse au premier appel API. Crée le keyspace IF NOT EXISTS, puis les tables IF NOT EXISTS. PlainTextAuthProvider avec CASSANDRA_USERNAME + CASSANDRA_PASSWORD. RoundRobinPolicy pour le load-balancing. Les prepared statements sont initialisés une fois.

### 4.4 RabbitMQ — Messagerie Asynchrone

- **Exchange** : `ent.events.topic` (type TOPIC, durable=True)
- **Queue notification** : `q.notification.user` (durable), liée aux patterns : `user.*`, `course.*`, `asset.*`, `assignment.*`, `grade.*`, `forum.*`, `calendar.*`
- **Queue AI** : `q.ai.context` (durable), liée aux patterns : `course.*`, `assignment.*`
- **Message** : JSON UTF-8, delivery_mode PERSISTENT, content_type application/json
- **Bibliothèque** : `aio_pika` (async Python)
- **Connexion robuste** : `aio_pika.connect_robust()` (reconnexion automatique)
- **Consumer** : démarré via `asyncio.create_task()` dans `@app.on_event("startup")`

### 4.5 MinIO — Stockage Objet S3

- **Client** : `boto3` (compatibilité AWS S3)
- **3 buckets** : `ent-courses` (cours), `ent-uploads` (soumissions), `ent-logs`
- **Upload** : `s3.put_object(Bucket=..., Key=..., Body=..., ContentType=...)`
- **Download** : `generate_presigned_url("get_object", ..., ExpiresIn=180)` — TTL 180s
- **Object key pattern** :
  - Cours : `{course_id}/{asset_id}/{filename}`
  - Soumissions : `submissions/{assignment_id}/{student_id}/{filename}`
- **Deux clients boto3** : `s3_upload` (endpoint interne minio:9000) et `s3_sign` (endpoint externe localhost:9002 pour les presigned URLs accessibles depuis le navigateur)

### 4.6 Redis

Cache distribué sur le port 6379. Authentification par mot de passe (`requirepass`). Utilisé pour la gestion de sessions et le rate-limiting (à disposition des services).

---

## SECTION 5 — MICROSERVICES — DESCRIPTION DÉTAILLÉE

### 5.0 Structure Uniforme de Chaque Service

Chaque microservice respecte la structure de fichiers suivante (convention absolue) :
```
services/<nom-service>/
├── app/
│   ├── __init__.py
│   ├── runtime.py        ← copie IDENTIQUE sur tous les services
│   └── main.py           ← logique métier et endpoints
├── requirements.txt
└── Dockerfile            ← pattern slim Python
```

### 5.1 runtime.py — Module Transversal (identique sur tous les services)

Le module `runtime.py` est copié verbatim sur tous les services. Il configure via `setup_service_runtime(app, service_name)` :

**Métriques Prometheus :**
- `Counter` : `ent_http_requests_total` labels [service, method, path, status]
- `Histogram` : `ent_http_request_duration_seconds` labels [service, method, path] buckets (0.01, 0.05, 0.1, 0.2, 0.4, 0.8, 1.5, 3, 6)

**Middleware HTTP :**
- Génération/propagation du `x-request-id` (UUID4 ou repris du header entrant)
- Logging structuré JSON de chaque requête : event, service, request_id, method, path, status_code, duration_ms
- Mesure de la durée et incrémentation des compteurs Prometheus
- Propagation des headers `x-request-id` et `x-correlation-id` dans les réponses

**Gestionnaires d'exceptions :**
- `StarletteHTTPException` → JSON `{"error": {"code": "...", "message": "..."}, "request_id": "..."}`
- `RequestValidationError` → JSON `{"error": {"code": "VALIDATION_ERROR", "message": "...", "details": [...]}, "request_id": "..."}`
- `Exception` non capturée → JSON `{"error": {"code": "INTERNAL_ERROR", "message": "..."}, "request_id": "..."}`

**Endpoint observabilité :**
- `GET /metrics` → retourne `generate_latest()` avec `media_type=CONTENT_TYPE_LATEST`

**Fonction utilitaire :**
- `extract_request_id(request_obj)` → extrait `request.state.request_id`

### 5.2 ms-auth-core (Port 8010)

**Rôle :** Service de validation JWT. Seul service qui communique directement avec Keycloak pour récupérer les clés publiques JWKS.

**Dépendances :**
- `fastapi`, `uvicorn`, `PyJWT[crypto]` (PyJWKClient), `prometheus-client`

**Configuration (dataclass Settings) :**
- AUTH_REALM=ent-est
- AUTH_ISSUER=http://localhost:8080/realms/ent-est
- AUTH_JWKS_URL=http://keycloak:8080/realms/ent-est/protocol/openid-connect/certs
- AUTH_AUDIENCE=ent-gateway,ent-frontend
- AUTH_VERIFY_AUDIENCE=true

**Endpoints :**
- `GET /auth/health` → `{"status": "ok", "service": "ms-auth-core", "realm": "ent-est"}`
- `GET /auth/me` → Décode le JWT (Bearer), retourne : sub, preferred_username, email, realm_access, aud, iss, exp, iat
- `POST /auth/introspect` → Body: `{"token": "..."}`, retourne: `{"active": bool, "claims": {...} | null}`
- `GET /metrics` → Prometheus

**Logique de validation :**
1. `PyJWKClient(jwks_url)` récupère et met en cache les clés publiques
2. `jwt.decode(token, key=signing_key.key, algorithms=["RS256"], options={"verify_aud": False, "verify_iss": False})`
3. Vérification manuelle de l'audience : intersection `{aud, azp}` ∩ `{ent-gateway, ent-frontend}`
4. `ExpiredSignatureError` → 401 "Token expired"
5. `InvalidTokenError` → 401 "Invalid token"

### 5.3 ms-api-gateway (Port 8008)

**Rôle :** Point d'entrée unique de la plateforme. Valide les JWT, gère le CORS, et proxifie vers les services downstream.

**Dépendances :**
- `fastapi`, `uvicorn`, `httpx`, `prometheus-client`

**Configuration via env :**
- AUTH_CORE_BASE_URL, GATEWAY_TIMEOUT_SECONDS=8, GATEWAY_IDEMPOTENT_RETRIES=2
- URLs des 8 services downstream (COURSE_CONTENT, COURSE_ACCESS, IDENTITY_ADMIN, NOTIFICATION, CALENDAR, FORUM, EXAM, AI)
- CORS : localhost:5173, localhost:3000, localhost:4173

**Mécanisme JWT :**
```
verify_jwt_and_get_claims(authorization: Header)
  → GET {AUTH_CORE_BASE_URL}/auth/me avec Bearer token
  → 401 si absent, 401 si ms-auth-core retourne 401
  → 502 si ms-auth-core retourne autre erreur
  → retourne claims dict

require_roles(*roles)
  → FastAPI Depends sur verify_jwt_and_get_claims
  → vérifie intersection roles ∩ claims.realm_access.roles
  → 403 si vide
```

**Résilience :**
- GET uniquement : 2+1 tentatives avec backoff exponentiel (0.15s → 0.30s)
- POST/PUT/PATCH/DELETE : 1 tentative (non-idempotent)
- Timeout : 8s (configurable)
- 503 si service downstream inaccessible
- Propagation des erreurs (400/401/403/404/422/502) depuis les services

**TABLEAU COMPLET des routes (5 colonnes : Méthode | Chemin | Rôle Requis | Service Cible | Description) :**

| Méthode | Chemin | Rôle | Service | Description |
|---------|--------|------|---------|-------------|
| GET | /gateway/health | Public | — | Healthcheck gateway |
| GET | /api/me | Authentifié | auth-core | Claims JWT utilisateur courant |
| GET | /api/protected/ping | Authentifié | — | Test token valide |
| GET | /api/protected/admin | admin | — | Test rôle admin |
| GET | /api/protected/teacher | teacher | — | Test rôle teacher |
| GET | /api/protected/student | student | — | Test rôle student |
| GET | /api/protected/academic | teacher, admin | — | Test rôle académique |
| GET | /api/content/courses | teacher, admin | course-content | Liste les cours |
| POST | /api/content/courses | teacher, admin | course-content | Créer un cours |
| PUT | /api/content/courses/{id} | teacher, admin | course-content | Modifier un cours |
| DELETE | /api/content/courses/{id} | teacher, admin | course-content | Supprimer un cours |
| POST | /api/content/courses/{id}/assets | teacher, admin | course-content | Upload fichier (multipart) |
| DELETE | /api/content/courses/{id}/assets/{aid} | teacher, admin | course-content | Supprimer un asset |
| GET | /api/access/courses | student | course-access | Liste cours (vue étudiant) |
| GET | /api/access/courses/{id} | student | course-access | Détail cours |
| POST | /api/access/courses/{id}/download-links | student | course-access | Presigned URL download |
| POST | /api/admin/users | admin | identity-admin | Créer utilisateur |
| GET | /api/admin/users | admin | identity-admin | Lister utilisateurs |
| GET | /api/admin/users/{id} | admin | identity-admin | Détail utilisateur |
| PATCH | /api/admin/users/{id}/roles | admin | identity-admin | Modifier rôles |
| GET | /api/notifications | Authentifié | notification | Mes notifications (sub → user_id) |
| PATCH | /api/notifications/{id}/read | Authentifié | notification | Marquer une notif lue |
| PATCH | /api/notifications/read-all | Authentifié | notification | Tout marquer lu |
| GET | /api/stats | Authentifié | Plusieurs | Stats adaptées au rôle |
| POST | /api/calendar/events | teacher, admin | calendar | Créer événement |
| GET | /api/calendar/events | Authentifié | calendar | Lister (?month, ?module_code) |
| GET | /api/calendar/events/{id} | Authentifié | calendar | Détail événement |
| PATCH | /api/calendar/events/{id} | teacher, admin | calendar | Modifier événement |
| DELETE | /api/calendar/events/{id} | teacher, admin | calendar | Supprimer (204) |
| POST | /api/forum/threads | Authentifié | forum | Créer fil |
| GET | /api/forum/threads | Authentifié | forum | Lister fils (?module_code) |
| GET | /api/forum/threads/{id} | Authentifié | forum | Détail + messages |
| POST | /api/forum/threads/{id}/messages | Authentifié | forum | Poster message REST |
| POST | /api/assignments | teacher, admin | exam | Créer devoir |
| GET | /api/assignments | Authentifié | exam | Lister (?module_code, ?status) |
| GET | /api/assignments/{id} | Authentifié | exam | Détail devoir |
| POST | /api/assignments/{id}/submissions | student | exam | Soumettre (fichier ou texte) |
| GET | /api/assignments/{id}/submissions | Authentifié | exam | Lister soumissions |
| POST | /api/assignments/{id}/submissions/{sid}/grade | teacher, admin | exam | Noter |
| GET | /api/ai/health | Public | ai-assistant | Santé + état Ollama |
| POST | /api/ai/chat | Authentifié | ai-assistant | Chat avec LLM |
| POST | /api/ai/summarize | Authentifié | ai-assistant | Résumé de contenu |
| POST | /api/ai/faq/generate | Authentifié | ai-assistant | Génération de FAQ |

### 5.4 ms-identity-admin (Port 8013)

**Rôle :** Administration des utilisateurs. Opérations CRUD via l'API Admin Keycloak + profils miroirs dans Cassandra.

**Dépendances :** fastapi, uvicorn, httpx, aio_pika, cassandra-driver, pydantic[email], prometheus-client

**Modèles Pydantic :**
- `CreateUserRequest` : username (3–80), email (EmailStr), first_name (1–120), last_name (1–120), password (8–256), roles (list, défaut ["student"]), enabled (bool, défaut True)
- `PatchUserRolesRequest` : roles (list, min 1)
- `UserProfileResponse` : user_id, username, email, full_name, role, status, created_at, updated_at

**Flux de création utilisateur :**
1. Obtenir token admin Keycloak (`grant_type=password, client_id=admin-cli, realm=master`)
2. POST /admin/realms/ent-est/users (créer dans Keycloak)
3. Si 409 CONFLICT → HTTPException 409 "User already exists"
4. Extraire user_id depuis le header Location de la réponse
5. PUT .../users/{id}/reset-password (définir le mot de passe, temporary=False)
6. Pour chaque rôle : GET /admin/realms/ent-est/roles/{name} → POST .../role-mappings/realm
7. INSERT dans Cassandra table user_profiles
8. Publier user.created.v1 sur RabbitMQ

**Flux de modification des rôles :**
1. Obtenir token admin Keycloak
2. GET rôles actuels → DELETE tous
3. Assigner les nouveaux rôles
4. Mettre à jour profil Cassandra
5. Publier user.role.assigned.v1

**Endpoints :**
- `GET /identity-admin/health`
- `POST /admin/users` → require_admin → CreateUserRequest → UserProfileResponse (201)
- `PATCH /admin/users/{user_id}/roles` → require_admin → PatchUserRolesRequest → UserProfileResponse
- `GET /admin/users/{user_id}` → require_admin → UserProfileResponse
- `GET /admin/users` → require_admin → list[UserProfileResponse] (?search, ?limit=25)

### 5.5 ms-course-content (Port 8011)

**Rôle :** Gestion du catalogue de cours par les enseignants et administrateurs.

**Dépendances :** fastapi, uvicorn, httpx, aio_pika, cassandra-driver, boto3, pydantic, prometheus-client

**Modèles Pydantic :**
- `CreateCourseRequest` : title (3–200), description (3–4000), module_code (2–50), tags (list[str]), visibility (défaut "public_class")
- `UpdateCourseRequest` : idem CreateCourseRequest
- `CreateCourseResponse` : course_id, title, description, module_code, tags, visibility, teacher_id, created_at, updated_at
- `CourseWithAssetsResponse` : extends CreateCourseResponse + assets (list[dict])
- `UploadAssetResponse` : asset_id, course_id, filename, content_type, size_bytes, minio_bucket, minio_object_key

**Logique métier :**
- `list_courses` : filtre par teacher_id (si teacher) ou tout (si admin)
- `create_course` : uuid4 pour course_id, stocke teacher_id=claims.sub
- `upload_course_asset` : lecture fichier → s3.put_object → INSERT cassandra → UPDATE updated_at du cours
- `delete_course` : supprime tous les assets MinIO + Cassandra, puis le cours
- Object key pattern : `{course_id}/{asset_id}/{filename}`

**Endpoints :**
- `GET /courses-content/health`
- `GET /courses` → teacher/admin
- `POST /courses` → teacher/admin → 201
- `GET /courses/{id}` → teacher/admin
- `PUT /courses/{id}` → teacher/admin
- `DELETE /courses/{id}` → teacher/admin
- `POST /courses/{id}/assets` → teacher/admin, UploadFile → 201
- `DELETE /courses/{id}/assets/{aid}` → teacher/admin
- `GET /internal/courses` → x-internal-token (pour ms-course-access)
- `GET /internal/courses/{id}` → x-internal-token

### 5.6 ms-course-access (Port 8012)

**Rôle :** Accès en lecture seule aux cours pour les étudiants. Délègue à ms-course-content via token interne.

**Logique :**
- `list_courses` : GET /internal/courses → filtre champs (retire teacher_id, ajoute assets_count)
- `get_course` : GET /internal/courses/{id} → retourne cours avec assets
- `generate_download_link` : récupère le cours, trouve l'asset (par asset_id ou premier), génère presigned URL MinIO TTL=180s via `s3_signer` (endpoint externe localhost:9002 pour accessibilité navigateur)

**Endpoints :**
- `GET /courses-access/health`
- `GET /courses` → student uniquement
- `GET /courses/{id}` → student
- `POST /courses/{id}/download-links` → student → DownloadLinkResponse (download_url, expires_in_seconds=180)

### 5.7 ms-notification (Port 8014)

**Rôle :** Service dual-mode — consommateur RabbitMQ asynchrone + API REST pour lire les notifications.

**Table Cassandra `notifications` :** PRIMARY KEY (user_id, created_at DESC, notif_id). Permet de récupérer efficacement les notifications d'un utilisateur triées par date.

**Map événement → sujet email :**
- user.created.v1 → "Welcome to ENT EST Salé!"
- course.created.v1 → "New Course Available"
- course.updated.v1 → "Course Updated"
- course.deleted.v1 → "Course Removed"
- asset.uploaded.v1 → "New Course Material"
- user.role.assigned.v1 → "Role Updated"
- assignment.published.v1 → "New Assignment Published"
- assignment.submitted.v1 → "Assignment Submission Received"
- grade.published.v1 → "Your Assignment Has Been Graded"

**Consumer :**
- Patterns : `user.*`, `course.*`, `asset.*`, `assignment.*`, `grade.*`, `forum.*`, `calendar.*`
- Pour chaque message : extraire user_id du payload (logique variable selon le type d'événement), stocker dans Cassandra, envoyer email SMTP si email présent dans le payload
- Task asyncio démarrée au startup, annulée proprement au shutdown

**Endpoints :**
- `GET /notifications/health` → {consumer_enabled, smtp_enabled}
- `POST /notifications/test` → créer notification test
- `GET /notifications/{user_id}?limit=50` → list[dict]
- `PATCH /notifications/{user_id}/{notif_id}/read` → mark one read
- `PATCH /notifications/{user_id}/read-all` → mark all read, retourne count

### 5.8 ms-calendar-schedule (Port 8015)

**Rôle :** Gestion des événements du calendrier académique (cours, examens, deadlines, réunions).

**Modèles Pydantic :**
- `CreateEventRequest` : title (2–200), description (max 2000), event_type ("course"|"exam"|"deadline"|"other"), start_time (datetime), end_time (datetime), module_code (défaut "all"), target_group (défaut "all")
- `PatchEventRequest` : tous champs optionnels (PATCH partiel)
- `CalendarEventResponse` : event_id, title, description, event_type, start_time (ISO), end_time (ISO), module_code, target_group, created_by, created_at

**Contraintes :** end_time > start_time (validé côté service, 400 sinon)

**Filtrage :** `list_events` filtre en mémoire par `month` (YYYY-MM sur start_time.strftime) et `module_code`

**Endpoints :**
- `GET /calendar/health`
- `POST /calendar/events` → require_write (teacher/admin) → 201
- `GET /calendar/events` → require_auth (tous) → ?month=YYYY-MM, ?module_code
- `GET /calendar/events/{id}` → require_auth
- `PATCH /calendar/events/{id}` → require_write
- `DELETE /calendar/events/{id}` → require_write → 204

### 5.9 ms-forum-chat (Port 8016)

**Rôle :** Forum académique avec fils de discussion (REST) et chat temps-réel (WebSocket) par salle de module.

**ConnectionManager :** Gestionnaire in-memory de connexions WebSocket par salle (dict[str, list[WebSocket]]). Méthodes : connect(room, ws), disconnect(room, ws), broadcast(room, message).

**Tables Cassandra :**
- `forum_threads` : thread_id PK → title, body, author_id, author_name, module_code, created_at
- `forum_thread_counters` : thread_id PK → reply_count (COUNTER — table dédiée obligatoire en Cassandra)
- `forum_messages` : PRIMARY KEY (thread_id, created_at ASC, message_id) → corps du message, auteur

**Format message WebSocket :**
```json
{
  "type": "message",    // ou "system" pour join/leave
  "room": "DEV101",
  "text": "Bonjour à tous",
  "user_id": "uuid",
  "username": "teacher1"
}
```

**Authentification WebSocket :** Token JWT passé en query param `?token=<jwt>` → validé via GET /auth/me → si invalide, ws.close(code=4001)

**Endpoints REST :**
- `GET /forum/health`
- `POST /forum/threads` → require_auth → 201, publie forum.thread.created.v1
- `GET /forum/threads` → require_auth → ?module_code
- `GET /forum/threads/{id}` → require_auth → ThreadDetailResponse (avec messages)
- `POST /forum/threads/{id}/messages` → require_auth → 201, publie forum.message.posted.v1

**Endpoint WebSocket :**
- `WS /chat/ws?token=<jwt>&room=<module_code>` → direct sur le service (port 8016), pas via gateway

### 5.10 ms-exam-assignment (Port 8017)

**Rôle :** Gestion complète du cycle devoirs : création, soumission de fichiers, notation.

**Modèles Pydantic :**
- `CreateAssignmentRequest` : title (3–200), description (1–5000), due_date (datetime), module_code (1–50), max_grade (≥0, défaut 20.0), status ("draft"|"published")
- `GradeRequest` : grade (≥0), feedback (max 5000)
- `AssignmentResponse` : assignment_id, title, description, due_date, module_code, created_by, created_by_name, max_grade, status, created_at
- `SubmissionResponse` : submission_id, assignment_id, student_id, student_name, submitted_at, content_text, has_file (bool), download_url (presigned|None), grade (float|None), feedback (str|None), graded_at (str|None)

**Flux soumission :**
1. Vérifier que le devoir existe et est "published"
2. Vérifier content_text ou fichier présent
3. Si fichier : lire → vérifier taille (max 50MB) → s3_upload.put_object(key=`submissions/{assignment_id}/{student_id}/{filename}`)
4. INSERT dans `submissions` + INSERT dans `submissions_by_assignment` (index)
5. Publier assignment.submitted.v1

**Flux notation :**
1. Vérifier devoir + soumission
2. Vérifier grade ≤ max_grade
3. UPDATE SET grade, feedback, graded_at
4. Publier grade.published.v1

**Visibilité soumissions :** teacher/admin voit toutes → student ne voit que les siennes (filtre sur student_id)

**Endpoints :**
- `GET /exams/health`
- `POST /assignments` → require_teacher → 201
- `GET /assignments` → require_auth → ?module_code, ?status (alias)
- `GET /assignments/{id}` → require_auth
- `POST /assignments/{id}/submissions` → require_student → Form(content_text) + File(optional) → 201
- `GET /assignments/{id}/submissions` → require_auth (filtre selon rôle)
- `POST /assignments/{id}/submissions/{sid}/grade` → require_teacher

### 5.11 ms-ai-assistant (Port 8018)

**Rôle :** Assistant IA utilisant Ollama (LLM Llama3 local) pour chat, résumé et génération de FAQ.

**Sécurité intégrée :**
- **Rate limiter** : `RateLimiter` in-memory, 20 req/min par user_id (sliding window 60s)
- **Anti-injection prompt** : 8 patterns regex (ignore previous instructions, forget everything, system prompt leak...) + liste noire (sudo, rm -rf, drop table, exec(, eval()...)
- **Redaction PII** : regex email, date, téléphone → `[EMAIL_REDACTED]`, `[DATE_REDACTED]`, `[PHONE_REDACTED]`

**Contexte par rôle :**
- admin : "administrator helping with system management"
- teacher : "teacher helping with course management"
- student : "student helper for course content and assignments"

**Consumer RabbitMQ :** `q.ai.context`, patterns `course.*`, `assignment.*`. Stocke les événements cours/devoirs dans `context_store` (dict en mémoire) pour enrichir les réponses.

**Ollama :** POST {OLLAMA_BASE_URL}/api/generate → {model: llama3, prompt, stream: false, options: {num_predict: 2048, temperature: 0.7}}

**Endpoints :**
- `GET /ai/health` → {status, service, model, ollama: {status, model}} (vérifie GET /api/tags sur Ollama)
- `POST /ai/chat` → ChatRequest{user_id, role, question, context_refs[]} → ChatResponse{answer, sources, model, tokens_used}
- `POST /ai/summarize` → SummarizeRequest{course_id, content, max_length=500} → SummarizeResponse{summary, key_points[]}
- `POST /ai/faq/generate` → FAQGenerateRequest{course_id, content, num_questions=5} → FAQGenerateResponse{faqs: [{q, a}]}

---

## SECTION 6 — INTERFACE UTILISATEUR (FRONTEND)

### 6.1 Stack Technique

**TABLEAU :**

| Technologie | Version | Rôle |
|-------------|---------|------|
| React | 19.2.4 | Bibliothèque UI, composants fonctionnels, hooks |
| TypeScript | ~6.0.2 | Typage statique |
| Vite | 8.0.4 | Build tool ultra-rapide, HMR en dev |
| Tailwind CSS | 4.2.2 | Utility-first CSS, responsive design |
| shadcn/ui | 4.3.0 | Composants UI accessibles (via @base-ui/react) |
| React Router | 7.14.1 | Navigation SPA, routes imbriquées |
| lucide-react | 1.8.0 | Icônes (Bell, BookOpenText, CalendarDays, etc.) |
| Geist Font | 5.2.8 | Police variable principale |
| nginx:alpine | — | Serveur de production (build multi-stage) |
| Node.js | 22-alpine | Build stage Docker |

### 6.2 Architecture Frontend

```
frontend/src/
├── main.tsx               ← Entry point, BrowserRouter, AuthProvider, ThemeProvider
├── App.tsx                ← Routes principale (React Router v6)
├── context/
│   ├── auth-context.tsx   ← AuthProvider, useAuth(), apiFetch(), JWT lifecycle
│   └── theme-context.tsx  ← ThemeProvider, dark/light mode
├── components/
│   ├── app-shell.tsx      ← Layout principal : sidebar + header + Outlet
│   ├── route-guards.tsx   ← ProtectedRoute, RoleRoute
│   └── ui/                ← Composants shadcn/ui
│       ├── alert.tsx, avatar.tsx, badge.tsx, button.tsx
│       ├── card.tsx, dialog.tsx, dropdown-menu.tsx
│       ├── input.tsx, label.tsx, select.tsx, separator.tsx
│       ├── skeleton.tsx, table.tsx, tabs.tsx, textarea.tsx
├── pages/
│   ├── login-page.tsx
│   ├── dashboard-page.tsx
│   ├── admin-page.tsx
│   ├── teacher-page.tsx
│   ├── student-page.tsx
│   ├── calendar-page.tsx
│   ├── forum-page.tsx
│   ├── exam-page.tsx
│   ├── assistant-page.tsx
│   ├── notifications-page.tsx
│   ├── profile-page.tsx
│   ├── role-landing-page.tsx
│   ├── unauthorized-page.tsx
│   └── not-found-page.tsx
├── lib/
│   ├── auth.ts            ← beginPkceLogin, completePkceLogin, directAccessGrant, decodeJwtClaims
│   └── utils.ts           ← cn() (clsx + tailwind-merge)
```

### 6.3 Système d'Authentification Frontend

**auth-context.tsx :**
- `AuthSession` : {accessToken, refreshToken, expiresAt}
- `JwtClaims` : {sub, preferred_username, email, realm_access: {roles[]}, aud, iss, exp, iat}
- Persistance : `localStorage` sous la clé `AUTH_SESSION_KEY`
- `apiFetch<T>(path, init?)` : ajoute automatiquement `Authorization: Bearer <token>`, rafraîchit si expiré
- `useEffect` de surveillance : rafraîchit le token automatiquement si expiré (via `refreshPkceSession`)
- `directAccessGrant` : appel direct Keycloak avec username/password (password flow)
- `beginPkceLogin / completePkceLogin` : flux Authorization Code avec PKCE

**auth.ts — lib :**
- `decodeJwtClaims(token)` : décode le payload JWT (atob sur la partie base64)
- `isSessionExpired(session)` : vérifie expiresAt - 60s
- `beginPkceLogin()` : génère code_verifier + code_challenge, redirige vers Keycloak
- `completePkceLogin(code, state)` : échange le code contre les tokens
- `directAccessGrant(username, password)` : POST /token avec password grant

**route-guards.tsx :**
- `ProtectedRoute` : si `!isAuthenticated` → `<Navigate to="/login" />` 
- `RoleRoute` : si `!hasAnyRole(allowedRoles)` → `<Navigate to="/unauthorized" />`

### 6.4 AppShell — Layout Principal

**Sidebar (256px ouverte / 72px réduite) :**
- Logo ENT EST Salé avec GraduationCap (Lucide)
- User Card : Avatar initiales, username, badges de rôles colorés
- Navigation : 9 items filtrés selon les rôles
- Badge de notifications non lues sur l'item "Notifications" (rafraîchi toutes les 60s)
- Bouton Sign Out
- Bouton toggle ouvert/réduit (chevron)

**Header fixe :**
- Bouton menu mobile (lg:hidden)
- Titre de la page actuelle
- Toggle thème dark/light (Sun/Moon)
- Cloche notifications avec badge count
- Menu utilisateur dropdown : Profile, Notifications, Sign Out

**Navigation Items :**
| Route | Label | Icône | Rôles Visibles |
|-------|-------|-------|----------------|
| /app | Dashboard | LayoutDashboard | Tous |
| /app/assistant | AI Assistant | Sparkles | Tous |
| /app/admin | User Management | ShieldCheck | admin |
| /app/teacher | Course Studio | CloudUpload | teacher, admin |
| /app/student | Course Catalog | BookOpenText | student |
| /app/calendar | Calendar | CalendarDays | Tous |
| /app/forum | Forum | MessageSquare | Tous |
| /app/exams | Assignments | ClipboardList | teacher, admin, student |
| /app/notifications | Notifications | Bell | Tous |

### 6.5 Pages Détaillées

**TABLEAU complet des pages :**

| Page | Route | Rôles | Fonctionnalité | API Calls |
|------|-------|-------|---------------|-----------|
| LoginPage | /login | Public | Form username/password, directAccessGrant Keycloak, redirect /app | POST Keycloak /token |
| DashboardPage | /app | Tous | Stats temps-réel selon rôle, fil d'activité forum, raccourcis | GET /api/stats, GET /api/forum/threads |
| AdminPage | /app/admin | admin | Liste utilisateurs, formulaire création, modification rôles | GET/POST /api/admin/users, PATCH /api/admin/users/{id}/roles |
| TeacherPage | /app/teacher | teacher, admin | Gestion cours (CRUD), upload assets (multipart), liste devoirs | GET/POST/PUT/DELETE /api/content/courses, POST /api/content/courses/{id}/assets |
| StudentPage | /app/student | student | Catalogue cours, téléchargement assets, mes devoirs | GET /api/access/courses, POST /api/access/courses/{id}/download-links |
| CalendarPage | /app/calendar | Tous | Calendrier mensuel interactif, filtrage, modal création (teacher/admin) | GET /api/calendar/events, POST /api/calendar/events |
| ForumPage | /app/forum | Tous | Fils de discussion, chat WebSocket temps-réel par module, création threads | GET /api/forum/threads, POST /api/forum/threads, WS ws://localhost:8016/chat/ws |
| ExamPage | /app/exams | Tous | Devoirs publiés, soumission fichier/texte (student), liste soumissions + notes (teacher) | GET/POST /api/assignments, POST /api/assignments/{id}/submissions, POST .../grade |
| AssistantPage | /app/assistant | Tous | Interface chat IA, résumé de contenu, génération FAQ | POST /api/ai/chat, POST /api/ai/summarize, POST /api/ai/faq/generate |
| NotificationsPage | /app/notifications | Tous | Centre de notifications, marquage lu/tout lu, filtre non lus | GET /api/notifications, PATCH /api/notifications/{id}/read, PATCH /api/notifications/read-all |
| ProfilePage | /app/profile | Tous | Informations profil, rôles, déconnexion | GET /api/me |

### 6.6 Dockerfile Frontend (Multi-Stage Build)

```dockerfile
# Stage 1 : Build
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build        # TypeScript + Vite → /app/dist

# Stage 2 : Production
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 6.7 nginx.conf — Configuration Proxy

```nginx
server {
    listen 80;
    location / {
        try_files $uri $uri/ /index.html;    # SPA fallback
    }
    location /api/ {
        proxy_pass http://ms-api-gateway:8000/api/;   # Proxy vers Gateway
        client_max_body_size 100M;
    }
    location /realms/ {
        proxy_pass http://keycloak:8080/realms/;       # Proxy OIDC
    }
}
```

---

## SECTION 7 — SÉCURITÉ ET AUTHENTIFICATION

### 7.1 Modèle de Sécurité Global

La sécurité de la plateforme repose sur le standard industriel OAuth2/OpenID Connect avec Keycloak comme Authorization Server. Les JWT sont signés avec l'algorithme RS256 (clé asymétrique RSA). Aucun secret partagé entre les microservices.

### 7.2 Flux d'Authentification Complet

**DIAGRAMME (textuel à reproduire) :**
```
Utilisateur → LoginPage → directAccessGrant → Keycloak POST /token
                                                    ↓
                                         access_token (JWT RS256)
                                         + refresh_token
                                                    ↓
                          localStorage → auth-context.tsx
                                         session = {accessToken, refreshToken, expiresAt}
                                                    ↓
                          apiFetch() → GET /api/resource
                                   Authorization: Bearer <JWT>
                                                    ↓
                                        ms-api-gateway
                                        verify_jwt_and_get_claims()
                                                    ↓
                                        GET /auth/me → ms-auth-core
                                        PyJWKClient → JWKS → RS256 verify
                                                    ↓
                                        claims = {sub, username, realm_access.roles}
                                                    ↓
                                        require_roles() → check intersection
                                        403 si rôle insuffisant
                                        ↓ si autorisé
                                        proxy → microservice cible
```

### 7.3 RBAC — Contrôle d'Accès Basé sur les Rôles

**TABLEAU complet (3 colonnes : Rôle | Permissions | Restrictions) :**

| Rôle | Permissions | Restrictions |
|------|-------------|-------------|
| **admin** | Créer/modifier/supprimer utilisateurs et rôles (Keycloak + Cassandra). CRUD complet sur tous les cours, assets, devoirs. Gestion calendrier. Accès à toutes les pages. Voir toutes les soumissions et notes. | — |
| **teacher** | CRUD complet sur ses propres cours (admin voit tout). Upload assets MinIO. Créer/modifier/supprimer devoirs. Voir et noter toutes les soumissions. Créer/modifier/supprimer événements calendrier. Accès forum. | Pas d'accès User Management. Pas de création d'utilisateurs. |
| **student** | Lecture seule des cours (via ms-course-access, pas de teacher_id). Génération presigned URLs pour download. Soumettre des devoirs (fichier ≤50MB ou texte). Voir ses propres soumissions et notes. Lire calendrier. Accès forum. | Pas d'accès aux routes teacher/admin. Ne voit que ses propres soumissions. |

### 7.4 Sécurité des Communications

**Réseau Docker :** Tous les services communiquent via le réseau interne Docker `ent-network` (bridge). Seuls les ports mappés dans docker-compose.yml sont accessibles depuis l'hôte.

**Token interne :** `INTERNAL_API_TOKEN` (header `x-internal-token`) utilisé par ms-course-access pour appeler les endpoints `/internal/courses` de ms-course-content sans JWT utilisateur.

**CORS :** Configurable via `GATEWAY_CORS_ORIGINS`. En développement : `http://localhost:5173,http://localhost:3000,http://localhost:4173`.

**Autres mesures :**
- Mots de passe hashés par Keycloak (bcrypt)
- Variables sensibles dans `.env.compose` (hors versionning git)
- Retry avec backoff exponentiel (pas d'amplification DDoS)
- Rate limiting IA : 20 req/min par utilisateur
- Anti-injection prompt dans ms-ai-assistant (8 patterns regex)
- Validation stricte Pydantic sur toutes les entrées
- Timeouts configurables sur toutes les connexions HTTP

---

## SECTION 8 — OBSERVABILITÉ (PROMETHEUS & GRAFANA)

### 8.1 Instrumentation des Services (runtime.py)

**Chaque service** expose automatiquement via runtime.py :
- `ent_http_requests_total` (Counter) → labels: service, method, path, status
- `ent_http_request_duration_seconds` (Histogram) → labels: service, method, path → buckets: 0.01s, 0.05s, 0.1s, 0.2s, 0.4s, 0.8s, 1.5s, 3s, 6s
- Endpoint `GET /metrics` → format text Prometheus (CONTENT_TYPE_LATEST)

### 8.2 Configuration Prometheus

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: ms-auth-core
    static_configs: [{targets: ['ms-auth-core:8000']}]
  - job_name: ms-api-gateway
    static_configs: [{targets: ['ms-api-gateway:8000']}]
  - job_name: ms-identity-admin
    static_configs: [{targets: ['ms-identity-admin:8000']}]
  - job_name: ms-course-content
    static_configs: [{targets: ['ms-course-content:8000']}]
  - job_name: ms-course-access
    static_configs: [{targets: ['ms-course-access:8000']}]
  - job_name: ms-notification
    static_configs: [{targets: ['ms-notification:8000']}]
  - job_name: ms-calendar-schedule
    static_configs: [{targets: ['ms-calendar-schedule:8000']}]
  - job_name: ms-forum-chat
    static_configs: [{targets: ['ms-forum-chat:8000']}]
  - job_name: ms-exam-assignment
    static_configs: [{targets: ['ms-exam-assignment:8000']}]
```

### 8.3 Grafana

- **Port** : 3001 (map depuis 3000 interne)
- **Admin** : GF_SECURITY_ADMIN_USER=admin / GF_SECURITY_ADMIN_PASSWORD (via env)
- **Datasource** : Auto-provisionnée depuis `infra/compose/grafana/provisioning/datasources/datasource.yml` → Prometheus URL interne
- **Dashboard** : Auto-provisionné `ENT Platform` depuis `infra/compose/grafana/provisioning/dashboards/ent-platform.json`
- **Provider config** : `dashboard.yml` avec allowUiUpdates=false

### 8.4 Métriques Clés à Surveiller

**TABLEAU :**

| Métrique PromQL | Description | Seuil d'Alerte |
|----------------|-------------|----------------|
| `rate(ent_http_requests_total[5m])` | Taux de requêtes par service | — |
| `rate(ent_http_requests_total{status=~"5.."}[5m])` | Taux d'erreurs 5xx | > 1% |
| `histogram_quantile(0.99, ent_http_request_duration_seconds_bucket)` | Latence p99 | > 3s |
| `rate(ent_http_requests_total{status="401"}[5m])` | Tentatives non authentifiées | > 10/min |
| `rate(ent_http_requests_total{status="403"}[5m])` | Tentatives non autorisées | > 5/min |

---

## SECTION 9 — DÉPLOIEMENT ET DOCKER COMPOSE

### 9.1 Structure Docker Compose

**Fichier :** `docker-compose.yml` (766 lignes)

**Shared config :**
```yaml
x-common: &common
  restart: unless-stopped
  networks: [ent-network]
```

**Réseau :** `ent-network` (bridge, nommé)

**Volumes nommés :** keycloak_postgres_data, cassandra_data, rabbitmq_data, minio_data, redis_data, grafana_data, ollama_data

### 9.2 Ordre de Démarrage et Healthchecks

**TABLEAU des dépendances :**

| Service | Dépend de | Condition |
|---------|----------|----------|
| keycloak | postgres-keycloak | service_healthy |
| keycloak-realm-bootstrap | keycloak | service_started |
| keycloak-users-bootstrap | keycloak-realm-bootstrap | service_completed_successfully |
| cassandra-init | cassandra | service_healthy |
| minio-init | minio | service_started |
| ms-auth-core | keycloak, keycloak-realm-bootstrap, keycloak-users-bootstrap | service_completed_successfully |
| ms-identity-admin | ms-auth-core, cassandra, cassandra-init, keycloak-realm-bootstrap, keycloak-users-bootstrap | service_healthy / completed |
| ms-course-content | ms-auth-core, minio, minio-init, cassandra, cassandra-init | service_healthy / completed |
| ms-course-access | ms-auth-core, ms-course-content | service_healthy |
| ms-notification | rabbitmq, cassandra, cassandra-init, mailpit | service_healthy / completed / started |
| ms-calendar-schedule | ms-auth-core, cassandra, cassandra-init, rabbitmq | service_healthy |
| ms-forum-chat | ms-auth-core, cassandra, cassandra-init, rabbitmq | service_healthy |
| ms-exam-assignment | ms-auth-core, cassandra, cassandra-init, rabbitmq, minio, minio-init | service_healthy |
| ms-ai-assistant | ms-auth-core, rabbitmq | service_healthy |
| ms-api-gateway | tous les microservices | service_healthy |
| frontend | ms-api-gateway, keycloak | service_healthy / started |
| prometheus | — | — |
| grafana | prometheus | — |

### 9.3 Healthchecks

**Pattern Python :**
```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/<service>/health', timeout=3)"]
  interval: 10s
  timeout: 5s
  retries: 10
```

**Cassandra :** `cqlsh -u cassandra -p <pass> -e "SELECT release_version FROM system.local"` — start_period: 120s

**RabbitMQ :** `rabbitmq-diagnostics -q ping` — interval: 15s, retries: 10

### 9.4 Dockerfiles des Microservices

**Pattern Python slim :**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Dépendances communes à tous les services :**
- `fastapi>=0.111,<1.0`
- `uvicorn[standard]>=0.30,<1.0`
- `prometheus-client>=0.20,<1.0`

**Dépendances spécifiques par service :**

| Service | Deps supplémentaires |
|---------|---------------------|
| ms-auth-core | PyJWT[crypto]>=2.8 |
| ms-identity-admin | httpx, aio_pika, cassandra-driver, pydantic[email] |
| ms-course-content | httpx, aio_pika, cassandra-driver, boto3 |
| ms-course-access | httpx, boto3 |
| ms-notification | aio_pika, cassandra-driver, aiosmtplib |
| ms-calendar-schedule | httpx, aio_pika, cassandra-driver |
| ms-forum-chat | httpx, aio_pika, cassandra-driver, websockets |
| ms-exam-assignment | httpx, aio_pika, cassandra-driver, boto3, python-multipart |
| ms-ai-assistant | httpx, aio_pika |

### 9.5 Commandes de Déploiement

```bash
# Démarrage complet (build + détaché)
docker compose --env-file .env.compose up -d --build

# Vérifier l'état de tous les services
docker compose ps

# Logs en temps réel d'un service
docker compose logs -f ms-api-gateway

# Smoke tests de validation
bash scripts/compose-healthcheck.sh
bash scripts/rbac-smoke-test.sh
bash scripts/course-content-smoke-test.sh
bash scripts/exam-smoke-test.sh

# Arrêt propre
docker compose down

# Arrêt + suppression volumes (reset complet)
docker compose down -v
```

---

## SECTION 10 — TESTS ET VALIDATION

### 10.1 Scripts de Smoke-Test

**TABLEAU détaillé (4 colonnes : Script | Tests Réalisés | Services Testés | Tokens Utilisés) :**

| Script | Tests | Services | Tokens |
|--------|-------|----------|--------|
| compose-healthcheck.sh | Vérification que tous les conteneurs Docker sont healthy via `docker compose ps` | Tous | Aucun |
| rbac-smoke-test.sh | /api/protected/ping (tous), /api/protected/admin (admin seulement, 403 si teacher/student), /api/protected/teacher (teacher, 403 si student), /api/protected/student (student, 403 si teacher) | ms-api-gateway, ms-auth-core | admin1, teacher1, student1 |
| course-content-smoke-test.sh | CRUD cours (POST, GET, PUT, DELETE), upload asset multipart, suppression asset. Vérification 403 si student. | ms-course-content, ms-api-gateway | teacher1, student1 |
| course-access-smoke-test.sh | Listing cours, détail cours, génération presigned URL (GET/POST), 403 si teacher sur /api/access | ms-course-access, ms-course-content | student1, teacher1 |
| identity-admin-smoke-test.sh | Création utilisateur (POST /api/admin/users), get user, liste users, patch roles. 403 si teacher. | ms-identity-admin, ms-api-gateway | admin1, teacher1 |
| calendar-smoke-test.sh | Création événement, liste (tous types), filtrage ?month + ?module_code, modification (PATCH), suppression (DELETE 204). 403 student pour écriture. | ms-calendar-schedule, ms-api-gateway | teacher1, student1 |
| forum-smoke-test.sh | Création fil, liste fils, filtrage module_code, get détail, post message REST, test WebSocket (connexion + message). | ms-forum-chat, ms-api-gateway | teacher1, student1 |
| exam-smoke-test.sh | Création devoir, liste + filtrage, get devoir, 403 student sur création, soumission texte (multipart), vue teacher (toutes soumissions), vue student (les siennes), notation 17.5/20, vérification grade student, rejet grade > max_grade (400). | ms-exam-assignment, ms-api-gateway | teacher1, student1, admin1 |

### 10.2 Pattern des Smoke-Tests

```bash
# Obtenir un token JWT via Keycloak
get_token() {
  curl -sf -X POST "${KC}/realms/${REALM}/protocol/openid-connect/token" \
    -d "client_id=ent-frontend" \
    -d "grant_type=password" \
    -d "username=${user}" -d "password=${pass}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])"
}

# Vérifier un code HTTP attendu
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" ...)
[[ "$HTTP_CODE" == "403" ]] || fail "Expected 403, got $HTTP_CODE"
```

---

## SECTION 11 — PATTERNS ET CONVENTIONS

### 11.1 Convention de Nommage

- **Services** : `ms-<domaine>-<fonction>` (ex: ms-course-content)
- **Containers** : `ent-<nom-service>` (ex: ent-ms-course-content)
- **Events** : `<domaine>.<action>.v<version>` (ex: course.created.v1)
- **Tables Cassandra** : snake_case pluriel (ex: forum_threads)
- **Routes API** : `/api/<domaine>/<ressource>` (ex: /api/calendar/events)

### 11.2 Versionnement des Événements

Tous les types d'événements incluent un suffixe de version (`.v1`). La clé de routage RabbitMQ utilise les 2 premiers segments. Cette approche permet l'évolution indépendante des producteurs et consommateurs : un `course.created.v2` peut coexister avec `course.created.v1` sur le même exchange.

### 11.3 Logging Structuré JSON

```json
{
  "event": "request.completed",
  "service": "ms-api-gateway",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "POST",
  "path": "/api/calendar/events",
  "status_code": 201,
  "duration_ms": 47.23
}
```

### 11.4 Gestion des Erreurs Standardisée

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Forbidden. Required one of roles: teacher, admin"
  },
  "request_id": "550e8400-..."
}
```

Codes d'erreur : BAD_REQUEST, UNAUTHENTICATED, FORBIDDEN, NOT_FOUND, CONFLICT, VALIDATION_ERROR, RATE_LIMITED, INTERNAL_ERROR

---

## SECTION 12 — ARBORESCENCE COMPLÈTE DU PROJET

```
ent-est-sale-platform/
├── docker-compose.yml              ← Orchestration complète (766 lignes)
├── .env.compose                    ← Variables d'environnement réelles
├── .env.compose.example            ← Template env
├── .yamllint                       ← Linting YAML
├── kind-config.yaml                ← Config cluster Kind (K8s futur)
├── README.md
├── README-k8.md
│
├── frontend/                       ← SPA React 18 + TypeScript
│   ├── Dockerfile                  ← Multi-stage (node:22 → nginx:alpine)
│   ├── nginx.conf                  ← SPA fallback + proxy /api + /realms
│   ├── package.json                ← React 19, Vite 8, Tailwind 4, shadcn 4
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── components.json             ← Config shadcn/ui
│   └── src/
│       ├── main.tsx
│       ├── App.tsx                 ← Routes React Router v6
│       ├── context/
│       │   ├── auth-context.tsx    ← JWT lifecycle, apiFetch()
│       │   └── theme-context.tsx
│       ├── components/
│       │   ├── app-shell.tsx       ← Sidebar + Header + Outlet
│       │   ├── route-guards.tsx    ← ProtectedRoute, RoleRoute
│       │   └── ui/                 ← 14 composants shadcn/ui
│       ├── pages/                  ← 14 pages
│       └── lib/
│           ├── auth.ts             ← PKCE + directAccessGrant
│           └── utils.ts
│
├── gateway/                        ← ms-api-gateway
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py                 ← 996 lignes, toutes les routes
│       └── runtime.py
│
├── services/
│   ├── ms-auth-core/               ← Port 8010
│   ├── ms-identity-admin/          ← Port 8013
│   ├── ms-course-content/          ← Port 8011
│   ├── ms-course-access/           ← Port 8012
│   ├── ms-notification/            ← Port 8014
│   ├── ms-calendar-schedule/       ← Port 8015
│   ├── ms-forum-chat/              ← Port 8016
│   ├── ms-exam-assignment/         ← Port 8017
│   └── ms-ai-assistant/            ← Port 8018
│       (chacun : Dockerfile, requirements.txt, app/__init__.py, app/runtime.py, app/main.py)
│
├── infra/
│   ├── bootstrap/
│   │   └── bootstrap-infra.sh
│   ├── compose/
│   │   ├── cassandra/
│   │   │   └── init-cassandra.sh   ← Création keyspace ent_est
│   │   ├── keycloak/
│   │   │   ├── realm.json          ← Realm ent-est, 3 rôles, 2 clients
│   │   │   ├── bootstrap-realm.sh
│   │   │   ├── bootstrap-users.sh
│   │   │   └── users-partial-import.template.json
│   │   ├── minio/
│   │   │   └── init-minio.sh       ← Création 3 buckets
│   │   ├── prometheus/
│   │   │   └── prometheus.yml      ← Scrape 9 services
│   │   └── grafana/
│   │       └── provisioning/
│   │           ├── datasources/datasource.yml
│   │           └── dashboards/
│   │               ├── dashboard.yml
│   │               └── ent-platform.json
│   ├── manifests/                  ← Manifests Kubernetes (futur)
│   │   ├── namespaces.yaml
│   │   ├── cassandra/cassandra.yaml
│   │   ├── keycloak/ (3 fichiers)
│   │   ├── rabbitmq/rabbitmq-cluster.yaml
│   │   └── ingress/keycloak-ingress.yaml
│   ├── values/
│   │   ├── minio-values.yaml
│   │   └── traefik-values.yaml
│   ├── cluster/kind-config.yaml
│   └── Makefile
│
├── scripts/                        ← 8 scripts smoke-test bash
│   ├── compose-healthcheck.sh
│   ├── rbac-smoke-test.sh
│   ├── course-content-smoke-test.sh
│   ├── course-access-smoke-test.sh
│   ├── identity-admin-smoke-test.sh
│   ├── calendar-smoke-test.sh
│   ├── forum-smoke-test.sh
│   └── exam-smoke-test.sh
│
└── docs/
    ├── README-compose.md
    ├── plan-ms-ai-assistant.md
    └── sprint-0-close-checklist.md
```

---

## SECTION 13 — TABLEAU DE BORD DES PORTS

**TABLEAU complet (3 colonnes : Port | Service | Accessible depuis) :**

| Port | Service | Accessible |
|------|---------|-----------|
| 3000 | Frontend (nginx) | Navigateur |
| 3001 | Grafana | Navigateur |
| 5432 | PostgreSQL (Keycloak backend) | Docker interne |
| 5672 | RabbitMQ AMQP | Docker interne |
| 6379 | Redis | Docker interne |
| 8008 | ms-api-gateway | Navigateur + services |
| 8010 | ms-auth-core | Docker interne |
| 8011 | ms-course-content | Docker interne |
| 8012 | ms-course-access | Docker interne |
| 8013 | ms-identity-admin | Docker interne |
| 8014 | ms-notification | Docker interne |
| 8015 | ms-calendar-schedule | Docker interne |
| 8016 | ms-forum-chat + WebSocket | Docker interne + Navigateur (WS) |
| 8017 | ms-exam-assignment | Docker interne |
| 8018 | ms-ai-assistant | Docker interne |
| 8025 | Mailpit UI | Navigateur (dev) |
| 8080 | Keycloak | Navigateur + Docker |
| 9000 | Keycloak healthcheck | Docker interne |
| 9001 | MinIO Console | Navigateur (dev) |
| 9002 | MinIO API (presigned URLs) | Navigateur + Docker |
| 9042 | Cassandra CQL | Docker interne |
| 9090 | Prometheus | Navigateur |
| 11434 | Ollama API | Docker interne (profil ai) |
| 15672 | RabbitMQ Management UI | Navigateur (dev) |
| 1025 | Mailpit SMTP | Docker interne |

---

## SECTION 14 — CONCLUSION ET PERSPECTIVES

### 14.1 Bilan du Projet

**Texte complet :**
Le projet ENT-EST-Salé constitue une implémentation complète, fonctionnelle et documentée d'une plateforme numérique académique selon les principes DevOps et Cloud. En partant d'une feuille blanche, l'équipe a conçu et réalisé en intégralité une architecture microservices industrielle comprenant 10 services, 9 composants d'infrastructure, un frontend complet et une stack d'observabilité opérationnelle.

**Réalisations techniques :**
1. Architecture microservices avec découplage fort et interfaces API clairement définies
2. Sécurité industrielle : OAuth2/OIDC, RBAC 3 rôles, JWT RS256, communications sécurisées
3. Persistance NoSQL scalable avec Apache Cassandra (11 tables, patterns de clés primaires optimisés)
4. Messagerie événementielle asynchrone avec RabbitMQ (13 types d'événements versionnés)
5. Stockage objet cloud-native avec MinIO S3-compatible (presigned URLs, 2 buckets applicatifs)
6. Interface utilisateur moderne et accessible (React 19, shadcn/ui, dark/light mode, responsive)
7. Chat temps-réel via WebSocket avec gestionnaire de salles par module
8. Observabilité complète Prometheus + Grafana (métriques standardisées sur 9 services)
9. Suite de 8 scripts smoke-test couvrant tous les flux fonctionnels end-to-end
10. Déploiement one-command via Docker Compose avec ordonnancement automatique

**Compétences DevOps acquises :**
- Conteneurisation Docker (multi-stage builds, healthchecks, volumes)
- Infrastructure as Code (docker-compose.yml déclaratif)
- Pattern Twelve-Factor App (configuration par env vars, logs JSON, stateless)
- Observabilité (instrumentation Prometheus, dashboards Grafana)
- Sécurité by design (IAM Keycloak, RBAC, pas de secrets hardcodés)
- Messagerie event-driven (RabbitMQ, topic exchange, consumer asyncio)

### 14.2 Perspectives d'Évolution

**Liste complète :**
1. **Migration Kubernetes** : Les manifests sont déjà préparés dans `infra/manifests/` (namespaces, Cassandra StatefulSet, RabbitMQ Cluster, Keycloak Deployment, Ingress Traefik). Helm charts disponibles pour MinIO et Traefik.
2. **CI/CD Pipeline** : GitHub Actions / GitLab CI pour le build automatique des images Docker, les tests et le déploiement.
3. **Dashboards Grafana avancés** : Taux de requêtes par service, latence p50/p95/p99, taux d'erreurs, alertes.
4. **ms-ai-assistant en production** : Déploiement avec GPU cloud (AWS, GCP), modèles plus performants.
5. **Application mobile** : React Native connectée au même backend (API Gateway + WebSocket).
6. **Haute disponibilité** : Cassandra multi-nœuds (replication_factor=3), RabbitMQ cluster, MinIO distributed mode.
7. **Service de gestion des emplois du temps** (ms-timetable).
8. **Tests d'intégration automatisés** dans la pipeline CI.
9. **Authentification multi-facteurs (MFA)** via Keycloak.
10. **Analyse des données académiques** : service de reporting/analytics sur les données Cassandra.

---

## SECTION 15 — BIBLIOGRAPHIE / RÉFÉRENCES

Lister les technologies avec leurs versions et URLs officielles :
- FastAPI 0.111 — https://fastapi.tiangolo.com
- React 19 — https://react.dev
- Keycloak 26.1.4 — https://www.keycloak.org
- Apache Cassandra 5.0 — https://cassandra.apache.org
- RabbitMQ 4.1.3 — https://www.rabbitmq.com
- MinIO — https://min.io
- Docker Compose — https://docs.docker.com/compose
- Prometheus — https://prometheus.io
- Grafana — https://grafana.com
- Ollama + Llama3 — https://ollama.ai
- PyJWT — https://pyjwt.readthedocs.io
- aio_pika — https://aio-pika.readthedocs.io
- boto3 (AWS SDK) — https://boto3.amazonaws.com
- shadcn/ui — https://ui.shadcn.com
- Tailwind CSS 4 — https://tailwindcss.com
- Vite 8 — https://vitejs.dev
- React Router 7 — https://reactrouter.com
- prometheus-client Python — https://github.com/prometheus/client_python

---

## NOTES POUR CLAUDE DESIGN

1. **Langue** : Tout le contenu en FRANÇAIS
2. **Police** : Calibri (corps 11pt, titres h1=18pt bleu marine, h2=14pt bleu accent, h3=12pt gris)
3. **Couleurs** : #0F294D (bleu marine) / #1A56DB (accent) / #059669 (vert) / #374151 (gris texte)
4. **Tableaux** : En-têtes bleu marine (#0F294D) texte blanc, lignes alternées bleu clair (#E8F0FE) / blanc
5. **Marges** : 2.5cm haut/bas, 2.8cm gauche, 2.5cm droite
6. **Couverture** : Page dédiée, pas de numéro de page
7. **Numérotation pages** : À partir de la table des matières
8. **Sauvegarde** : `Rapport_ENT_EST_Sale_FINAL.docx` dans le répertoire courant
9. **Ne rien omettre** : Chaque section, chaque tableau, chaque code block
10. **Blocs de code** : Police Courier New 9pt, fond gris très clair ou encadrés
