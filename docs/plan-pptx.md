# Plan de Présentation PowerPoint — ENT EST Salé

## Document pour génération PPTX avec Claude Design

---

# Structure de la Présentation

## Slide 1: Page de Titre

**Titre:** ENT EST Salé — Espace Numérique de Travail
**Sous-titre:** Architecture Microservices avec IA Intégrée
**Institution:** École Supérieure de Technologie de Salé
**Date:** Avril 2026
**Visuel suggéré:** Logo EST Salé + icônes microservices en arrière-plan

---

## Slide 2: Agenda / Sommaire

1. **Contexte & Objectifs**
2. **Architecture Globale**
3. **Stack Technique**
4. **Microservices Détaillés**
5. **Flux de Données**
6. **Sécurité & Authentification**
7. **Frontend & Interface**
8. **Infrastructure Docker**
9. **Conclusion**

---

## Slide 3: Contexte du Projet

**Titre:** Contexte & Objectifs

**Contenu:**
- **Problématique:** Digitalisation de l Espace Numérique de Travail de l EST Salé
- **Solution:** Plateforme microservices moderne avec IA embarquée
- **Bénéfices:**
  - Gestion centralisée utilisateurs
  - Publication collaborative de cours
  - Communication temps réel
  - Assistance IA via chatbot

**Visuel suggéré:** Université EST Salé + diagramme de la transformation digitale

---

## Slide 4: Architecture Microservices — Vue Globale

**Titre:** Architecture Microservices

**Contenu:**
```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND (React)                  │
└─────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│               API GATEWAY (FastAPI)                  │
│              Port 8008 — JWT Guard                  │
└─────────────────────────────────────────────────────┘
                           │
     ┌──────────────────────┼──────────────────────┐
     │                      │                      │
┌────▼────┐  ┌──────────────▼────┐  ┌──────────────▼───┐
│  Auth   │  │   Course Mgmt     │  │   Collaboration   │
│ Core   │  │ Content │ Access  │  │ Notification      │
│ 8010   │  │ 8011    │ 8012    │  │ Calendar Forum    │
└────────┘  └─────────┴──────────┘  │ 8014 8015 8016    │
     │           │                  └───────────────────┘
     │           │                      │
     ▼           ▼                      ▼
┌──────────────────────────────────────────────────────┐
│              INFRASTRUCTURE                          │
│  Keycloak │ Cassandra │ RabbitMQ │ MinIO │ Ollama    │
└──────────────────────────────────────────────────────┘
```

**Visuel suggéré:** Diagramme d architecture en blocs colorés

---

## Slide 5: Stack Technique

**Titre:** Stack Technique

**Tableau:**

| Catégorie | Technologie | Version | Usage |
|-----------|-------------|---------|-------|
| Backend | Python FastAPI | 0.111+ | Microservices |
| Frontend | React + TypeScript | 19.x / 6.x | SPA |
| Database | Apache Cassandra | 5.0 | Métadonnées |
| Storage | MinIO | latest | Fichiers/Cours |
| Messaging | RabbitMQ | 4.1.3 | Events async |
| IAM | Keycloak | 26.1.4 | OAuth2/OIDC |
| AI | Ollama + Llama 3 | latest | Chatbot IA |
| Container | Docker Compose | - | Déploiement |

**Visuel suggéré:** Logos technologiques disposés en grille

---

## Slide 6: MS-Auth-Core

**Titre:** MS-Auth-Core — Authentification JWT

**Contenu:**
- **Rôle:** Validation JWT + extraction identité
- **Port:** 8010
- **Dépendances:** Keycloak (JWKS)

**Endpoints:**
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/auth/health` | GET | Health check |
| `/auth/me` | GET | Retourne claims utilisateur |
| `/auth/introspect` | POST | Introspection token |

**Flux:**
```
Client → Bearer Token → MS-Auth-Core → Keycloak JWKS → Validation → Claims
```

**Visuel suggéré:** Schéma de flux JWT

---

## Slide 7: MS-Identity-Admin

**Titre:** MS-Identity-Admin — Gestion Utilisateurs

**Contenu:**
- **Rôle:** Provisioning utilisateurs + assignation rôles
- **Port:** 8013
- **Rôles:** admin, teacher, student
- **Base:** Cassandra (`user_profiles`)

**Endpoints:**
```
POST /admin/users        — Créer utilisateur
GET  /admin/users        — Lister utilisateurs
GET  /admin/users/{id}   — Détails utilisateur
PATCH /admin/users/{id}/roles — Modifier rôles
```

**Visuel suggéré:** Interface admin avec tableau utilisateurs

---

## Slide 8: MS-Course-Content

**Titre:** MS-Course-Content — Création de Cours

**Contenu:**
- **Rôle:** CRUD cours + upload ressources pédagogiques
- **Port:** 8011
- **Storage:** MinIO (bucket `ent-courses`)
- **Rôles:** teacher, admin

**Endpoints:**
```
GET  /courses           — Liste cours (filtré par teacher)
POST /courses           — Créer cours
POST /courses/{id}/assets — Upload fichier
GET  /courses/{id}      — Détails cours
PUT  /courses/{id}      — Modifier cours
DELETE /courses/{id}    — Supprimer cours
```

**Flux:**
```
Teacher → Upload → Gateway → MS-Course-Content → MinIO + Cassandra → RabbitMQ
```

**Visuel suggéré:** Formulaire upload cours

---

## Slide 9: MS-Course-Access

**Titre:** MS-Course-Access — Accès Étudiant

**Contenu:**
- **Rôle:** Catalogue cours + téléchargement sécurisé
- **Port:** 8012
- **Rôle requis:** student
- **Sécurité:** URLs pré-signées MinIO (TTL 180s)

**Endpoints:**
```
GET  /courses                    — Liste cours disponibles
GET  /courses/{id}               — Détails cours
POST /courses/{id}/download-links — Générer lien signé
```

**Visuel suggéré:** Interface catalogue étudiant

---

## Slide 10: MS-Notification

**Titre:** MS-Notification — Système de Notifications

**Contenu:**
- **Rôle:** Consomme événements RabbitMQ → notifications
- **Port:** 8014
- **Canaux:** Email (SMTP), In-app
- **Consumer:** RabbitMQ (multiples queues)

**Événements consommés:**
```
user.* → Nouvel utilisateur
course.* → Nouveau cours
assignment.* → Devoir publié
grade.* → Note publiée
forum.* → Nouveau message
```

**Visuel suggéré:** Interface notifications avec badges

---

## Slide 11: MS-Calendar-Schedule

**Titre:** MS-Calendar-Schedule — Calendrier Académique

**Contenu:**
- **Rôle:** Événements pédagogiques, emplois du temps
- **Port:** 8015
- **Base:** Cassandra (`calendar_events`)
- **Rôles:** teacher/admin (écriture), all (lecture)

**Endpoints:**
```
POST /calendar/events        — Créer événement
GET  /calendar/events        — Liste (filtrable)
GET  /calendar/events/{id}   — Détails
PATCH /calendar/events/{id}  — Modifier
DELETE /calendar/events/{id} — Supprimer
```

**Visuel suggéré:** Vue calendrier mensuel avec événements

---

## Slide 12: MS-Forum-Chat

**Titre:** MS-Forum-Chat — Forum + Chat Temps Réel

**Contenu:**
- **Rôle:** Discussions + WebSocket chat
- **Port:** 8016
- **Base:** Cassandra (threads, messages, counters)
- **Protocole:** REST + WebSocket

**Endpoints REST:**
```
POST /forum/threads         — Créer fil
GET  /forum/threads         — Liste fils
GET  /forum/threads/{id}   — Détails + messages
POST /forum/threads/{id}/messages — Répondre
```

**WebSocket:**
```
WS /chat/ws?token=JWT&room=MODULE
```

**Visuel suggéré:** Interface forum avec threads et chat bubble

---

## Slide 13: MS-Exam-Assignment

**Titre:** MS-Exam-Assignment — Devoirs & Évaluations

**Contenu:**
- **Rôle:** Publication, soumission, notation
- **Port:** 8017
- **Storage:** MinIO (bucket `ent-uploads`)
- **Base:** Cassandra (assignments, submissions)

**Workflow:**
```
Teacher: Create → Publish
Student: View → Submit (file + text)
Teacher: Grade → Feedback
```

**Endpoints:**
```
POST /assignments                              — Créer devoir
GET  /assignments                              — Lister
POST /assignments/{id}/submissions             — Soumettre
GET  /assignments/{id}/submissions            — Voir soumissions
POST /assignments/{id}/submissions/{sid}/grade — Noter
```

**Visuel suggéré:** Interface devoir avec zone upload et timeline

---

## Slide 14: MS-AI-Assistant

**Titre:** MS-AI-Assistant — Assistant IA (Llama 3)

**Contenu:**
- **Rôle:** Chatbot conversationnel ENT via Ollama
- **Port:** 8018
- **Model:** Llama 3 8B Instruct
- **Sécurité:** Rate limit + Prompt injection detection

**Features:**
```
/ai/chat        — Chat contextuel
/ai/summarize   — Résumé de cours
/ai/faq/generate — Génération FAQ auto
```

**Sécurité:**
- Rate limiting: 20 req/min/user
- Prompt injection: Regex detection
- PII redaction: Logs sans données sensibles
- Audit: Tous prompts loggés

**Visuel suggéré:** Interface chat avec bubbles AI + icône Sparkles

---

## Slide 15: Flux Event-Driven

**Titre:** Communication Asynchrone (RabbitMQ)

**Diagramme:**
```
┌──────────────┐       ┌───────────────────┐       ┌───────────────┐
│ Producers    │       │ Exchange Topic    │       │ Consumers     │
├──────────────┤       │ ent.events.topic │       ├───────────────┤
│ Course Mgmt  │──────▶│                   │─────▶│ Notification  │
│ Exam Service │       │ Routing:          │       │ AI Assistant  │
│ Forum Chat   │       │ user.*            │       │               │
│ Calendar     │       │ course.*          │       │               │
└──────────────┘       │ assignment.*      │       └───────────────┘
                       │ forum.*           │
                       └───────────────────┘
```

**Queue Bindings:**
- `q.notification.*` → MS-Notification
- `q.ai.context` → MS-AI-Assistant

**Visuel suggéré:** Flux RabbitMQ avec producteurs et consommateurs

---

## Slide 16: Sécurité & Authentification

**Titre:** Sécurité Multi-Couches

**Couches:**

1. **Réseau**
   - TLS intra-plateforme
   - CORS configuré

2. **Application**
   - JWT RS256 validation
   - RBAC (rôles: admin/teacher/student)
   - Rate limiting

3. **Données**
   - Secrets via env vars
   - Encryption at rest (MinIO)

4. **Audit**
   - Correlation ID
   - Structured JSON logs
   - PII redaction

**Demo Credentials:**
| User | Password | Role |
|------|----------|------|
| admin | Admin_123! | admin |
| teacher | Teacher_123! | teacher |
| student | Student_123! | student |

**Visuel suggéré:** Schéma sécurité avec замок icônes

---

## Slide 17: Frontend — Structure

**Titre:** Frontend React SPA

**Architecture:**
```
src/
├── main.tsx              # Entry point
├── App.tsx               # Routes (React Router)
├── components/
│   ├── app-shell.tsx     # Layout (sidebar + header)
│   └── ui/               # shadcn/ui components
├── context/
│   ├── auth-context.tsx  # Auth + apiFetch
│   └── theme-context.tsx # Dark/Light mode
├── lib/
│   └── auth.ts           # Keycloak integration
└── pages/
    ├── login-page.tsx
    ├── dashboard-page.tsx
    ├── admin-page.tsx
    ├── teacher-page.tsx
    ├── student-page.tsx
    ├── calendar-page.tsx
    ├── forum-page.tsx
    ├── exam-page.tsx
    ├── assistant-page.tsx
    └── notifications-page.tsx
```

**Routes:**
```
/login → Login
/app   → Dashboard (protégé)
/app/admin     → Admin only
/app/teacher   → Teacher only
/app/student    → Student only
/app/*          → All authenticated
```

**Visuel suggéré:** Wireframes des pages principales

---

## Slide 18: Infrastructure Docker Compose

**Titre:** Infrastructure Docker

**Services:**

| Service | Image | Ports |
|---------|-------|-------|
| Keycloak | keycloak:26.1.4 | 8080 |
| PostgreSQL | postgres:16 | 5432 |
| RabbitMQ | rabbitmq:4.1.3 | 5672, 15672 |
| MinIO | quay.io/minio/minio | 9000, 9001 |
| Cassandra | cassandra:5.0 | 9042 |
| Redis | redis:7-alpine | 6379 |
| Ollama | ollama/ollama | 11434 |
| Prometheus | prom/prometheus | 9090 |
| Grafana | grafana/grafana | 3001 |

**Commandes:**
```bash
# Standard
docker compose up -d

# Avec IA
docker compose --profile ai up -d
```

**Visuel suggéré:** Diagramme Docker containers

---

## Slide 19: Ports et URLs d'Accès

**Titre:** Points d'Accès

**Tableau:**

| Service | URL | Default Creds |
|---------|-----|---------------|
| Frontend | http://localhost:3000 | - |
| Keycloak Admin | http://localhost:8080/admin | admin / ChangeMe_123! |
| API Gateway | http://localhost:8008 | - |
| RabbitMQ MQ | http://localhost:15672 | ent / ChangeMe_123! |
| MinIO Console | http://localhost:9001 | minio / ChangeMe_123! |
| Grafana | http://localhost:3001 | admin / ChangeMe_123! |
| Prometheus | http://localhost:9090 | - |
| Mailpit UI | http://localhost:8025 | - |
| Ollama API | http://localhost:11434 | - |

**Visuel suggéré:** Dashboard unifié avec captures d'écrans des interfaces

---

## Slide 20: Déploiement & CI/CD

**Titre:** Déploiement & Intégration Continue

**CI/CD Pipeline:**
```
Push → GitHub Actions → Tests → Build Docker → Push to Registry → Deploy K8s
```

**Environnements:**
- Dev: Docker Compose local
- Stage: Kubernetes (helm)
- Prod: Cloud privé (VMware ESXi)

**Workflows:**
- `app-ci.yml` — Test et build microservices
- `infra-ci.yml` — Validation infrastructure

**Visuel suggéré:** Pipeline CI/CD diagram

---

## Slide 21: Schéma Global de Communication

**Titre:** Communication Inter-Services

**Communication Synchrone (REST):**
```
Frontend → Gateway → MS-Auth-Core → Keycloak
                ↘
                 → MS-Course-Content → Cassandra/MinIO
                ↘
                 → MS-AI-Assistant → Ollama
```

**Communication Asynchrone (AMQP):**
```
Services → RabbitMQ Exchange → Queues → Consumers
```

**Visuel suggéré:** Mermaid diagram du flux complet

---

## Slide 22: Screenshot — Dashboard

**Titre:** Interface — Dashboard

**Description:** Vue d'ensemble avec statistiques par rôle

**Éléments:**
- Sidebar navigation (Dashboard, AI Assistant, Admin, etc.)
- Header avec user menu + notifications
- Zone stats: cours, devoirs, notifications
- Quick actions: Créer cours, voir forum, etc.

**Visuel suggéré:** Capture d'écran réelle du dashboard

---

## Slide 23: Screenshot — AI Assistant

**Titre:** Interface — Assistant IA

**Description:** Chatbot conversationnel intégré

**Éléments:**
- Header avec statut Ollama (Online/Offline)
- Zone chat avec bulles user/assistant
- Input message avec bouton send
- Bouton clear chat

**Visuel suggéré:** Capture d'écran de l'AI Assistant

---

## Slide 24: Conclusion

**Titre:** Conclusion

**Résumé:**
- ✅ 9 microservices opérationnels
- ✅ Authentification JWT centralisée
- ✅ Base de données distribuée (Cassandra)
- ✅ Stockage objet sécurisé (MinIO)
- ✅ Messaging asynchrone (RabbitMQ)
- ✅ IA embarquée (Ollama/Llama 3)
- ✅ Interface React moderne
- ✅ Déploiement Docker Compose / Kubernetes

**Perspectives:**
- Déploiement Kubernetes complet
- Optimisation performances
- Ajout更多的 modules (bibliothèque, notes)

**Visuel suggéré:** Summary card avec checkmarks verts

---

## Slide 25: Questions

**Titre:** Questions ?

**Contenu:**
- Merci de votre attention
- Contact: [email institution]
- Documentation: [liens]

**Visuel suggéré:** Image de fin avec icône question mark ou groupe de discussion

---

# Notes pour Claude Design

## Design Guidelines

### Color Palette
- **Primary:** Violet/Purple gradient (correspond à l'UI existante)
- **Secondary:** Blue/Teal
- **Accent:** Green pour succès, Red pour erreurs
- **Background:** Light mode / Dark mode support

### Typography
- **Headings:** Sans-serif bold (Inter or Geist)
- **Body:** Sans-serif regular
- **Code:** Monospace

### Iconography
- Utiliser Lucide React icons (cf. frontend)
- Ex: GraduationCap, Sparkles, Shield, MessageSquare, etc.

### Layout
- Slides 16:9
- Header avec titre + numéro slide
- Footer optionnel avec logo

### Visual Elements
- Diagrammes architecture (Mermaid style)
- Tableaux pour données structurées
- Icônes pour points clés
- Badges pour statuts

## Sections à Détailler

1. Chaque slide "microservices" devrait avoir:
   - Bloc coloré (icône + titre)
   - Liste des endpoints
   - Diagramme de flux simple

2. Slides infrastructure:
   - Tableaux清晰
   - URLs mises en évidence

3. Slides screenshots:
   - Placeholder avec description détaillée
   - Bullet points des éléments UI

## Suggestions Visuelles

| Slide | Type Visuel |
|-------|-------------|
| Architecture | Diagramme en blocs |
| Stack | Grille logos |
| Microservices | Cards avec icônes |
| Flux | Flowchart horizontal |
| Sécurité | Schéma с замками |
| Docker | Containers diagram |
| UI Screenshots | Mockup frames |
| Conclusion | Summary cards |