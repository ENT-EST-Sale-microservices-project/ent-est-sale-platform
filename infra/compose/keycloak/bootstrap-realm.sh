#!/usr/bin/env sh
set -eu

KEYCLOAK_BASE="http://keycloak:8080"
TOKEN_URL="$KEYCLOAK_BASE/realms/master/protocol/openid-connect/token"
ADMIN_REALMS_URL="$KEYCLOAK_BASE/admin/realms"
REALM_NAME="ent-est"

printf '[keycloak-bootstrap] waiting for keycloak...\n'
for i in $(seq 1 90); do
  if curl -fsS "$KEYCLOAK_BASE/realms/master" >/dev/null 2>&1; then
    break
  fi
  sleep 3
done

printf '[keycloak-bootstrap] requesting admin token...\n'
ACCESS_TOKEN=$(curl -fsS -X POST "$TOKEN_URL" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "client_id=admin-cli" \
  --data-urlencode "username=${KEYCLOAK_ADMIN}" \
  --data-urlencode "password=${KEYCLOAK_ADMIN_PASSWORD}" \
  --data-urlencode "grant_type=password" \
  | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')

if [ -z "$ACCESS_TOKEN" ]; then
  printf '[keycloak-bootstrap] failed to obtain admin token\n' >&2
  exit 1
fi

printf '[keycloak-bootstrap] creating realm %s (idempotent)...\n' "$REALM_NAME"
HTTP_CODE=$(curl -sS -o /tmp/realm-create-response.txt -w '%{http_code}' \
  -X POST "$ADMIN_REALMS_URL" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data-binary @/config/realm.json)

if [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "409" ]; then
  printf '[keycloak-bootstrap] realm bootstrap successful (HTTP %s)\n' "$HTTP_CODE"
  exit 0
fi

printf '[keycloak-bootstrap] unexpected HTTP code: %s\n' "$HTTP_CODE" >&2
cat /tmp/realm-create-response.txt >&2 || true
exit 1
