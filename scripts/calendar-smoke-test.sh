#!/usr/bin/env bash
# Smoke test for MS-Calendar-Schedule via the API Gateway.
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

echo "=== Calendar Smoke Test ==="

TEACHER_TOKEN=$(get_token "${DEV_TEACHER_USER:-teacher1}" "${DEV_TEACHER_PASSWORD:-Teacher_123!}")
ok "Got teacher token"

ADMIN_TOKEN=$(get_token "${DEV_ADMIN_USER:-admin1}" "${DEV_ADMIN_PASSWORD:-Admin_123!}")
ok "Got admin token"

STUDENT_TOKEN=$(get_token "${DEV_STUDENT_USER:-student1}" "${DEV_STUDENT_PASSWORD:-Student_123!}")
ok "Got student token"

# Health check
STATUS=$(curl -sf "${GW}/gateway/health" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
[[ "$STATUS" == "ok" ]] || fail "Gateway health: $STATUS"
ok "Gateway healthy"

# Teacher creates an event
CREATE=$(curl -sf -X POST "${GW}/api/calendar/events" \
  -H "Authorization: Bearer ${TEACHER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "DevOps Lecture Week 1",
    "description": "Introduction to containerization",
    "event_type": "course",
    "start_time": "2026-05-05T09:00:00Z",
    "end_time":   "2026-05-05T11:00:00Z",
    "module_code": "DEV101",
    "target_group": "all"
  }')
EVENT_ID=$(echo "$CREATE" | python3 -c "import sys,json; print(json.load(sys.stdin)['event_id'])")
ok "Teacher created event: ${EVENT_ID}"

# Teacher lists events
LIST=$(curl -sf "${GW}/api/calendar/events" \
  -H "Authorization: Bearer ${TEACHER_TOKEN}")
COUNT=$(echo "$LIST" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
[[ "$COUNT" -ge 1 ]] || fail "Expected >=1 event, got $COUNT"
ok "Event list returned $COUNT event(s)"

# Filter by month
FILTERED=$(curl -sf "${GW}/api/calendar/events?month=2026-05" \
  -H "Authorization: Bearer ${TEACHER_TOKEN}")
FCOUNT=$(echo "$FILTERED" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
[[ "$FCOUNT" -ge 1 ]] || fail "Month filter returned no events"
ok "Month filter OK: $FCOUNT event(s) in 2026-05"

# Get single event
GET=$(curl -sf "${GW}/api/calendar/events/${EVENT_ID}" \
  -H "Authorization: Bearer ${TEACHER_TOKEN}")
TITLE=$(echo "$GET" | python3 -c "import sys,json; print(json.load(sys.stdin)['title'])")
[[ "$TITLE" == "DevOps Lecture Week 1" ]] || fail "Wrong title: $TITLE"
ok "Get event OK: $TITLE"

# Student can read events (not create)
STUDENT_LIST=$(curl -sf "${GW}/api/calendar/events" \
  -H "Authorization: Bearer ${STUDENT_TOKEN}")
ok "Student can list events"

# Student cannot create an event (expect 403)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${GW}/api/calendar/events" \
  -H "Authorization: Bearer ${STUDENT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"title":"hack","description":"x","event_type":"other","start_time":"2026-06-01T10:00:00Z","end_time":"2026-06-01T11:00:00Z"}')
[[ "$HTTP_CODE" == "403" ]] || fail "Student create event expected 403, got $HTTP_CODE"
ok "Student blocked from creating events (403)"

# Teacher patches the event
PATCH=$(curl -sf -X PATCH "${GW}/api/calendar/events/${EVENT_ID}" \
  -H "Authorization: Bearer ${TEACHER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"title": "DevOps Lecture Week 1 (Updated)"}')
PTITLE=$(echo "$PATCH" | python3 -c "import sys,json; print(json.load(sys.stdin)['title'])")
[[ "$PTITLE" == "DevOps Lecture Week 1 (Updated)" ]] || fail "Patch failed: $PTITLE"
ok "PATCH event OK"

# Admin deletes the event
HTTP_DEL=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "${GW}/api/calendar/events/${EVENT_ID}" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}")
[[ "$HTTP_DEL" == "204" ]] || fail "Delete event expected 204, got $HTTP_DEL"
ok "Admin deleted event (204)"

echo ""
echo "=== All calendar tests passed ==="
