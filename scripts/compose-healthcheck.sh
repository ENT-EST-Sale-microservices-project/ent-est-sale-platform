#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT_DIR/docker-compose.yml}"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env.compose}"

if ! command -v docker >/dev/null 2>&1; then
  echo "[ERROR] Docker is not installed or not in PATH"
  exit 1
fi

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "[ERROR] Compose file not found: $COMPOSE_FILE"
  exit 1
fi

if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
  COMPOSE=(docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE")
else
  echo "[WARN] ENV file not found ($ENV_FILE). Using defaults from compose file."
  COMPOSE=(docker compose -f "$COMPOSE_FILE")
fi

pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; return 1; }

status=0

required_services=(
  postgres-keycloak
  keycloak
  ms-auth-core
  ms-identity-admin
  ms-api-gateway
  ms-course-content
  ms-course-access
  ms-notification
  rabbitmq
  minio
  cassandra
  redis
  mailpit
)

running_services="$(${COMPOSE[@]} ps --status running --services || true)"
for svc in "${required_services[@]}"; do
  if echo "$running_services" | grep -qx "$svc"; then
    pass "service '$svc' is running"
  else
    fail "service '$svc' is not running" || status=1
  fi
done

check_http() {
  local name="$1"
  local url="$2"
  if curl -fsS --max-time 8 "$url" >/dev/null; then
    pass "$name reachable: $url"
  else
    fail "$name unreachable: $url" || status=1
  fi
}

check_http "Keycloak" "http://localhost:8080/realms/master"
check_http "MS-Auth-Core" "http://localhost:8010/auth/health"
check_http "MS-Identity-Admin" "http://localhost:8013/identity-admin/health"
check_http "MS-API-Gateway" "http://localhost:8008/gateway/health"
check_http "MS-Course-Content" "http://localhost:8011/courses-content/health"
check_http "MS-Course-Access" "http://localhost:8012/courses-access/health"
check_http "MS-Notification" "http://localhost:8014/notifications/health"
check_http "RabbitMQ UI" "http://localhost:15672/"
check_http "MinIO API" "http://localhost:9002/minio/health/live"
check_http "Mailpit UI" "http://localhost:8025/"

check_init_exit_zero() {
  local container="$1"
  local label="$2"
  if ! docker ps -a --format '{{.Names}}' | grep -qx "$container"; then
    fail "$label container missing: $container" || status=1
    return
  fi

  local code
  code="$(docker inspect "$container" --format '{{.State.ExitCode}}' 2>/dev/null || echo 999)"
  if [ "$code" = "0" ]; then
    pass "$label completed successfully"
  else
    fail "$label failed with exit code $code" || status=1
  fi
}

check_init_exit_zero "ent-keycloak-bootstrap" "Keycloak realm bootstrap"
check_init_exit_zero "ent-keycloak-users-bootstrap" "Keycloak users bootstrap"
check_init_exit_zero "ent-minio-init" "MinIO init"
check_init_exit_zero "ent-cassandra-init" "Cassandra init"

if [ "$status" -eq 0 ]; then
  echo "[OK] Compose platform health checks passed."
else
  echo "[ERROR] One or more checks failed."
fi

exit "$status"
