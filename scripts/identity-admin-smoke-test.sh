#!/usr/bin/env bash
set -euo pipefail

KEYCLOAK_TOKEN_URL="${KEYCLOAK_TOKEN_URL:-http://localhost:8080/realms/ent-est/protocol/openid-connect/token}"
GATEWAY_BASE_URL="${GATEWAY_BASE_URL:-http://localhost:8008}"
OIDC_CLIENT_ID="${OIDC_CLIENT_ID:-ent-frontend}"

ADMIN_USER="${RBAC_ADMIN_USER:-admin1}"
ADMIN_PASSWORD="${RBAC_ADMIN_PASSWORD:-Admin_123!}"

get_token() {
  local username="$1"
  local password="$2"

  curl -fsS -X POST "$KEYCLOAK_TOKEN_URL" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    --data-urlencode "client_id=$OIDC_CLIENT_ID" \
    --data-urlencode 'grant_type=password' \
    --data-urlencode "username=$username" \
    --data-urlencode "password=$password" \
    | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])"
}

ADMIN_TOKEN="$(get_token "$ADMIN_USER" "$ADMIN_PASSWORD")"

SUFFIX="$(date +%s)"
NEW_USER="student_smoke_$SUFFIX"
NEW_EMAIL="$NEW_USER@example.local"

CREATE_JSON="$(
  curl -fsS -X POST "$GATEWAY_BASE_URL/api/admin/users" \
    -H 'Content-Type: application/json' \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -d "{\"username\":\"$NEW_USER\",\"email\":\"$NEW_EMAIL\",\"first_name\":\"Smoke\",\"last_name\":\"Student\",\"password\":\"Student_123!\",\"roles\":[\"student\"],\"enabled\":true}"
)"

USER_ID="$(printf '%s' "$CREATE_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin)['user_id'])")"
if [ -z "$USER_ID" ]; then
  echo "[FAIL] identity-admin create user did not return user_id"
  exit 1
fi
echo "[PASS] admin created user: $USER_ID"

PATCH_JSON="$(
  curl -fsS -X PATCH "$GATEWAY_BASE_URL/api/admin/users/$USER_ID/roles" \
    -H 'Content-Type: application/json' \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -d '{"roles":["teacher"]}'
)"

ROLE="$(printf '%s' "$PATCH_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('role'))")"
if [ "$ROLE" != "teacher" ]; then
  echo "[FAIL] expected role teacher after patch, got '$ROLE'"
  exit 1
fi
echo "[PASS] admin patched roles to teacher"

GET_ROLE="$(
  curl -fsS -H "Authorization: Bearer $ADMIN_TOKEN" "$GATEWAY_BASE_URL/api/admin/users/$USER_ID" \
    | python3 -c "import sys, json; print(json.load(sys.stdin).get('role'))"
)"
if [ "$GET_ROLE" != "teacher" ]; then
  echo "[FAIL] get user expected role teacher, got '$GET_ROLE'"
  exit 1
fi
echo "[PASS] admin get user returns persisted role"

echo "[OK] identity-admin smoke test passed."
