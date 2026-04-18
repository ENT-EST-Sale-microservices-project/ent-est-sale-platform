# MS-Identity-Admin

FastAPI service for admin user provisioning and role assignment.

## Endpoints

- `GET /identity-admin/health`
- `POST /admin/users`
- `PATCH /admin/users/{user_id}/roles`
- `GET /admin/users/{user_id}`
- `GET /admin/users`

## Security

- All endpoints require bearer token validation via `ms-auth-core`.
- Default required role: `admin`.

## Persistence

- User profile metadata is stored in Cassandra table `user_profiles`.
- IAM source of truth remains Keycloak.

## Environment variables

- `AUTH_CORE_BASE_URL` (default: `http://ms-auth-core:8000`)
- `IDENTITY_ADMIN_TIMEOUT_SECONDS` (default: `8`)
- `IDENTITY_ADMIN_ALLOWED_ROLES` (default: `admin`)
- `KEYCLOAK_BASE_URL` (default: `http://keycloak:8080`)
- `KEYCLOAK_REALM` (default: `ent-est`)
- `KEYCLOAK_ADMIN_REALM` (default: `master`)
- `KEYCLOAK_ADMIN` (default: `admin`)
- `KEYCLOAK_ADMIN_PASSWORD` (default: `ChangeMe_123!`)
- `CASSANDRA_CONTACT_POINTS` (default: `cassandra`)
- `CASSANDRA_PORT` (default: `9042`)
- `CASSANDRA_USERNAME` (default: `cassandra`)
- `CASSANDRA_PASSWORD` (default: `ChangeMe_123!`)
- `CASSANDRA_KEYSPACE` (default: `ent_est`)
- `IDENTITY_ADMIN_PROFILE_TABLE` (default: `user_profiles`)
