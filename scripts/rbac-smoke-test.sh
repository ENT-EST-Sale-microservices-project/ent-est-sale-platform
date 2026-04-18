#!/usr/bin/env bash
set -euo pipefail

KEYCLOAK_TOKEN_URL="${KEYCLOAK_TOKEN_URL:-http://localhost:8080/realms/ent-est/protocol/openid-connect/token}"
GATEWAY_BASE_URL="${GATEWAY_BASE_URL:-http://localhost:8008}"
OIDC_CLIENT_ID="${OIDC_CLIENT_ID:-ent-frontend}"

ADMIN_USER="${RBAC_ADMIN_USER:-admin1}"
ADMIN_PASSWORD="${RBAC_ADMIN_PASSWORD:-Admin_123!}"
TEACHER_USER="${RBAC_TEACHER_USER:-teacher1}"
TEACHER_PASSWORD="${RBAC_TEACHER_PASSWORD:-Teacher_123!}"
STUDENT_USER="${RBAC_STUDENT_USER:-student1}"
STUDENT_PASSWORD="${RBAC_STUDENT_PASSWORD:-Student_123!}"

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

http_code() {
  local token="$1"
  local path="$2"
  curl -s -o /dev/null -w '%{http_code}' \
    -H "Authorization: Bearer $token" \
    "$GATEWAY_BASE_URL$path"
}

assert_code() {
  local actual="$1"
  local expected="$2"
  local label="$3"
  if [ "$actual" = "$expected" ]; then
    echo "[PASS] $label => $actual"
  else
    echo "[FAIL] $label => expected $expected, got $actual"
    return 1
  fi
}

ADMIN_TOKEN="$(get_token "$ADMIN_USER" "$ADMIN_PASSWORD")"
TEACHER_TOKEN="$(get_token "$TEACHER_USER" "$TEACHER_PASSWORD")"
STUDENT_TOKEN="$(get_token "$STUDENT_USER" "$STUDENT_PASSWORD")"

status=0

assert_code "$(http_code "$ADMIN_TOKEN" '/api/protected/admin')" "200" "admin -> /admin" || status=1
assert_code "$(http_code "$TEACHER_TOKEN" '/api/protected/admin')" "403" "teacher -> /admin" || status=1
assert_code "$(http_code "$TEACHER_TOKEN" '/api/protected/teacher')" "200" "teacher -> /teacher" || status=1
assert_code "$(http_code "$STUDENT_TOKEN" '/api/protected/student')" "200" "student -> /student" || status=1
assert_code "$(http_code "$STUDENT_TOKEN" '/api/protected/academic')" "403" "student -> /academic" || status=1

if [ "$status" -eq 0 ]; then
  echo "[OK] RBAC smoke test passed."
else
  echo "[ERROR] RBAC smoke test failed."
fi

exit "$status"
