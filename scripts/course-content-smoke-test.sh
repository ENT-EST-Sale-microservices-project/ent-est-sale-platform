#!/usr/bin/env bash
set -euo pipefail

KEYCLOAK_TOKEN_URL="${KEYCLOAK_TOKEN_URL:-http://localhost:8080/realms/ent-est/protocol/openid-connect/token}"
COURSE_CONTENT_BASE_URL="${COURSE_CONTENT_BASE_URL:-http://localhost:8011}"
OIDC_CLIENT_ID="${OIDC_CLIENT_ID:-ent-frontend}"

TEACHER_USER="${COURSE_TEST_TEACHER_USER:-teacher1}"
TEACHER_PASSWORD="${COURSE_TEST_TEACHER_PASSWORD:-Teacher_123!}"
STUDENT_USER="${COURSE_TEST_STUDENT_USER:-student1}"
STUDENT_PASSWORD="${COURSE_TEST_STUDENT_PASSWORD:-Student_123!}"

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

TEACHER_TOKEN="$(get_token "$TEACHER_USER" "$TEACHER_PASSWORD")"
STUDENT_TOKEN="$(get_token "$STUDENT_USER" "$STUDENT_PASSWORD")"

COURSE_ID="$(
  curl -fsS -X POST "$COURSE_CONTENT_BASE_URL/courses" \
    -H 'Content-Type: application/json' \
    -H "Authorization: Bearer $TEACHER_TOKEN" \
    -d '{"title":"DevOps Intro","description":"Week 1 intro","module_code":"DEV101","tags":["devops","intro"],"visibility":"public_class"}' \
    | python3 -c "import sys, json; print(json.load(sys.stdin)['course_id'])"
)"

echo "[PASS] course created: $COURSE_ID"

tmp_file="$(mktemp)"
printf 'sample file for course content smoke test\n' > "$tmp_file"

ASSET_ID="$(
  curl -fsS -X POST "$COURSE_CONTENT_BASE_URL/courses/$COURSE_ID/assets" \
    -H "Authorization: Bearer $TEACHER_TOKEN" \
    -F "file=@$tmp_file;type=text/plain" \
    | python3 -c "import sys, json; print(json.load(sys.stdin)['asset_id'])"
)"

rm -f "$tmp_file"

echo "[PASS] asset uploaded: $ASSET_ID"

student_code="$(curl -s -o /dev/null -w '%{http_code}' -X POST "$COURSE_CONTENT_BASE_URL/courses" -H 'Content-Type: application/json' -H "Authorization: Bearer $STUDENT_TOKEN" -d '{"title":"Forbidden","description":"Forbidden","module_code":"NOPE"}')"
if [ "$student_code" = "403" ]; then
  echo "[PASS] student create course blocked: 403"
else
  echo "[FAIL] student create course expected 403, got $student_code"
  exit 1
fi

echo "[OK] course-content smoke test passed."
