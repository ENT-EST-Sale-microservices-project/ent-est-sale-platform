#!/usr/bin/env bash
set -euo pipefail

KEYCLOAK_TOKEN_URL="${KEYCLOAK_TOKEN_URL:-http://localhost:8080/realms/ent-est/protocol/openid-connect/token}"
COURSE_CONTENT_BASE_URL="${COURSE_CONTENT_BASE_URL:-http://localhost:8011}"
COURSE_ACCESS_BASE_URL="${COURSE_ACCESS_BASE_URL:-http://localhost:8012}"
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

COURSE_JSON="$(
  curl -fsS -X POST "$COURSE_CONTENT_BASE_URL/courses" \
    -H 'Content-Type: application/json' \
    -H "Authorization: Bearer $TEACHER_TOKEN" \
    -d '{"title":"SRE Intro","description":"SRE basics","module_code":"SRE101","tags":["sre"],"visibility":"public_class"}'
)"
COURSE_ID="$(printf '%s' "$COURSE_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin)['course_id'])")"
echo "[PASS] teacher created course: $COURSE_ID"

tmp_file="$(mktemp)"
printf 'course-access smoke test file\n' > "$tmp_file"
ASSET_JSON="$(
  curl -fsS -X POST "$COURSE_CONTENT_BASE_URL/courses/$COURSE_ID/assets" \
    -H "Authorization: Bearer $TEACHER_TOKEN" \
    -F "file=@$tmp_file;type=text/plain"
)"
rm -f "$tmp_file"
ASSET_ID="$(printf '%s' "$ASSET_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin)['asset_id'])")"
echo "[PASS] teacher uploaded asset: $ASSET_ID"

LIST_JSON="$(curl -fsS -H "Authorization: Bearer $STUDENT_TOKEN" "$COURSE_ACCESS_BASE_URL/courses")"
COURSE_PRESENT="$(printf '%s' "$LIST_JSON" | python3 -c "import sys, json; c=json.load(sys.stdin); print('yes' if any(i.get('course_id')=='$COURSE_ID' for i in c) else 'no')")"
if [ "$COURSE_PRESENT" != "yes" ]; then
  echo "[FAIL] student list missing created course"
  exit 1
fi
echo "[PASS] student can list courses"

LINK_JSON="$(curl -fsS -X POST "$COURSE_ACCESS_BASE_URL/courses/$COURSE_ID/download-links" -H 'Content-Type: application/json' -H "Authorization: Bearer $STUDENT_TOKEN" -d "{\"asset_id\":\"$ASSET_ID\"}")"
DOWNLOAD_URL="$(printf '%s' "$LINK_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin)['download_url'])")"
if [ -z "$DOWNLOAD_URL" ]; then
  echo "[FAIL] empty download URL"
  exit 1
fi

echo "[PASS] student got pre-signed download URL"

DL_CODE="$(curl -s -o /dev/null -w '%{http_code}' "$DOWNLOAD_URL")"
if [ "$DL_CODE" != "200" ]; then
  echo "[FAIL] pre-signed URL expected 200, got $DL_CODE"
  exit 1
fi

echo "[PASS] pre-signed URL download works"

TEACHER_LIST_CODE="$(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $TEACHER_TOKEN" "$COURSE_ACCESS_BASE_URL/courses")"
if [ "$TEACHER_LIST_CODE" != "403" ]; then
  echo "[FAIL] teacher list expected 403, got $TEACHER_LIST_CODE"
  exit 1
fi

echo "[PASS] teacher blocked from student access API: 403"
echo "[OK] course-access smoke test passed."
