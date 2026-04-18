#!/usr/bin/env sh
set -eu

KEYCLOAK_BASE="http://keycloak:8080"
REALM_NAME="ent-est"
TOKEN_URL="$KEYCLOAK_BASE/realms/master/protocol/openid-connect/token"
PARTIAL_IMPORT_URL="$KEYCLOAK_BASE/admin/realms/$REALM_NAME/partialImport"
TEMPLATE_FILE="/config/users-partial-import.template.json"
PAYLOAD_FILE="/tmp/users-partial-import.json"

escape_for_sed() {
  printf '%s' "$1" | sed 's/[&|]/\\&/g'
}

ADMIN_PASSWORD_ESCAPED="$(escape_for_sed "${DEV_ADMIN_PASSWORD}")"
TEACHER_PASSWORD_ESCAPED="$(escape_for_sed "${DEV_TEACHER_PASSWORD}")"
STUDENT_PASSWORD_ESCAPED="$(escape_for_sed "${DEV_STUDENT_PASSWORD}")"

sed \
  -e "s|__ADMIN_PASSWORD__|$ADMIN_PASSWORD_ESCAPED|g" \
  -e "s|__TEACHER_PASSWORD__|$TEACHER_PASSWORD_ESCAPED|g" \
  -e "s|__STUDENT_PASSWORD__|$STUDENT_PASSWORD_ESCAPED|g" \
  "$TEMPLATE_FILE" > "$PAYLOAD_FILE"

printf '[keycloak-users-bootstrap] waiting for realm %s...\n' "$REALM_NAME"
for i in $(seq 1 90); do
  if curl -fsS "$KEYCLOAK_BASE/realms/$REALM_NAME" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

printf '[keycloak-users-bootstrap] requesting admin token...\n'
ACCESS_TOKEN=$(curl -fsS -X POST "$TOKEN_URL" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "client_id=admin-cli" \
  --data-urlencode "username=${KEYCLOAK_ADMIN}" \
  --data-urlencode "password=${KEYCLOAK_ADMIN_PASSWORD}" \
  --data-urlencode "grant_type=password" \
  | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')

if [ -z "$ACCESS_TOKEN" ]; then
  printf '[keycloak-users-bootstrap] failed to obtain admin token\n' >&2
  exit 1
fi

printf '[keycloak-users-bootstrap] applying partial import (idempotent)...\n'
HTTP_CODE=$(curl -sS -o /tmp/users-import-response.txt -w '%{http_code}' \
  -X POST "$PARTIAL_IMPORT_URL" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data-binary @"$PAYLOAD_FILE")

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
  printf '[keycloak-users-bootstrap] users bootstrap successful (HTTP %s)\n' "$HTTP_CODE"
  exit 0
fi

printf '[keycloak-users-bootstrap] unexpected HTTP code: %s\n' "$HTTP_CODE" >&2
cat /tmp/users-import-response.txt >&2 || true
exit 1
