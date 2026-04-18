# MS-Course-Access

FastAPI service for student course listing and pre-signed download links.

## Endpoints

- `GET /courses-access/health`
- `GET /courses`
- `GET /courses/{course_id}`
- `POST /courses/{course_id}/download-links`

## Security

- Requires bearer token validated via `ms-auth-core`.
- Default allowed role: `student`.

## Environment variables

- `AUTH_CORE_BASE_URL` (default: `http://ms-auth-core:8000`)
- `COURSE_CONTENT_BASE_URL` (default: `http://ms-course-content:8000`)
- `INTERNAL_API_TOKEN` (default: `dev-internal-token`)
- `COURSE_ACCESS_ALLOWED_ROLES` (default: `student`)
- `MINIO_SIGNING_ENDPOINT` (default: `http://localhost:9002`)
- `MINIO_ROOT_USER` (default: `minio`)
- `MINIO_ROOT_PASSWORD` (default: `ChangeMe_123!`)
- `MINIO_COURSE_BUCKET` (default: `ent-courses`)
