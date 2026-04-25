# PLAN EXHAUSTIF — PRÉSENTATION PPTX
## ENT EST Salé — Projet DevOps & Cloud
### Document destiné à Claude Design pour génération automatique du fichier PPTX

---

## MÉTADONNÉES DU DOCUMENT

- **Titre global** : ENT EST Salé — Plateforme d'Enseignement Numérique Microservices
- **Module** : DevOps et Cloud
- **Filière** : Ingénierie des Applications Web et Mobile
- **École** : École Supérieure de Technologie (EST) Salé
- **Université** : Université Mohammed V — Rabat
- **Groupe** : 5 étudiants + 1 encadrant
- **Nombre de slides cibles** : 28 slides (+ slide de questions)
- **Format** : 16:9, résolution 1920×1080

---

## GUIDE DE DESIGN GLOBAL

### Palette de couleurs
- **Couleur primaire** : `#2563EB` (Bleu roi — Modern Blue)
- **Couleur secondaire** : `#1E40AF` (Bleu foncé — gradient vers le bas)
- **Accent 1** : `#F59E0B` (Ambre — highlights, badges)
- **Accent 2** : `#10B981` (Émeraude — succès, validation)
- **Fond clair** : `#F8FAFC` (Gris très clair)
- **Fond sombre** : `#0F172A` (Navy — slides de titre)
- **Texte principal** : `#1E293B`
- **Texte secondaire** : `#64748B`
- **Bordures / séparateurs** : `#E2E8F0`

### Typographies
- **Titre de slide** : Inter Bold ou Montserrat Bold, 36–44pt, couleur blanche (sur fond sombre) ou primaire (sur fond clair)
- **Sous-titre** : Inter SemiBold, 22–28pt
- **Corps de texte** : Inter Regular, 14–18pt
- **Code / technique** : JetBrains Mono ou Consolas, 12–14pt, fond `#1E293B` texte `#E2E8F0`
- **Badges / labels** : Inter Bold, 10–12pt, fond coloré, coins arrondis

### Style général
- Coins arrondis (12px) pour tous les blocs / cartes
- Ombres légères (`box-shadow: 0 4px 16px rgba(0,0,0,0.12)`) sur toutes les cartes
- Dégradés sur les en-têtes de section (bleu primaire → bleu foncé, de gauche à droite)
- Icônes : style Lucide (outline, mono-couleur)
- Séparateurs horizontaux fins (`#E2E8F0`)
- Fond de slide standard : blanc ou `#F8FAFC`
- Fond de slide section break : `#0F172A` avec texte blanc
- Numéros de slide : petit, coin inférieur droit, `#94A3B8`

### Éléments récurrents
- **Header strip** sur chaque slide : bande supérieure de 8px en dégradé bleu
- **Logo académique** : coin supérieur gauche (petit) : "EST Salé · UM5 · 2024–2025"
- **Numéro de slide** : coin inférieur droit
- **Pied de page** : "ENT EST Salé — DevOps & Cloud" centré en bas, 10pt gris

---

## SLIDE 1 — DIAPOSITIVE DE TITRE

**Fond** : `#0F172A` (navy sombre) avec motif subtil de points (`#1E293B`) — effet "starfield léger"

**Contenu** :
- Bloc centré avec :
  - Icône : mortier académique (GraduationCap) taille 72px, couleur `#2563EB`
  - Titre principal : **"ENT EST Salé"** — Inter ExtraBold 56pt, blanc
  - Sous-titre ligne 1 : *"Plateforme d'Enseignement Numérique*" — 28pt, `#93C5FD`
  - Sous-titre ligne 2 : *"Architecture Microservices · DevOps · Cloud"* — 20pt, `#64748B`
  - Séparateur horizontal dégradé bleu (2px, 40% largeur slide)
  - Badge : `DevOps & Cloud — Module 2024–2025` — fond `#2563EB`, texte blanc, coins 999px

**Zone bas de slide** (3 colonnes) :
- Gauche : "EST Salé · Université Mohammed V" — 14pt gris
- Centre : Logo ou nom du groupe — "Groupe 5 étudiants"
- Droite : Encadrant + date — "2024–2025"

---

## SLIDE 2 — SOMMAIRE / PLAN DE PRÉSENTATION

**Fond** : `#F8FAFC`
**Titre** : "Plan de Présentation" — bleu primaire, 38pt

**Contenu** : Grille 2 colonnes de 7+7 items numérotés avec icônes

| N° | Section | Icône |
|----|---------|-------|
| 01 | Contexte & Équipe | Users |
| 02 | Présentation du Projet | Layers |
| 03 | Architecture Globale | Network |
| 04 | Stack Technologique | Code |
| 05 | Infrastructure Docker | Container |
| 06 | Authentification Keycloak | Shield |
| 07 | API Gateway | Router |
| 08 | Microservices (10 services) | Server |
| 09 | Stockage : Cassandra & MinIO | Database |
| 10 | Messagerie RabbitMQ | MessageSquare |
| 11 | Interface Frontend | Monitor |
| 12 | Sécurité & RBAC | Lock |
| 13 | Observabilité & Métriques | BarChart |
| 14 | Tests & Validation | CheckCircle |
| 15 | Bilan & Perspectives | Sparkles |

**Design** : Chaque item = carte légère avec fond blanc, ombre subtile, numéro en badge bleu, texte gris

---

## SLIDE 3 — CONTEXTE ET ÉQUIPE

**Fond** : Blanc
**Titre** : "Contexte du Projet"

**Partie gauche (60%)** — Blocs d'info :

Bloc 1 — **École & Filière** :
- EST Salé — Université Mohammed V, Rabat
- Filière : Ingénierie des Applications Web et Mobile
- Module : DevOps et Cloud — 2024/2025

Bloc 2 — **Problématique** :
> "Les étudiants et enseignants de l'EST Salé ont besoin d'une plateforme numérique unifiée pour la gestion des cours, examens, forum et notifications — entièrement conteneurisée et déployable en production."

Bloc 3 — **Objectifs** :
- Concevoir une plateforme ENT (Environnement Numérique de Travail) complète
- Mettre en pratique les principes DevOps : conteneurisation, CI/CD, observabilité
- Architecture microservices avec orchestration Docker Compose

**Partie droite (40%)** — Équipe :

5 cartes "membre" empilées :
- Avatar circulaire (initiales sur fond bleu dégradé)
- Nom de l'étudiant
- Rôle dans le projet

Encart séparé avec fond doré clair :
- "Encadrant : M. [Nom]"
- Badge "Supervision"

---

## SLIDE 4 — VUE D'ENSEMBLE DU PROJET

**Fond** : `#F8FAFC`
**Titre** : "ENT EST Salé — Vue d'Ensemble"

**Zone principale** : Grande carte centrale avec les chiffres clés

**Grille 4 colonnes de métriques** :

| Métrique | Valeur | Icône |
|----------|--------|-------|
| Microservices | **10** | Server |
| Tables Cassandra | **11** | Database |
| Événements RabbitMQ | **13** | MessageSquare |
| Routes API Gateway | **40+** | Route |
| Pages Frontend | **11** | Monitor |
| Scripts de test | **8** | TestTube |
| Lignes de code | **~6 000** | Code |
| Services Docker | **25+** | Container |

**En bas** : Timeline du projet en ligne horizontale :
- Sprint 0 : Infrastructure de base (Keycloak, Cassandra, RabbitMQ, MinIO)
- Sprint 1 : Services core (Auth, Identity, Gateway, Notification, Course)
- Sprint 2 : Services avancés (Calendar, Forum, Exam, AI)
- Sprint 3 : Frontend complet + Observabilité

---

## SLIDE 5 — ARCHITECTURE GLOBALE (SCHÉMA PRINCIPAL)

**Fond** : `#0F172A`
**Titre** : "Architecture Générale" — blanc, 38pt

**Schéma d'architecture** — Diagramme en couches horizontal, fond sombre :

```
┌─────────────────────────────────────────────────────────────────────┐
│                     COUCHE CLIENTE (BROWSER)                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │    React 19 + TypeScript + Vite + Tailwind CSS + shadcn/ui   │   │
│  │              SPA · nginx · Port 3000                         │   │
│  └──────────────────┬────────────────────────────┬─────────────┘   │
│                     │ HTTP/REST                  │ WebSocket        │
└─────────────────────┼────────────────────────────┼─────────────────┘
                      ▼                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     COUCHE GATEWAY & AUTH                            │
│  ┌─────────────────────┐      ┌─────────────────────────────────┐  │
│  │  ms-api-gateway     │      │        Keycloak 26.1.4          │  │
│  │  FastAPI · Port 8000│◄────►│  OIDC/OAuth2 · PKCE · Port 8080│  │
│  │  JWT RS256 · RBAC   │      │  Realm ent-est · 3 rôles        │  │
│  └──────────┬──────────┘      └─────────────────────────────────┘  │
└─────────────┼───────────────────────────────────────────────────────┘
              │ HTTP interne (+ x-internal-token)
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    COUCHE MICROSERVICES (10 services)                │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────┐  │
│  │ms-auth-core│ │ms-identity │ │ms-course-  │ │ms-course-access│  │
│  │Port 8001   │ │Port 8002   │ │content 8003│ │Port 8004       │  │
│  └────────────┘ └────────────┘ └────────────┘ └────────────────┘  │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────┐  │
│  │ms-notif    │ │ms-calendar │ │ms-forum    │ │ms-exam-assign  │  │
│  │Port 8005   │ │Port 8006   │ │Port 8007   │ │Port 8008       │  │
│  └────────────┘ └────────────┘ └────────────┘ └────────────────┘  │
│  ┌────────────┐                                                     │
│  │ms-ai-asst  │                                                     │
│  │Port 8009   │                                                     │
│  └────────────┘                                                     │
└─────────────┬────────────────────────────────────────────────────────┘
              │
     ┌────────┴──────────┐
     ▼                   ▼
┌──────────────────┐  ┌─────────────────────────────────────────────┐
│ COUCHE DONNÉES   │  │          COUCHE MESSAGERIE & CACHE           │
│ ┌──────────────┐ │  │  ┌─────────────────┐   ┌─────────────────┐  │
│ │  Cassandra   │ │  │  │   RabbitMQ 4.1  │   │   Redis 7       │  │
│ │  5.0 · 9042  │ │  │  │   Port 5672     │   │   Port 6379     │  │
│ │  11 tables   │ │  │  │   13 événements │   │   Cache+Rate    │  │
│ └──────────────┘ │  │  └─────────────────┘   └─────────────────┘  │
│ ┌──────────────┐ │  └─────────────────────────────────────────────┘
│ │    MinIO     │ │
│ │  Port 9001   │ │  ┌─────────────────────────────────────────────┐
│ │  3 buckets   │ │  │       COUCHE OBSERVABILITÉ                  │
│ └──────────────┘ │  │  Prometheus 15s · Grafana · Mailpit SMTP    │
└──────────────────┘  └─────────────────────────────────────────────┘
```

**Design** : Chaque bloc = rectangle arrondi coloré par couche :
- Clients : violet
- Gateway/Auth : bleu primaire
- Microservices : bleu clair / cyan
- Données : vert émeraude
- Messagerie : orange
- Observabilité : jaune/ambre

Flèches avec labels ("HTTP/REST", "WebSocket JWT", "aio_pika", "JWKS", "boto3", "CQL")

---

## SLIDE 6 — STACK TECHNOLOGIQUE

**Fond** : Blanc
**Titre** : "Technologies Utilisées"

**Grille 3×4 de cartes technologie** (chaque carte = logo + nom + version + description courte) :

**Ligne 1 — Backend**
| Carte | Contenu |
|-------|---------|
| FastAPI 0.115 | Framework Python async, OpenAPI auto-généré |
| Python 3.12 | Langage principal, asyncio, type hints |
| Pydantic v2 | Validation des modèles de données |
| aio_pika | Client RabbitMQ asynchrone |

**Ligne 2 — Infrastructure**
| Carte | Contenu |
|-------|---------|
| Docker / Compose | Conteneurisation · 25+ services |
| Keycloak 26.1.4 | IAM · OIDC · OAuth2 · PKCE |
| Cassandra 5.0 | Base NoSQL distribuée · 11 tables |
| RabbitMQ 4.1.3 | Message broker · 13 event types |

**Ligne 3 — Frontend & Observabilité**
| Carte | Contenu |
|-------|---------|
| React 19 + Vite 8 | SPA moderne · TypeScript 6 |
| Tailwind CSS 4.2 | Utility-first CSS · shadcn/ui |
| Prometheus + Grafana | Métriques · Dashboards |
| MinIO + Redis | Stockage S3 · Cache / Rate limit |

**En bas** : Barre de légende des couches couleurs

---

## SLIDE 7 — INFRASTRUCTURE DOCKER COMPOSE

**Fond** : `#F8FAFC`
**Titre** : "Orchestration Docker Compose"

**Partie gauche** — Tableau des services (2 colonnes) :

**Tableau des 25+ services** :

| Service | Image | Port | Rôle |
|---------|-------|------|------|
| keycloak | keycloak/keycloak:26.1.4 | 8080 | IAM/OIDC |
| ms-api-gateway | build ./gateway | 8000 | Proxy central |
| ms-auth-core | build ./services/ms-auth-core | 8001 | Validation JWT |
| ms-identity-admin | build ./services/ms-identity-admin | 8002 | Gestion utilisateurs |
| ms-course-content | build ./services/ms-course-content | 8003 | Gestion cours |
| ms-course-access | build ./services/ms-course-access | 8004 | Accès étudiant |
| ms-notification | build ./services/ms-notification | 8005 | Emails/Notifications |
| ms-calendar-schedule | build ./services/ms-calendar-schedule | 8006 | Calendrier |
| ms-forum-chat | build ./services/ms-forum-chat | 8007 | Forum WebSocket |
| ms-exam-assignment | build ./services/ms-exam-assignment | 8008 | Examens/Devoirs |
| ms-ai-assistant | build ./services/ms-ai-assistant | 8009 | Assistant IA |
| cassandra | cassandra:5.0 | 9042 | Base de données |
| rabbitmq | rabbitmq:4.1.3-management | 5672/15672 | Message broker |
| minio | minio/minio:latest | 9000/9001 | Stockage fichiers |
| redis | redis:7-alpine | 6379 | Cache / Rate limit |
| mailpit | axllent/mailpit:v1.18 | 1025/8025 | SMTP sandbox |
| prometheus | prom/prometheus:latest | 9090 | Métriques |
| grafana | grafana/grafana:latest | 3001 | Dashboards |
| frontend | build ./frontend (nginx) | 3000 | Interface web |
| ollama | ollama/ollama:latest | 11434 | LLM local |
| keycloak-init | custom | — | Init realm/clients |
| cassandra-init | custom | — | Init keyspace/tables |
| minio-init | custom | — | Init buckets |

**Partie droite** — Diagramme de dépendances (dependency graph) :

```
cassandra ──────────────────────────────────┐
rabbitmq ────────────────────────────────┐  │
keycloak ────────────────────────────┐   │  │
                                     ▼   ▼  ▼
minio ──────────────────────► keycloak-init
redis                          cassandra-init
                               minio-init
                                    │
                                    ▼
                               ms-auth-core
                               ms-identity-admin
                               ms-course-content
                               ms-course-access
                               ms-notification
                               ms-calendar-schedule
                               ms-forum-chat
                               ms-exam-assignment
                               ms-ai-assistant
                                    │
                                    ▼
                               ms-api-gateway
                                    │
                                    ▼
                               frontend (nginx)
```

**Points techniques mis en avant** (3 bullets avec icône) :
- Healthchecks sur tous les services critiques (cassandra: `cqlsh`, rabbitmq: `rabbitmq-diagnostics`, minio: `curl /minio/health/live`)
- Volumes nommés persistants : `cassandra_data`, `rabbitmq_data`, `minio_data`, `grafana_data`
- Network bridge dédié : `ent-network` (tous les services)
- `restart: unless-stopped` sur tous les services de production

---

## SLIDE 8 — AUTHENTIFICATION KEYCLOAK & OIDC

**Fond** : Blanc
**Titre** : "Authentification · Keycloak 26.1.4 · OIDC/OAuth2"

**Partie gauche (45%)** — Configuration Realm :

Carte bleu clair :
- **Realm** : `ent-est`
- **3 Rôles Realm** : `admin`, `teacher`, `student`
- **2 Clients** :
  - `ent-gateway` : confidential, client_credentials
  - `ent-frontend` : public, standardFlow + directAccessGrants, PKCE
- **redirect_uris** : `localhost:3000/*`, `localhost:5173/*`
- **Token** : RS256, JWKS auto-géré

**Partie droite (55%)** — Flux PKCE (diagramme de séquence) :

```
Browser (React)          Keycloak              API Gateway
    │                       │                       │
    │──── 1. Login form ────►│                       │
    │◄─── 2. Redirect +     │                       │
    │     code_verifier      │                       │
    │──── 3. Auth code ─────►│                       │
    │◄─── 4. Access Token   │                       │
    │     (JWT RS256)        │                       │
    │                        │                       │
    │────── 5. GET /api/... + Bearer ───────────────►│
    │                        │   6. JWKS verify      │
    │                        │◄──────────────────────│
    │◄──── 7. Response ─────────────────────────────│
```

**En bas** — Structure du JWT (carte code sombre) :
```json
{
  "sub": "uuid-keycloak-user",
  "preferred_username": "student1",
  "email": "student1@est-sale.ma",
  "realm_access": {
    "roles": ["student", "default-roles-ent-est"]
  },
  "aud": ["ent-gateway", "account"],
  "iss": "http://keycloak:8080/realms/ent-est",
  "exp": 1735000000,
  "iat": 1734996400
}
```

---

## SLIDE 9 — API GATEWAY

**Fond** : `#F8FAFC`
**Titre** : "ms-api-gateway · Proxy Central · Port 8000"

**Schéma de routage** (gauche, 50%) :

```
Client HTTP
    │
    ▼
┌─────────────────────────────────────────┐
│          ms-api-gateway (FastAPI)        │
│  verify_jwt_and_get_claims()            │
│  require_roles([...])                   │
│  _request_downstream() + retry logic   │
│  exponential backoff (max 3 attempts)   │
├─────────────────────────────────────────┤
│  /api/auth/*     → ms-auth-core:8001    │
│  /api/users/*    → ms-identity:8002     │
│  /api/courses/*  → ms-course-content:8003│
│  /api/access/*   → ms-course-access:8004│
│  /api/notifs/*   → ms-notification:8005 │
│  /api/calendar/* → ms-calendar:8006     │
│  /api/forum/*    → ms-forum-chat:8007   │
│  /api/exams/*    → ms-exam-assignment:8008│
│  /api/assistant/*→ ms-ai-assistant:8009 │
│  /api/stats      → agrégation multi-svc │
└─────────────────────────────────────────┘
```

**Tableau des routes clés** (droite, 50%) :

| Méthode | Route | Rôles |
|---------|-------|-------|
| GET | /api/auth/me | tous |
| GET | /api/auth/introspect | tous |
| GET | /api/users | admin |
| POST | /api/users | admin |
| POST | /api/users/{id}/roles | admin |
| GET | /api/courses | teacher/admin |
| POST | /api/courses | teacher/admin |
| GET | /api/access/courses | student |
| GET | /api/access/courses/{id}/asset/{aid} | student |
| POST | /api/calendar/events | tous |
| GET | /api/forum/threads | tous |
| WS | /api/forum/chat/ws | tous |
| POST | /api/exams/assignments | teacher/admin |
| POST | /api/exams/{id}/submit | student |
| GET | /api/assistant/chat | tous |
| GET | /api/stats | admin |

**Points clés** (3 badges) :
- JWT RS256 · PyJWKClient · JWKS live
- Retry exponentiel · max 3 tentatives
- x-request-id propagé à tous les services

---

## SLIDE 10 — MICROSERVICES : OVERVIEW

**Fond** : Blanc
**Titre** : "10 Microservices Indépendants"

**Grille 2×5 de cartes service** :

Chaque carte contient :
- Icône du service (Lucide)
- Nom du service en badge coloré
- Port
- 3 mots-clés techniques
- 2–3 endpoints principaux

**Carte 1 : ms-auth-core (Port 8001)**
- Icône : ShieldCheck, bleu
- PyJWKClient · RS256 · JWKS
- `GET /auth/me`, `POST /auth/introspect`

**Carte 2 : ms-identity-admin (Port 8002)**
- Icône : Users, violet
- Keycloak Admin API · Cassandra user_profiles · aio_pika
- `GET /users`, `POST /users`, `POST /users/{id}/roles`

**Carte 3 : ms-course-content (Port 8003)**
- Icône : BookOpen, vert
- Cassandra courses/course_assets · MinIO upload · Events
- `POST /courses`, `POST /courses/{id}/assets`, internal `/internal/courses`

**Carte 4 : ms-course-access (Port 8004)**
- Icône : GraduationCap, cyan
- Presigned URL TTL=180s · 2 clients boto3 · INTERNAL_API_TOKEN
- `GET /access/courses`, `GET /access/courses/{id}/asset/{aid}`

**Carte 5 : ms-notification (Port 8005)**
- Icône : Bell, orange
- Consumer RabbitMQ · aiosmtplib · Cassandra notifications
- `GET /notifications`, `PATCH /notifications/{id}/read`

**Carte 6 : ms-calendar-schedule (Port 8006)**
- Icône : CalendarDays, indigo
- Cassandra events · CRUD · filtre par mois/module
- `POST /calendar/events`, `GET /calendar/events`, `PATCH /calendar/events/{id}`

**Carte 7 : ms-forum-chat (Port 8007)**
- Icône : MessageSquare, rose
- WebSocket · ConnectionManager · Cassandra threads/messages/counters
- `GET /forum/threads`, `POST /forum/threads`, `WS /chat/ws?token=...&room=...`

**Carte 8 : ms-exam-assignment (Port 8008)**
- Icône : ClipboardList, ambre
- Cassandra assignments/submissions · MinIO fichiers 50MB · Grade validation
- `POST /exams/assignments`, `POST /exams/{id}/submit`, `POST /exams/submissions/{id}/grade`

**Carte 9 : ms-ai-assistant (Port 8009)**
- Icône : Sparkles, violet/rose
- Ollama LLM · Rate limiter · Anti-injection · Contexte par rôle
- `POST /assistant/chat`, `GET /assistant/faq`, `GET /assistant/faq/{q_id}/answer`

**Note** : ms-api-gateway est le 10ème service (compte comme microservice de routing)

---

## SLIDE 11 — BASE DE DONNÉES CASSANDRA

**Fond** : `#F8FAFC`
**Titre** : "Apache Cassandra 5.0 · Keyspace ent_est · 11 Tables"

**Partie gauche** — Schéma des tables (liste structurée) :

```
Keyspace: ent_est
├── user_profiles        (PK: user_id)
├── courses              (PK: course_id)
├── course_assets        (PK: (course_id, asset_id))
├── notifications        (PK: (user_id, created_at DESC, notif_id))
├── calendar_events      (PK: (owner_id, event_id))
├── forum_threads        (PK: (module_code, created_at DESC, thread_id))
├── forum_messages       (PK: (room_id, created_at ASC, msg_id))
├── forum_thread_counters(PK: thread_id — COUNTER type)
├── assignments          (PK: assignment_id)
├── submissions          (PK: submission_id)
└── submissions_by_assignment (PK: assignment_id, clustering: submission_id)
```

**Partie droite** — Détail de 3 tables importantes (cartes code sombre) :

**Table notifications** :
```sql
CREATE TABLE notifications (
  user_id   TEXT,
  created_at TIMESTAMP,
  notif_id  UUID,
  type      TEXT,
  payload   TEXT,
  read      BOOLEAN,
  PRIMARY KEY ((user_id), created_at, notif_id)
) WITH CLUSTERING ORDER BY (created_at DESC);
```

**Table forum_messages** :
```sql
CREATE TABLE forum_messages (
  room_id    TEXT,
  created_at TIMESTAMP,
  msg_id     UUID,
  sender_id  TEXT,
  username   TEXT,
  content    TEXT,
  PRIMARY KEY ((room_id), created_at, msg_id)
) WITH CLUSTERING ORDER BY (created_at ASC);
```

**Table submissions_by_assignment** (index secondaire) :
```sql
CREATE TABLE submissions_by_assignment (
  assignment_id UUID,
  submission_id UUID,
  PRIMARY KEY (assignment_id, submission_id)
);
```

**Points clés** (bas de slide) :
- Pattern `_ensure_db()` : initialisation lazy au démarrage de chaque service
- PlainTextAuthProvider : cassandra/cassandra
- Prepared statements : performance optimisée
- Counters natifs Cassandra pour les statistiques de threads

---

## SLIDE 12 — MESSAGERIE RABBITMQ

**Fond** : Blanc
**Titre** : "RabbitMQ 4.1.3 · Exchange Topic · 13 Événements"

**Schéma de flux** (haut, 60% largeur) :

```
 PRODUCTEURS                    EXCHANGE                    CONSOMMATEUR
                           ent.events.topic
ms-identity-admin  ──────► [topic, durable]
ms-course-content  ──────►                  ──► Q: notifications ──► ms-notification
ms-exam-assignment ──────►  routing_key =   ──► Q: ai-context    ──► ms-ai-assistant
ms-calendar-sched  ──────►  event_type[0]
ms-forum-chat      ──────►  + event_type[1]
```

**Tableau complet des 13 événements** :

| # | Event Type | Routing Key | Producteur | Consommateur |
|---|------------|-------------|------------|--------------|
| 1 | user.created.v1 | user.created | ms-identity | ms-notification, ms-ai |
| 2 | user.role.assigned.v1 | user.role | ms-identity | ms-notification |
| 3 | course.created.v1 | course.created | ms-course-content | ms-notification, ms-ai |
| 4 | course.updated.v1 | course.updated | ms-course-content | ms-notification |
| 5 | course.deleted.v1 | course.deleted | ms-course-content | ms-notification |
| 6 | course.asset.uploaded.v1 | course.asset | ms-course-content | ms-notification |
| 7 | course.asset.deleted.v1 | course.asset | ms-course-content | ms-notification |
| 8 | exam.assignment.created.v1 | exam.assignment | ms-exam | ms-notification, ms-ai |
| 9 | exam.submission.graded.v1 | exam.submission | ms-exam | ms-notification |
| 10 | calendar.event.created.v1 | calendar.event | ms-calendar | ms-notification, ms-ai |
| 11 | calendar.event.updated.v1 | calendar.event | ms-calendar | ms-notification |
| 12 | forum.thread.created.v1 | forum.thread | ms-forum | ms-notification |
| 13 | forum.message.posted.v1 | forum.message | ms-forum | ms-ai |

**Encart technique** (carte code sombre, coin bas droit) :
```python
# Enveloppe standard de tous les messages
{
  "event_type": "user.created.v1",
  "version": "v1",
  "timestamp": "2025-01-15T10:00:00Z",
  "payload": { ... }
}
```

**Points clés** :
- Exchange unique `ent.events.topic` — topic, durable
- Routing key = 2 premiers segments du event_type
- Versioning `.v1` pour compatibilité future
- aio_pika (async) dans tous les services

---

## SLIDE 13 — STOCKAGE MINIO & REDIS

**Fond** : `#F8FAFC`
**Titre** : "Stockage Objet MinIO · Cache Redis"

**Partie gauche (55%)** — MinIO :

Schéma :
```
ms-course-content ──boto3──► MinIO (Port 9000)
                              ├── bucket: course-assets
                              │    └── {course_id}/{asset_id}/{filename}
                              ├── bucket: exam-submissions
                              │    └── {assignment_id}/{submission_id}/{filename}
                              └── bucket: avatars
                                   └── {user_id}/avatar.{ext}

ms-course-access  ──boto3──► MinIO (Port 9000)
   s3_upload = endpoint interne 9000
   s3_sign   = endpoint externe 9002 (accès navigateur)
   Presigned URL TTL = 180 secondes
```

2 clients boto3 dans ms-course-access et ms-exam :
- `s3_upload` : endpoint interne `minio:9000` pour upload depuis les services
- `s3_sign` : endpoint public `localhost:9002` pour URLs signées accessibles par le navigateur

Limite de taille : `client_max_body_size 100M` (nginx), `MAX_FILE_SIZE = 50MB` (ms-exam)

**Partie droite (45%)** — Redis :

```
Redis 7-alpine · Port 6379

Usage 1 : CACHE
  ms-ai-assistant context_store → dict en mémoire
  (non Redis direct dans cette version)

Usage 2 : RATE LIMITING
  ms-ai-assistant : RateLimiter
  ┌────────────────────────────────┐
  │ class RateLimiter:             │
  │   max_requests = 20           │
  │   window_seconds = 60         │
  │   requests: dict[str, deque]  │
  │   async def is_allowed(key)   │
  │   → sliding window algorithm  │
  └────────────────────────────────┘
  
  Limite : 20 requêtes / minute / utilisateur
  Clé : user_id (sub du JWT)
```

---

## SLIDE 14 — MICROSERVICE DÉTAIL : ms-ai-assistant

**Fond** : Fond dégradé violet sombre (`#1E1B4B` → `#0F172A`)
**Titre** : "ms-ai-assistant · Assistant IA Contextuel" — blanc

**Architecture interne** (diagramme) :

```
Requête utilisateur
        │
        ▼
┌───────────────────────────┐
│   RateLimiter             │  20 req/min par user_id
│   sliding window          │  → 429 si dépassé
└───────────┬───────────────┘
            │
            ▼
┌───────────────────────────┐
│   Anti-Injection Guard    │  8 regex patterns
│   INJECTION_PATTERNS      │  + PROMPT_INJECTION_PATTERNS list
│   → 400 si détecté        │  Redact PII (email/phone/date)
└───────────┬───────────────┘
            │
            ▼
┌───────────────────────────┐
│   _build_context_for_role()│
│   admin   → stats système │  context_store (RabbitMQ events)
│   teacher → cours/examens │  mis à jour en temps réel
│   student → cours/notes   │
└───────────┬───────────────┘
            │
            ▼
┌───────────────────────────┐
│   Ollama API              │  POST /api/generate
│   model: llama3.2         │  temperature: 0.7
│   stream: false           │  Port 11434 (local)
└───────────┬───────────────┘
            │
            ▼
       Réponse JSON
```

**3 points de sécurité** (badges colorés) :
- 8 patterns regex anti-injection (system prompt leak, ignore instructions, etc.)
- Redaction PII : email → `[EMAIL]`, téléphone → `[PHONE]`, dates → `[DATE]`
- Contexte isolé par rôle : chaque rôle ne voit que ses données pertinentes

---

## SLIDE 15 — MICROSERVICE DÉTAIL : ms-forum-chat (WebSocket)

**Fond** : Blanc
**Titre** : "ms-forum-chat · Forum Temps Réel · WebSocket"

**Schéma WebSocket** (gauche, 50%) :

```
Browser (React)
    │
    │ WS /chat/ws?token=JWT&room=module_code
    ▼
ms-api-gateway
    │ proxy WebSocket upgrade
    ▼
ms-forum-chat (Port 8007)
    │
    ▼
┌──────────────────────────────────┐
│  ConnectionManager               │
│  active: dict[room, list[WS]]    │
│                                  │
│  async connect(ws, room, user)   │
│  async disconnect(ws, room)      │
│  async broadcast(room, msg)      │
└──────────────────────────────────┘
    │
    ├── Cassandra forum_threads
    ├── Cassandra forum_messages
    └── Cassandra forum_thread_counters (COUNTER)
```

**Messages système JSON** (carte code sombre) :
```json
// Connexion
{"type": "system", "event": "join",
 "username": "student1", "room": "web-dev",
 "timestamp": "2025-01-15T10:00:00Z"}

// Déconnexion
{"type": "system", "event": "leave",
 "username": "student1", "room": "web-dev",
 "timestamp": "2025-01-15T10:05:00Z"}

// Message normal
{"type": "message", "sender_id": "uuid",
 "username": "student1", "content": "Bonjour !",
 "msg_id": "uuid", "timestamp": "..."}
```

**Tableau 3 tables Cassandra Forum** (droite, 50%) :

| Table | PK | Clustering | Usage |
|-------|----|------------|-------|
| forum_threads | module_code | created_at DESC, thread_id | Liste des sujets |
| forum_messages | room_id | created_at ASC, msg_id | Messages en ordre |
| forum_thread_counters | thread_id | — (COUNTER) | Comptage messages |

---

## SLIDE 16 — INTERFACE FRONTEND (ARCHITECTURE)

**Fond** : `#F8FAFC`
**Titre** : "Frontend · React 19 · TypeScript · Vite"

**Stack technique** (gauche, 40%) :

Carte blanche avec badges tech :
- React 19.2.4 — SPA
- TypeScript 6.0.2 — Types stricts
- Vite 8.0.4 — Build ultra-rapide
- Tailwind CSS 4.2.2 — Utility-first
- shadcn/ui 4.3.0 — Composants accessibles
- React Router 7.14.1 — Navigation SPA
- Lucide React 1.8.0 — Icônes

**Structure des pages** (centre/droite, 60%) :

Arbre de routes avec icônes :
```
/login              → LoginPage (PKCE + directAccessGrant)
/app                → AppShell (sidebar + header)
  /                 → DashboardPage (stats + widgets)
  /assistant        → AssistantPage (chat IA)
  /admin            → AdminPage [admin]
  /teacher          → TeacherPage [teacher/admin]
  /student          → StudentPage [student]
  /calendar         → CalendarPage
  /forum            → ForumPage (WebSocket)
  /exams            → ExamPage
  /notifications    → NotificationsPage
  /profile          → ProfilePage
```

**AppShell** — description :
- Sidebar : 256px (ouvert) / 72px (fermé) — toggle smooth 300ms
- 9 items de navigation filtrés par rôle
- Badge notifications temps réel (poll 60s)
- Toggle thème dark/light
- Dropdown utilisateur (Profile, Notifications, Sign Out)
- Header sticky : "Role Workspace" + "Welcome back, username"

**Auth Context** (bas) :
```
AuthProvider
  ├── PKCE flow (standardFlow)
  ├── directAccessGrant (username/password)
  ├── Auto-refresh token (< 60s expiry)
  ├── apiFetch<T>(url) → Bearer auto-injecté
  ├── hasAnyRole([...]) → boolean
  └── logout() → clear + navigate /login
```

---

## SLIDE 17 — INTERFACE FRONTEND (PAGES)

**Fond** : Blanc
**Titre** : "Pages de l'Application"

**Grille 2×3 de captures / mockups de pages** :

(Puisque pas de vraies captures disponibles, décrire le contenu de chaque page sous forme de "wireframe décrit")

**Page 1 — Dashboard**
- Grille de widgets : stats (cours inscrits, examens à rendre, messages non lus, événements proches)
- Activité récente (timeline)
- Raccourcis rapides

**Page 2 — Assistant IA**
- Interface chat (bulle gauche = IA, droite = utilisateur)
- Zone de saisie avec bouton envoyer
- Section FAQ en dessous
- Contexte affiché selon le rôle de l'utilisateur

**Page 3 — Course Studio (Teacher)**
- Formulaire de création de cours
- Upload de fichiers (drag & drop)
- Liste des cours existants avec options édition/suppression

**Page 4 — Forum**
- Liste des threads par module
- Zone de chat WebSocket en temps réel
- Indicateur "en ligne"
- Messages système (join/leave)

**Page 5 — Examens**
- Teacher : créer un devoir, voir soumissions, noter
- Student : voir les devoirs actifs, soumettre un fichier (50MB max), voir ses notes

**Page 6 — Notifications**
- Liste chronologique des notifications
- Badge rouge non lues dans la sidebar
- Bouton "marquer comme lu"

---

## SLIDE 18 — SÉCURITÉ & RBAC

**Fond** : `#0F172A`
**Titre** : "Sécurité · RBAC · Modèle d'Autorisation" — blanc

**Modèle RBAC** (gauche, 45%) :

```
Keycloak Realm Roles
├── admin
│   ├── Gestion utilisateurs (CRUD)
│   ├── Accès stats globales
│   ├── Création cours
│   └── Toutes les routes
├── teacher
│   ├── Création cours + assets
│   ├── Création examens
│   ├── Notation soumissions
│   └── Forum + Calendar
└── student
    ├── Lecture cours (presigned URL)
    ├── Soumission examens
    ├── Forum + Calendar
    └── Notifications
```

**Pattern de sécurité** (droite, 55%) :

Couche 1 — Keycloak (externe) :
```python
# Gateway - vérification JWT RS256
async def verify_jwt_and_get_claims(token: str):
    jwks_client = PyJWKClient(JWKS_URL)
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    payload = jwt.decode(token, signing_key.key,
                        algorithms=["RS256"],
                        audience=EXPECTED_AUD)
    return payload
```

Couche 2 — require_roles() (par route) :
```python
def require_roles(allowed: list[str]):
    async def check(claims=Depends(get_claims)):
        roles = claims.get("realm_access",{}).get("roles",[])
        if not any(r in roles for r in allowed):
            raise HTTPException(403, "Forbidden")
    return Depends(check)

@router.post("/courses")
async def create_course(
    _=require_roles(["teacher","admin"])
):...
```

Couche 3 — INTERNAL_API_TOKEN (inter-services) :
```python
# ms-course-content routes internes
@router.get("/internal/courses")
async def list_courses_internal(
    x_internal_token: str = Header(...)
):
    if x_internal_token != INTERNAL_API_TOKEN:
        raise HTTPException(401)
```

**Points de sécurité additionnels** :
- PKCE obligatoire pour le client public ent-frontend
- Pas de secrets client exposés côté navigateur
- Headers CORS configurés par nginx
- x-request-id pour traçabilité bout-en-bout

---

## SLIDE 19 — OBSERVABILITÉ : PROMETHEUS & GRAFANA

**Fond** : `#F8FAFC`
**Titre** : "Observabilité · Prometheus · Grafana"

**Schéma de collecte** :

```
ms-auth-core:8001/metrics ──┐
ms-api-gateway:8000/metrics ─┤
ms-identity-admin:8002/metrics┤
ms-course-content:8003/metrics┼──► Prometheus :9090 ──► Grafana :3001
ms-course-access:8004/metrics─┤   scrape_interval: 15s   Dashboards
ms-notification:8005/metrics ─┤   auto-provisioned       auto-provisioned
ms-calendar:8006/metrics ─────┤
ms-forum-chat:8007/metrics ───┤
ms-exam-assignment:8008/metrics┘
```

**Module runtime.py partagé** — le cœur de l'observabilité (carte code sombre) :

```python
# 2 métriques Prometheus par service
REQUEST_COUNTER = Counter(
    "ent_http_requests_total",
    "Total HTTP requests",
    ["service", "method", "path", "status"]
)
REQUEST_DURATION = Histogram(
    "ent_http_request_duration_seconds",
    "HTTP request duration",
    ["service", "method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.2, 0.4, 0.8, 1.5, 3, 6)
)

def setup_service_runtime(app: FastAPI, service_name: str):
    # Middleware : mesure durée + log structuré JSON
    # Handler 404/500 standardisés
    # Route GET /metrics → Prometheus
    # Route GET /health → {"status":"ok","service":...}
    # x-request-id propagation (UUID si absent)
```

**Métriques collectées** :
- `ent_http_requests_total{service, method, path, status}` — Counter
- `ent_http_request_duration_seconds{service, method, path}` — Histogram
- Labels permettent filtrage par service, méthode HTTP, code de réponse

**Dashboards Grafana** :
- Request rate par service (req/sec)
- Latence P50/P95/P99 par endpoint
- Taux d'erreurs (4xx/5xx)
- Health status de tous les services

---

## SLIDE 20 — TESTS ET VALIDATION

**Fond** : Blanc
**Titre** : "Tests & Validation · 8 Scripts Smoke-Test"

**Grille 2×4 de cartes script** :

| Script | Service testé | Flux testé |
|--------|--------------|------------|
| auth-smoke-test.sh | ms-auth-core | GET /auth/me + introspect avec JWT valide/invalide |
| identity-smoke-test.sh | ms-identity-admin | CRUD utilisateurs + assignation rôles + 403 si non-admin |
| course-smoke-test.sh | ms-course-content | Créer cours + upload asset + suppression |
| access-smoke-test.sh | ms-course-access | Étudiant accède presigned URL + 403 pour teacher |
| notification-smoke-test.sh | ms-notification | Trigger event + vérifier notification créée |
| calendar-smoke-test.sh | ms-calendar-schedule | CRUD événements + filtres mois/module |
| forum-smoke-test.sh | ms-forum-chat | CRUD threads + WebSocket connect/message |
| exam-smoke-test.sh | ms-exam-assignment | Créer devoir + soumettre + noter + 400 grade > max |

**Extrait du pattern commun** (carte code sombre) :
```bash
#!/bin/bash
BASE=http://localhost:8000

# 1. Obtenir token Keycloak (password grant)
TEACHER_TOKEN=$(curl -s -X POST \
  http://localhost:8080/realms/ent-est/protocol/openid-connect/token \
  -d "client_id=ent-frontend&grant_type=password&\
      username=teacher1&password=teacher1" \
  | jq -r .access_token)

# 2. Tester route protégée
curl -s -H "Authorization: Bearer $TEACHER_TOKEN" \
     $BASE/api/exams/assignments | jq .

# 3. Valider 403 pour non-autorisé
STUDENT_TOKEN=$(...)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
     -H "Authorization: Bearer $STUDENT_TOKEN" \
     -X POST $BASE/api/exams/assignments)
[ "$STATUS" = "403" ] && echo "✓ RBAC OK" || echo "✗ FAIL"

# 4. Valider 400 pour grade invalide
curl -s -X POST .../grade -d '{"grade":110,"max_grade":100}'
# → 400 Bad Request attendu
```

**Validation des contraintes métier** :
- Grade ≤ max_grade (400 si dépassé)
- Fichier ≤ 50MB (413 si dépassé)
- end_time > start_time pour les événements calendrier
- Seul l'auteur peut modifier son cours/devoir (403 sinon)

---

## SLIDE 21 — PATTERNS & CONVENTIONS

**Fond** : `#F8FAFC`
**Titre** : "Patterns Communs · Conventions de Code"

**Grille 2×3 de cartes pattern** :

**Pattern 1 — Structure de chaque service** :
```
services/ms-{nom}/
├── app/
│   ├── main.py        # FastAPI app + routes
│   └── runtime.py     # copie verbatim du module partagé
├── Dockerfile         # multi-stage si besoin
└── requirements.txt   # dépendances minimales
```

**Pattern 2 — Startup FastAPI** :
```python
app = FastAPI(title="ms-{nom}")
setup_service_runtime(app, "{nom}")

@app.on_event("startup")
async def startup():
    await _ensure_db()    # Cassandra init lazy
    asyncio.create_task(_consume_events()) # RabbitMQ consumer
```

**Pattern 3 — Modèles Pydantic** :
```python
class CreateCourseRequest(BaseModel):
    title: str
    description: str
    module_code: str
    teacher_id: str

class CourseResponse(BaseModel):
    course_id: str
    title: str
    created_at: datetime
```

**Pattern 4 — Publish RabbitMQ** :
```python
async def _publish_event(event_type: str, payload: dict):
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    exchange = await channel.declare_exchange(
        "ent.events.topic", aio_pika.ExchangeType.TOPIC, durable=True
    )
    routing_key = ".".join(event_type.split(".")[:2])
    body = json.dumps({"event_type": event_type,
                       "version": "v1",
                       "timestamp": datetime.utcnow().isoformat(),
                       "payload": payload})
    await exchange.publish(
        aio_pika.Message(body.encode()), routing_key=routing_key
    )
```

**Pattern 5 — Logging structuré JSON** :
```python
# Via setup_service_runtime → middleware log
{
  "timestamp": "2025-01-15T10:00:00Z",
  "service": "ms-course-content",
  "method": "POST",
  "path": "/courses",
  "status": 201,
  "duration_ms": 45.2,
  "request_id": "uuid-v4"
}
```

**Pattern 6 — Dockerfile multi-stage** :
```dockerfile
# Backend services
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

# Frontend (multi-stage)
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

---

## SLIDE 22 — ARBRE DE FICHIERS DU PROJET

**Fond** : `#0F172A`
**Titre** : "Structure du Projet" — blanc

**Arbre complet** (2 colonnes, police JetBrains Mono 11pt, fond sombre) :

**Colonne gauche** :
```
ent-est-sale-platform/
├── docker-compose.yml          (766 lignes)
├── gateway/
│   └── app/
│       ├── main.py             (996 lignes, 40+ routes)
│       └── runtime.py
├── services/
│   ├── ms-auth-core/
│   │   └── app/main.py
│   ├── ms-identity-admin/
│   │   └── app/main.py
│   ├── ms-course-content/
│   │   └── app/main.py
│   ├── ms-course-access/
│   │   └── app/main.py
│   ├── ms-notification/
│   │   └── app/main.py
│   ├── ms-calendar-schedule/
│   │   └── app/main.py
│   ├── ms-forum-chat/
│   │   └── app/main.py
│   ├── ms-exam-assignment/
│   │   └── app/main.py
│   └── ms-ai-assistant/
│       └── app/main.py
```

**Colonne droite** :
```
├── frontend/
│   ├── src/
│   │   ├── App.tsx             (routes)
│   │   ├── context/
│   │   │   ├── auth-context.tsx
│   │   │   └── theme-context.tsx
│   │   ├── components/
│   │   │   ├── app-shell.tsx   (sidebar + header)
│   │   │   └── route-guards.tsx
│   │   └── pages/
│   │       ├── dashboard-page.tsx
│   │       ├── assistant-page.tsx
│   │       ├── admin-page.tsx
│   │       ├── teacher-page.tsx
│   │       ├── student-page.tsx
│   │       ├── calendar-page.tsx
│   │       ├── forum-page.tsx
│   │       ├── exam-page.tsx
│   │       └── notifications-page.tsx
│   ├── nginx.conf
│   └── package.json
├── infra/compose/
│   ├── keycloak/realm.json
│   ├── prometheus/prometheus.yml
│   └── grafana/
│       ├── datasources/
│       └── dashboards/
└── scripts/
    ├── auth-smoke-test.sh
    ├── identity-smoke-test.sh
    ├── course-smoke-test.sh
    ├── access-smoke-test.sh
    ├── notification-smoke-test.sh
    ├── calendar-smoke-test.sh
    ├── forum-smoke-test.sh
    └── exam-smoke-test.sh
```

---

## SLIDE 23 — TABLEAU DES PORTS & SERVICES

**Fond** : Blanc
**Titre** : "Cartographie des Ports · Accès aux Services"

**Grand tableau stylisé** (centré, lignes alternées bleu clair / blanc) :

| Service | Port interne | Port externe | URL d'accès |
|---------|-------------|-------------|-------------|
| Frontend (nginx) | 80 | 3000 | http://localhost:3000 |
| ms-api-gateway | 8000 | 8000 | http://localhost:8000 |
| ms-auth-core | 8001 | — | interne seulement |
| ms-identity-admin | 8002 | — | interne seulement |
| ms-course-content | 8003 | — | interne seulement |
| ms-course-access | 8004 | — | interne seulement |
| ms-notification | 8005 | — | interne seulement |
| ms-calendar-schedule | 8006 | — | interne seulement |
| ms-forum-chat | 8007 | 8007 | ws://localhost:8007 |
| ms-exam-assignment | 8008 | — | interne seulement |
| ms-ai-assistant | 8009 | — | interne seulement |
| Keycloak | 8080 | 8080 | http://localhost:8080 |
| Cassandra | 9042 | 9042 | cqlsh localhost 9042 |
| RabbitMQ AMQP | 5672 | 5672 | amqp://guest:guest@localhost |
| RabbitMQ Management | 15672 | 15672 | http://localhost:15672 |
| MinIO API | 9000 | 9000 | http://localhost:9000 |
| MinIO Console | 9001 | 9001 | http://localhost:9001 |
| MinIO externe (sign) | 9000 | 9002 | http://localhost:9002 |
| Redis | 6379 | 6379 | redis-cli -h localhost |
| Mailpit SMTP | 1025 | 1025 | aiosmtplib → localhost:1025 |
| Mailpit WebUI | 8025 | 8025 | http://localhost:8025 |
| Prometheus | 9090 | 9090 | http://localhost:9090 |
| Grafana | 3000 | 3001 | http://localhost:3001 |
| Ollama | 11434 | 11434 | http://localhost:11434 |

**Note** : Les services internes ne sont accessibles que via le réseau Docker `ent-network` — jamais exposés directement au navigateur.

---

## SLIDE 24 — DÉPLOIEMENT & LANCEMENT

**Fond** : `#F8FAFC`
**Titre** : "Déploiement & Mise en Route"

**Étapes de démarrage** (timeline verticale) :

```
① Clone du repo
   git clone <repo> && cd ent-est-sale-platform

② Configuration (.env optionnel)
   export KEYCLOAK_ADMIN=admin
   export KEYCLOAK_ADMIN_PASSWORD=admin

③ Démarrage de l'infrastructure
   docker compose up -d cassandra rabbitmq keycloak minio redis
   # Attendre healthchecks (~60s)

④ Initialisation automatique
   docker compose up -d keycloak-init cassandra-init minio-init
   # Crée : realm ent-est, keyspace ent_est, buckets MinIO

⑤ Démarrage des services
   docker compose up -d
   # Lance les 25+ services en ordre de dépendance

⑥ Vérification
   docker compose ps           # tous HEALTHY
   curl localhost:8000/health  # {"status":"ok"}

⑦ Accès
   http://localhost:3000        # Interface web
   http://localhost:8080        # Keycloak admin
   http://localhost:3001        # Grafana
   http://localhost:8025        # Mailpit (emails)
   http://localhost:15672       # RabbitMQ Management
```

**Commandes utiles** (carte code sombre, droite) :
```bash
# Voir les logs en direct
docker compose logs -f ms-api-gateway

# Lancer les smoke tests
bash scripts/exam-smoke-test.sh

# Accéder à Cassandra
docker exec -it cassandra cqlsh -u cassandra -p cassandra
USE ent_est;
DESCRIBE TABLES;

# Métriques Prometheus
curl http://localhost:8001/metrics
curl http://localhost:8003/metrics
```

---

## SLIDE 25 — DÉFIS TECHNIQUES & SOLUTIONS

**Fond** : Blanc
**Titre** : "Défis Techniques & Solutions Apportées"

**Grille 3 colonnes de cartes "défi → solution"** :

**Défi 1** :
- Titre : "Initialisation ordonnée des services"
- Problème : Cassandra et Keycloak doivent être prêts avant les microservices
- Solution : Healthchecks Docker + `depends_on: condition: service_healthy` + services init dédiés (keycloak-init, cassandra-init)

**Défi 2** :
- Titre : "Presigned URLs accessibles du navigateur"
- Problème : MinIO interne sur `minio:9000` n'est pas accessible depuis le navigateur
- Solution : 2 clients boto3 : `s3_upload` (interne) + `s3_sign` (endpoint public `localhost:9002`)

**Défi 3** :
- Titre : "WebSocket à travers le gateway"
- Problème : nginx et FastAPI doivent gérer le protocole WebSocket (upgrade HTTP)
- Solution : Configuration nginx `proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade;` + auth JWT via query param `?token=...`

**Défi 4** :
- Titre : "Sécurité du LLM"
- Problème : Risque d'injection de prompts et de fuite de données PII via l'assistant IA
- Solution : 8 patterns regex anti-injection + redaction PII + contexte isolé par rôle + rate limiting 20 req/min

**Défi 5** :
- Titre : "Observabilité distribuée"
- Problème : Corréler les requêtes entre 10 services différents
- Solution : `x-request-id` propagé à travers tous les services + logging JSON structuré + module `runtime.py` partagé

**Défi 6** :
- Titre : "Cohérence des données distribuées"
- Problème : Cassandra ne supporte pas les transactions ACID
- Solution : Modèle d'événements RabbitMQ + eventual consistency + tables dénormalisées adaptées aux patterns de requête

---

## SLIDE 26 — BILAN ET ACQUIS

**Fond** : `#0F172A`
**Titre** : "Bilan du Projet" — blanc

**Trois colonnes** :

**Colonne 1 — Ce que nous avons réalisé** (vert) :
- ✓ 10 microservices Python FastAPI entièrement fonctionnels
- ✓ Authentification OpenID Connect / PKCE avec Keycloak
- ✓ Base de données NoSQL Cassandra (11 tables)
- ✓ Messagerie asynchrone RabbitMQ (13 événements)
- ✓ Stockage objet MinIO avec presigned URLs
- ✓ Chat WebSocket temps réel
- ✓ Assistant IA local (Ollama + LLaMA 3.2)
- ✓ Interface React 19 responsive avec RBAC
- ✓ Observabilité Prometheus + Grafana
- ✓ 8 scripts de smoke tests automatisés

**Colonne 2 — Compétences acquises** (bleu) :
- Architecture microservices en production
- Conteneurisation avancée Docker Compose
- Authentification OAuth2 / OIDC / PKCE
- Bases de données NoSQL distribuées
- Event-driven architecture (EDA)
- Observabilité et métriques
- Sécurité RBAC multi-couche
- CI/CD patterns et smoke tests
- WebSocket temps réel en production

**Colonne 3 — Points d'amélioration** (orange) :
- Déploiement Kubernetes (Helm charts)
- Pipeline CI/CD complet (GitHub Actions)
- Tests d'intégration automatisés (pytest)
- HTTPS/TLS (Let's Encrypt)
- Backup automatique Cassandra
- Monitoring d'alertes (AlertManager)

---

## SLIDE 27 — PERSPECTIVES & ÉVOLUTIONS

**Fond** : Blanc
**Titre** : "Perspectives & Évolutions Futures"

**Roadmap visuelle** (timeline horizontale) :

```
Phase actuelle          Phase 2               Phase 3
(Accompli)              (Prochains mois)      (Long terme)
    │                       │                     │
    ▼                       ▼                     ▼
Docker Compose ──────► Kubernetes (K8s) ──────► Cloud natif
10 services      Helm charts, HPA, PDB    AWS EKS / GKE
RBAC Keycloak    Ingress NGINX TLS        Multi-tenant
Prometheus       AlertManager             SLA 99.9%
Manual deploy    GitHub Actions CI/CD     GitOps (ArgoCD)
```

**6 évolutions techniques** (grille 2×3) :

**Kubernetes** :
- Helm charts pour chaque microservice
- HorizontalPodAutoscaler (HPA)
- PodDisruptionBudget (PDB)

**CI/CD Complet** :
- GitHub Actions : build, test, push image, deploy
- Environnements staging/production
- Rollback automatique

**Sécurité renforcée** :
- mTLS entre services (Istio service mesh)
- Secrets management (HashiCorp Vault)
- HTTPS partout (cert-manager)

**Observabilité avancée** :
- Tracing distribué (Jaeger/OpenTelemetry)
- Log aggregation (Loki)
- Alerting (PagerDuty)

**IA améliorée** :
- Fine-tuning du modèle sur contenus pédagogiques
- RAG (Retrieval Augmented Generation) sur les cours
- Embeddings vectoriels (pgvector/Chroma)

**Fonctionnalités** :
- Application mobile (React Native)
- Visioconférence intégrée (WebRTC)
- Correction automatique par IA

---

## SLIDE 28 — CONCLUSION

**Fond** : `#0F172A` avec motif de points
**Titre** : "Conclusion" — blanc, 44pt

**Citation centrale** (grand texte centré) :
> "ENT EST Salé démontre qu'une équipe de 5 étudiants peut concevoir et déployer une plateforme d'enseignement numérique complète en appliquant les principes DevOps, l'architecture microservices et les meilleures pratiques cloud."

**Trois badges métriques** (centré, grand) :
- **10** Microservices FastAPI
- **25+** Services Docker
- **~6 000** Lignes de code

**Remerciements** (bas, centré) :
- "Merci à notre encadrant pour son accompagnement"
- "EST Salé · Université Mohammed V · Rabat"
- "Filière : Ingénierie des Applications Web et Mobile"
- "Module : DevOps et Cloud · 2024–2025"

**Logo** : GraduationCap centré, 64px, `#2563EB`

---

## SLIDE 29 — QUESTIONS & DISCUSSION

**Fond** : Dégradé bleu primaire (`#2563EB` → `#1E40AF`)
**Contenu** : Centré vertical + horizontal

- Grand "?" en Lucide QuestionMarkCircle — 120px, blanc, semi-transparent
- Texte principal : **"Questions & Discussion"** — 48pt, blanc, bold
- Sous-titre : *"Merci pour votre attention"* — 24pt, `#BFDBFE`
- En bas : noms des 5 membres + encadrant — 16pt, blanc/70%

---

## INSTRUCTIONS SUPPLÉMENTAIRES POUR CLAUDE DESIGN

### Génération du fichier PPTX

1. **Format** : `.pptx`, 16:9, 1920×1080px
2. **Slides de section break** (slides 5, 8, 14, 15, 18, 19, 22) : fond `#0F172A`
3. **Transitions** : Fade (0.3s) entre les slides — sobre et professionnel
4. **Animations** : Apparition des listes en cascade (délai 0.1s par élément) — pas d'animations flashy
5. **Polices de fallback** : si Inter non disponible, utiliser Calibri ou Segoe UI
6. **Hauteur des blocs code** : fond `#1E293B`, padding 12px, coins 8px, police monospace 11-12pt
7. **Tous les tableaux** : en-tête fond `#2563EB` texte blanc, lignes alternées `#F1F5F9`/blanc
8. **Icônes** : SVG Lucide inline ou remplacées par des shapes PowerPoint équivalentes
9. **Les schémas ASCII** : à convertir en vraies formes SmartArt ou shapes PowerPoint avec des connecteurs
10. **Numérotation des slides** : visible sur chaque slide sauf la première et la dernière

### Nomenclature des slides

| N° | Nom court |
|----|-----------|
| 1 | TITRE |
| 2 | SOMMAIRE |
| 3 | CONTEXTE |
| 4 | OVERVIEW |
| 5 | ARCHI GLOBALE |
| 6 | STACK TECH |
| 7 | DOCKER COMPOSE |
| 8 | KEYCLOAK |
| 9 | API GATEWAY |
| 10 | MICROSERVICES OVERVIEW |
| 11 | CASSANDRA |
| 12 | RABBITMQ |
| 13 | MINIO & REDIS |
| 14 | AI ASSISTANT |
| 15 | FORUM WEBSOCKET |
| 16 | FRONTEND ARCH |
| 17 | FRONTEND PAGES |
| 18 | SECURITE RBAC |
| 19 | OBSERVABILITE |
| 20 | TESTS |
| 21 | PATTERNS |
| 22 | FILE TREE |
| 23 | PORTS |
| 24 | DEPLOIEMENT |
| 25 | DEFIS |
| 26 | BILAN |
| 27 | PERSPECTIVES |
| 28 | CONCLUSION |
| 29 | QUESTIONS |
