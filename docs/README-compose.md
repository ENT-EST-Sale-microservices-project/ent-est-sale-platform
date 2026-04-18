# ENT EST Salé — Docker Compose Stack (Local Dev)

This setup gives you a full local platform for development without Kubernetes.

## Included services

- Keycloak + PostgreSQL
- RabbitMQ (management UI included)
- MinIO + bucket bootstrap
- Cassandra + password/keyspace bootstrap
- Redis (cache/session helper)
- Mailpit (SMTP sandbox for notification testing)
- MS-Auth-Core (JWT validation with Keycloak)
- MS-Identity-Admin (admin user provisioning + role assignment)
- MS-API-Gateway (JWT guard via MS-Auth-Core)
- MS-Course-Content (teacher/admin course creation + MinIO upload)
- MS-Course-Access (student listing + pre-signed download links)
- MS-Notification (RabbitMQ consumer for `user.*` and `course.*` events)
- Frontend (React SPA served via Nginx)

Course metadata persistence:
- `ms-course-content` persists course/asset metadata in Cassandra keyspace `ent_est` by default.

## 1) Prepare environment

```bash
cp .env.compose.example .env.compose
# edit credentials if needed
```

## 2) Start everything

```bash
docker compose --env-file .env.compose up -d --build --wait
```

## 3) Run one-shot initializers (idempotent)

```bash
docker compose --env-file .env.compose up --no-deps keycloak-realm-bootstrap keycloak-users-bootstrap minio-init cassandra-init
```

Default dev users for RBAC tests (realm `ent-est`):

- `admin1` / `Admin_123!`
- `teacher1` / `Teacher_123!`
- `student1` / `Student_123!`

## 4) Useful URLs

- Keycloak: http://localhost:8080
- RabbitMQ UI: http://localhost:15672
- MinIO API: http://localhost:9002
- MinIO Console: http://localhost:9001
- Mailpit UI: http://localhost:8025
- MS-Auth-Core: http://localhost:8010/auth/health
- MS-Identity-Admin: http://localhost:8013/identity-admin/health
- MS-API-Gateway: http://localhost:8008/gateway/health
- MS-Course-Content: http://localhost:8011/courses-content/health
- MS-Course-Access: http://localhost:8012/courses-access/health
- MS-Notification: http://localhost:8014/notifications/health
- Frontend: http://localhost:3000

Protected gateway routes (for example `/api/protected/admin`) return:
- `401` without bearer token
- `403` with valid token but missing `admin` role

RBAC route examples:
- `/api/protected/admin` → requires `admin`
- `/api/protected/teacher` → requires `teacher`
- `/api/protected/student` → requires `student`
- `/api/protected/academic` → requires `teacher` or `admin`
- `/api/admin/users` → requires `admin`

## 5) Stop stack

```bash
docker compose --env-file .env.compose down
```

## 6) Remove containers + volumes

```bash
docker compose --env-file .env.compose down -v
```

## 7) Verify stack health (one command)

```bash
./scripts/compose-healthcheck.sh
```

If your env file is custom:

```bash
ENV_FILE=.env.compose.example ./scripts/compose-healthcheck.sh
```

## 8) Verify RBAC behavior (one command)

```bash
./scripts/rbac-smoke-test.sh
```

Expected result includes:
- `admin -> /admin => 200`
- `teacher -> /admin => 403`
- `teacher -> /teacher => 200`
- `student -> /student => 200`
- `student -> /academic => 403`

## 9) Verify course-content flow (one command)

```bash
./scripts/course-content-smoke-test.sh
```

This verifies:
- teacher can create a course
- teacher can upload an asset
- student is blocked from creating courses (`403`)

## 10) Verify course-access flow (one command)

```bash
./scripts/course-access-smoke-test.sh
```

This verifies:
- student can list courses
- student gets a pre-signed download URL
- pre-signed URL downloads successfully
- teacher is blocked from student-only access APIs (`403`)

Gateway exposes these course routes for frontend integration:
- `POST /api/content/courses`
- `POST /api/content/courses/{course_id}/assets`
- `PUT /api/content/courses/{course_id}`
- `DELETE /api/content/courses/{course_id}/assets/{asset_id}`
- `GET /api/access/courses`
- `GET /api/access/courses/{course_id}`
- `POST /api/access/courses/{course_id}/download-links`

## 11) Verify identity-admin flow (one command)

```bash
./scripts/identity-admin-smoke-test.sh
```

This verifies:
- admin can create a new user
- admin can patch user role
- role persistence is readable via get-user endpoint

## Notes

- This stack is for local development and integration tests.
- Keep Kubernetes manifests for production/staging parity.
- Ports are exposed on localhost for simple service-to-service debugging.
