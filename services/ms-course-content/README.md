# MS-Course-Content

FastAPI service for teacher/admin course creation and asset upload to MinIO.

This service stores course and asset metadata in Cassandra.

## Endpoints

- `GET /courses-content/health`
- `POST /courses`
- `POST /courses/{course_id}/assets`
- `GET /courses/{course_id}`

## Security

All write endpoints require a valid bearer token with role `teacher` or `admin`.
Token validation is delegated to `ms-auth-core` (`/auth/me`).

## Environment variables

- `AUTH_CORE_BASE_URL` (default: `http://ms-auth-core:8000`)
- `COURSE_CONTENT_ALLOWED_ROLES` (default: `teacher,admin`)
- `INTERNAL_API_TOKEN` (default: `dev-internal-token`)
- `MINIO_ENDPOINT` (default: `http://minio:9000`)
- `MINIO_ROOT_USER` (default: `minio`)
- `MINIO_ROOT_PASSWORD` (default: `ChangeMe_123!`)
- `MINIO_COURSE_BUCKET` (default: `ent-courses`)
- `CASSANDRA_CONTACT_POINTS` (default: `cassandra`)
- `CASSANDRA_PORT` (default: `9042`)
- `CASSANDRA_USERNAME` (default: `cassandra`)
- `CASSANDRA_PASSWORD` (default: `ChangeMe_123!`)
- `CASSANDRA_KEYSPACE` (default: `ent_est`)
- `COURSE_CONTENT_COURSES_TABLE` (default: `courses`)
- `COURSE_CONTENT_ASSETS_TABLE` (default: `course_assets`)
