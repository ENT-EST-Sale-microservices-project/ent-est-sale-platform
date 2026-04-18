# MS-API-Gateway

Minimal API Gateway integrated with `ms-auth-core` for JWT guard.

## Endpoints

- `GET /gateway/health`
- `GET /api/me` (requires bearer token, delegated to `ms-auth-core /auth/me`)
- `GET /api/protected/ping` (requires bearer token)
- `GET /api/protected/admin` (requires valid token with `admin` role)
- `GET /api/protected/teacher` (requires valid token with `teacher` role)
- `GET /api/protected/student` (requires valid token with `student` role)
- `GET /api/protected/academic` (requires one of: `teacher` or `admin`)

### Course content via gateway

- `POST /api/courses` (requires `teacher` or `admin`)
- `POST /api/courses/{course_id}/assets` (requires `teacher` or `admin`)

### Course access via gateway

- `GET /api/courses` (requires `student`)
- `GET /api/courses/{course_id}` (requires `student`)
- `POST /api/courses/{course_id}/download-links` (requires `student`)

### Identity admin via gateway

- `POST /api/admin/users` (requires `admin`)
- `PATCH /api/admin/users/{user_id}/roles` (requires `admin`)
- `GET /api/admin/users/{user_id}` (requires `admin`)
- `GET /api/admin/users` (requires `admin`)

## RBAC behavior

- Missing bearer token ⇒ `401`
- Invalid/expired token ⇒ `401`
- Valid token, but missing required role ⇒ `403`

## Environment variables

- `AUTH_CORE_BASE_URL` (default: `http://ms-auth-core:8000`)
- `GATEWAY_TIMEOUT_SECONDS` (default: `8`)
- `GATEWAY_COURSE_CONTENT_URL` (default: `http://ms-course-content:8000`)
- `GATEWAY_COURSE_ACCESS_URL` (default: `http://ms-course-access:8000`)
- `GATEWAY_IDENTITY_ADMIN_URL` (default: `http://ms-identity-admin:8000`)
