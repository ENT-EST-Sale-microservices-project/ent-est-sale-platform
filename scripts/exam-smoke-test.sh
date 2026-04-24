#!/usr/bin/env bash
# Smoke test for MS-Exam-Assignment via the API Gateway.
set -euo pipefail

ENV_FILE="${ENV_FILE:-.env.compose}"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  set -o allexport; source "$ENV_FILE"; set +o allexport
fi

GW="http://localhost:${MS_API_GATEWAY_PORT:-8008}"
KC="http://localhost:8080"
REALM="${AUTH_REALM:-ent-est}"

ok()  { echo "[OK]  $*"; }
fail(){ echo "[FAIL] $*" >&2; exit 1; }

get_token() {
  local user="$1" pass="$2"
  curl -sf -X POST \
    "${KC}/realms/${REALM}/protocol/openid-connect/token" \
    -d "client_id=ent-frontend" \
    -d "grant_type=password" \
    -d "username=${user}" \
    -d "password=${pass}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])"
}

echo "=== Exam / Assignment Smoke Test ==="

TEACHER_TOKEN=$(get_token "${DEV_TEACHER_USER:-teacher1}" "${DEV_TEACHER_PASSWORD:-Teacher_123!}")
ok "Got teacher token"
STUDENT_TOKEN=$(get_token "${DEV_STUDENT_USER:-student1}" "${DEV_STUDENT_PASSWORD:-Student_123!}")
ok "Got student token"
ADMIN_TOKEN=$(get_token "${DEV_ADMIN_USER:-admin1}" "${DEV_ADMIN_PASSWORD:-Admin_123!}")
ok "Got admin token"

# Gateway health
STATUS=$(curl -sf "${GW}/gateway/health" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
[[ "$STATUS" == "ok" ]] || fail "Gateway health: $STATUS"
ok "Gateway healthy"

# Teacher creates an assignment
DUE="$(date -u -d '+7 days' '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date -u -v+7d '+%Y-%m-%dT%H:%M:%SZ')"
CREATE=$(curl -sf -X POST "${GW}/api/assignments" \
  -H "Authorization: Bearer ${TEACHER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"Docker Lab Report\",
    \"description\": \"Write a report on Docker networking modes.\",
    \"due_date\": \"${DUE}\",
    \"module_code\": \"DEV101\",
    \"max_grade\": 20,
    \"status\": \"published\"
  }")
ASSIGN_ID=$(echo "$CREATE" | python3 -c "import sys,json; print(json.load(sys.stdin)['assignment_id'])")
ok "Teacher created assignment: ${ASSIGN_ID}"

# List assignments — all authenticated users
LIST=$(curl -sf "${GW}/api/assignments" \
  -H "Authorization: Bearer ${STUDENT_TOKEN}")
COUNT=$(echo "$LIST" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
[[ "$COUNT" -ge 1 ]] || fail "Expected >=1 assignment, got $COUNT"
ok "Assignment list returned $COUNT item(s)"

# Filter by module_code
FILTERED=$(curl -sf "${GW}/api/assignments?module_code=DEV101" \
  -H "Authorization: Bearer ${STUDENT_TOKEN}")
FCOUNT=$(echo "$FILTERED" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
[[ "$FCOUNT" -ge 1 ]] || fail "module_code filter returned no results"
ok "module_code filter OK: $FCOUNT item(s)"

# Get single assignment
GET=$(curl -sf "${GW}/api/assignments/${ASSIGN_ID}" \
  -H "Authorization: Bearer ${STUDENT_TOKEN}")
TITLE=$(echo "$GET" | python3 -c "import sys,json; print(json.load(sys.stdin)['title'])")
[[ "$TITLE" == "Docker Lab Report" ]] || fail "Wrong title: $TITLE"
ok "Get assignment OK: $TITLE"

# Student blocked from creating assignments
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${GW}/api/assignments" \
  -H "Authorization: Bearer ${STUDENT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"title":"x","description":"x","due_date":"2026-12-01T00:00:00Z","module_code":"X","max_grade":10,"status":"published"}')
[[ "$HTTP_CODE" == "403" ]] || fail "Student create assignment expected 403, got $HTTP_CODE"
ok "Student blocked from creating assignments (403)"

# Student submits (text-only via multipart form)
SUBMIT=$(curl -sf -X POST "${GW}/api/assignments/${ASSIGN_ID}/submissions" \
  -H "Authorization: Bearer ${STUDENT_TOKEN}" \
  -F "content_text=Bridge mode isolates containers; host mode shares the host network stack.")
SUB_ID=$(echo "$SUBMIT" | python3 -c "import sys,json; print(json.load(sys.stdin)['submission_id'])")
ok "Student submitted assignment: ${SUB_ID}"

# Teacher views all submissions
SUBS=$(curl -sf "${GW}/api/assignments/${ASSIGN_ID}/submissions" \
  -H "Authorization: Bearer ${TEACHER_TOKEN}")
SCOUNT=$(echo "$SUBS" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
[[ "$SCOUNT" -ge 1 ]] || fail "Teacher expected >=1 submission, got $SCOUNT"
ok "Teacher sees $SCOUNT submission(s)"

# Student sees only their own submission
MY_SUBS=$(curl -sf "${GW}/api/assignments/${ASSIGN_ID}/submissions" \
  -H "Authorization: Bearer ${STUDENT_TOKEN}")
MY_COUNT=$(echo "$MY_SUBS" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
[[ "$MY_COUNT" -ge 1 ]] || fail "Student sees no own submissions"
ok "Student sees $MY_COUNT own submission(s)"

# Teacher grades the submission
GRADE=$(curl -sf -X POST "${GW}/api/assignments/${ASSIGN_ID}/submissions/${SUB_ID}/grade" \
  -H "Authorization: Bearer ${TEACHER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"grade": 17.5, "feedback": "Good explanation, missing one edge case."}')
RECEIVED_GRADE=$(echo "$GRADE" | python3 -c "import sys,json; print(json.load(sys.stdin)['grade'])")
[[ "$RECEIVED_GRADE" == "17.5" ]] || fail "Grade expected 17.5, got $RECEIVED_GRADE"
ok "Teacher graded submission: $RECEIVED_GRADE / 20"

# Student sees their grade
GRADED=$(curl -sf "${GW}/api/assignments/${ASSIGN_ID}/submissions" \
  -H "Authorization: Bearer ${STUDENT_TOKEN}")
STUDENT_GRADE=$(echo "$GRADED" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['grade'])")
[[ "$STUDENT_GRADE" == "17.5" ]] || fail "Student grade expected 17.5, got $STUDENT_GRADE"
ok "Student sees grade: $STUDENT_GRADE"

# Grade exceeding max_grade is rejected
HTTP_BAD=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${GW}/api/assignments/${ASSIGN_ID}/submissions/${SUB_ID}/grade" \
  -H "Authorization: Bearer ${TEACHER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"grade": 99, "feedback": "over max"}')
[[ "$HTTP_BAD" == "400" ]] || fail "Over-max grade expected 400, got $HTTP_BAD"
ok "Over-max grade rejected (400)"

echo ""
echo "=== All exam tests passed ==="
