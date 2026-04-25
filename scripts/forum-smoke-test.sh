#!/usr/bin/env bash
# Smoke test for MS-Forum-Chat REST API via the API Gateway.
# WebSocket is not tested here (requires a WS client); use the frontend for that.
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

echo "=== Forum Smoke Test ==="

STUDENT_TOKEN=$(get_token "${DEV_STUDENT_USER:-student1}" "${DEV_STUDENT_PASSWORD:-Student_123!}")
ok "Got student token"

TEACHER_TOKEN=$(get_token "${DEV_TEACHER_USER:-teacher1}" "${DEV_TEACHER_PASSWORD:-Teacher_123!}")
ok "Got teacher token"

# Health
STATUS=$(curl -sf "${GW}/gateway/health" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
[[ "$STATUS" == "ok" ]] || fail "Gateway health: $STATUS"
ok "Gateway healthy"

# Student creates a thread
CREATE=$(curl -sf -X POST "${GW}/api/forum/threads" \
  -H "Authorization: Bearer ${STUDENT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Question about Docker networking",
    "body": "Can someone explain bridge vs host networking?",
    "module_code": "DEV101"
  }')
THREAD_ID=$(echo "$CREATE" | python3 -c "import sys,json; print(json.load(sys.stdin)['thread_id'])")
ok "Student created thread: ${THREAD_ID}"

# List threads
LIST=$(curl -sf "${GW}/api/forum/threads" \
  -H "Authorization: Bearer ${STUDENT_TOKEN}")
COUNT=$(echo "$LIST" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
[[ "$COUNT" -ge 1 ]] || fail "Expected >=1 thread, got $COUNT"
ok "Thread list returned $COUNT thread(s)"

# Filter by module_code
FILTERED=$(curl -sf "${GW}/api/forum/threads?module_code=DEV101" \
  -H "Authorization: Bearer ${STUDENT_TOKEN}")
FCOUNT=$(echo "$FILTERED" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
[[ "$FCOUNT" -ge 1 ]] || fail "Module filter returned no threads"
ok "module_code filter OK: $FCOUNT thread(s)"

# Get thread detail
DETAIL=$(curl -sf "${GW}/api/forum/threads/${THREAD_ID}" \
  -H "Authorization: Bearer ${STUDENT_TOKEN}")
TITLE=$(echo "$DETAIL" | python3 -c "import sys,json; print(json.load(sys.stdin)['title'])")
[[ "$TITLE" == "Question about Docker networking" ]] || fail "Wrong title: $TITLE"
ok "Get thread detail OK: $TITLE"

# Teacher replies
REPLY=$(curl -sf -X POST "${GW}/api/forum/threads/${THREAD_ID}/messages" \
  -H "Authorization: Bearer ${TEACHER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"body": "Bridge mode creates a virtual network; host mode shares the hosts network stack."}')
MSG_ID=$(echo "$REPLY" | python3 -c "import sys,json; print(json.load(sys.stdin)['message_id'])")
ok "Teacher posted reply: ${MSG_ID}"

# Verify reply count incremented
DETAIL2=$(curl -sf "${GW}/api/forum/threads/${THREAD_ID}" \
  -H "Authorization: Bearer ${STUDENT_TOKEN}")
RC=$(echo "$DETAIL2" | python3 -c "import sys,json; print(json.load(sys.stdin)['reply_count'])")
[[ "$RC" -ge 1 ]] || fail "reply_count expected >=1, got $RC"
ok "reply_count after post: $RC"

# Verify message is in thread detail
MSGS=$(echo "$DETAIL2" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['messages']))")
[[ "$MSGS" -ge 1 ]] || fail "Expected >=1 message in thread, got $MSGS"
ok "Thread has $MSGS message(s)"

# Student posts second reply
curl -sf -X POST "${GW}/api/forum/threads/${THREAD_ID}/messages" \
  -H "Authorization: Bearer ${STUDENT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"body": "Thanks, that makes sense!"}' > /dev/null
ok "Student posted follow-up reply"

# Unauthenticated request is rejected
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${GW}/api/forum/threads")
[[ "$HTTP_CODE" == "401" ]] || fail "Unauthenticated list expected 401, got $HTTP_CODE"
ok "Unauthenticated access blocked (401)"

echo ""
echo "=== All forum tests passed ==="
echo "Note: WebSocket chat is accessible directly at ws://localhost:${MS_FORUM_PORT:-8016}/chat/ws?token=<jwt>&room=<module_code>"
