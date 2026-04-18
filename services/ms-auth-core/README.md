# MS-Auth-Core

FastAPI service for JWT verification and identity extraction with Keycloak.

## Endpoints

- `GET /auth/health`
- `GET /auth/me` (requires `Authorization: Bearer <token>`)
- `POST /auth/introspect`

## Environment variables

- `AUTH_REALM` (default: `ent-est`)
- `AUTH_ISSUER` (default: `http://localhost:8080/realms/ent-est`)
- `AUTH_JWKS_URL` (default: `http://keycloak:8080/realms/ent-est/protocol/openid-connect/certs`)
- `AUTH_AUDIENCE` (default: `ent-gateway,ent-frontend`; comma-separated accepted audiences)
- `AUTH_VERIFY_AUDIENCE` (default: `true`)
