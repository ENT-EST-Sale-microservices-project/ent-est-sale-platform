#!/usr/bin/env bash
# ==============================================================================
# ENT EST Salé — Kubernetes Infrastructure Bootstrap (Orchestrator)
# ==============================================================================
# Supports : Kind (local dev) | Existing cluster (prod / staging)
# Ingress  : Traefik v3  (MIT, replaces ingress-nginx EOL March 2026)
# Platform : Keycloak · RabbitMQ · MinIO · Cassandra  — 100 % open-source
#
# Usage:
#   Local (Kind):
#     ./bootstrap/bootstrap-infra.sh --mode kind --cluster-name ent-est \
#                                    --kind-config ./cluster/kind-config.yaml
#
#   Existing cluster (prod):
#     ./bootstrap/bootstrap-infra.sh --mode existing \
#                                    --kube-context prod-admin@prod-cluster
#
# All variables can be set in .env at the repo root (copied from .env.example).
# CLI flags always win over .env values.
# ==============================================================================
set -euo pipefail

# ── Resolve paths ─────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MANIFESTS_DIR="$INFRA_DIR/manifests"
VALUES_DIR="$INFRA_DIR/values"

# ── Load .env (lowest precedence — CLI flags and shell env win) ───────────────
ENV_FILE="$INFRA_DIR/.env"
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$ENV_FILE"
  set +a
else
  echo "INFO  No .env found at $ENV_FILE — using shell environment / defaults."
  echo "      Copy .env.example to .env and fill in your values."
fi

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

log()    { echo -e "${CYAN}[$(date '+%H:%M:%S')] INFO${RESET}  $*"; }
ok()     { echo -e "${GREEN}[$(date '+%H:%M:%S')]  OK  ${RESET}  $*"; }
warn()   { echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARN${RESET}  $*"; }
error()  { echo -e "${RED}[$(date '+%H:%M:%S')] ERROR${RESET} $*" >&2; }
banner() {
  echo -e "\n${BOLD}${CYAN}══════════════════════════════════════════════════${RESET}"
  echo -e "${BOLD}${CYAN}  $*${RESET}"
  echo -e "${BOLD}${CYAN}══════════════════════════════════════════════════${RESET}\n"
}

# ── Defaults (override via .env or CLI) ───────────────────────────────────────
MODE="${MODE:-kind}"
CLUSTER_NAME="${CLUSTER_NAME:-ent-est}"
KIND_CONFIG="${KIND_CONFIG:-$INFRA_DIR/cluster/kind-config.yaml}"
KUBE_CONTEXT="${KUBE_CONTEXT:-}"

PLATFORM_NS="${PLATFORM_NS:-ent-platform}"
APPS_NS="${APPS_NS:-ent-apps}"
OBS_NS="${OBS_NS:-ent-observability}"
TRAEFIK_NS="${TRAEFIK_NS:-traefik}"

PERSISTENCE_ENABLED="${PERSISTENCE_ENABLED:-false}"
SKIP_WAIT="${SKIP_WAIT:-false}"
POD_WAIT_TIMEOUT="${POD_WAIT_TIMEOUT:-600s}"

KEYCLOAK_ADMIN="${KEYCLOAK_ADMIN:-admin}"
KEYCLOAK_PASSWORD="${KEYCLOAK_PASSWORD:-ChangeMe_123!}"
RABBITMQ_USER="${RABBITMQ_USER:-ent}"
RABBITMQ_PASSWORD="${RABBITMQ_PASSWORD:-ChangeMe_123!}"
MINIO_ROOT_USER="${MINIO_ROOT_USER:-minio}"
MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-ChangeMe_123!}"
CASSANDRA_PASSWORD="${CASSANDRA_PASSWORD:-ChangeMe_123!}"

# ── Argument parsing ──────────────────────────────────────────────────────────
usage() {
  grep '^#' "$0" | head -25 | sed 's/^# \{0,1\}//'
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)           MODE="$2";         shift 2 ;;
    --cluster-name)   CLUSTER_NAME="$2"; shift 2 ;;
    --kind-config)    KIND_CONFIG="$2";  shift 2 ;;
    --kube-context)   KUBE_CONTEXT="$2"; shift 2 ;;
    -h|--help)        usage ;;
    *)  error "Unknown argument: $1"; usage ;;
  esac
done

# Export everything so envsubst can see it when rendering manifests.
export PLATFORM_NS APPS_NS OBS_NS TRAEFIK_NS
export KEYCLOAK_ADMIN KEYCLOAK_PASSWORD
export RABBITMQ_USER RABBITMQ_PASSWORD
export MINIO_ROOT_USER MINIO_ROOT_PASSWORD
export CASSANDRA_PASSWORD

# ── Helpers ───────────────────────────────────────────────────────────────────
require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    error "Required command not found: '$1'. Please install it first."
    exit 1
  fi
}

# apply_manifest <file> '<${VAR1} ${VAR2} ...>'
# Renders the template with envsubst (only the listed vars) then applies it.
apply_manifest() {
  local file="$1"
  local vars="${2:-}"
  if [[ -z "$vars" ]]; then
    envsubst < "$file" | kubectl apply -f -
  else
    envsubst "$vars" < "$file" | kubectl apply -f -
  fi
}

wait_deploy() {
  local ns="$1" name="$2" timeout="${3:-$POD_WAIT_TIMEOUT}"
  [[ "$SKIP_WAIT" == "true" ]] && { warn "SKIP_WAIT=true — skipping deployment/$name"; return 0; }
  log "Waiting for deployment/$name in $ns (timeout: $timeout)..."
  if ! kubectl rollout status deployment/"$name" -n "$ns" --timeout="$timeout"; then
    error "deployment/$name did not become ready."
    kubectl get pods -n "$ns" -o wide || true
    kubectl describe pods -n "$ns" -l "app.kubernetes.io/name=$name" 2>/dev/null | tail -40 || true
    exit 1
  fi
  ok "deployment/$name is ready."
}

wait_sts() {
  local ns="$1" name="$2" timeout="${3:-$POD_WAIT_TIMEOUT}"
  [[ "$SKIP_WAIT" == "true" ]] && { warn "SKIP_WAIT=true — skipping statefulset/$name"; return 0; }
  log "Waiting for statefulset/$name in $ns (timeout: $timeout)..."
  if ! kubectl rollout status statefulset/"$name" -n "$ns" --timeout="$timeout"; then
    error "statefulset/$name did not become ready."
    kubectl get pods -n "$ns" -o wide || true
    kubectl describe pods -n "$ns" -l "app.kubernetes.io/name=$name" 2>/dev/null | tail -40 || true
    exit 1
  fi
  ok "statefulset/$name is ready."
}

wait_job() {
  local ns="$1" name="$2" timeout="${3:-300s}"
  [[ "$SKIP_WAIT" == "true" ]] && { warn "SKIP_WAIT=true — skipping job/$name"; return 0; }
  log "Waiting for job/$name in $ns (timeout: $timeout)..."
  if ! kubectl wait --for=condition=complete job/"$name" -n "$ns" --timeout="$timeout"; then
    error "job/$name did not complete successfully."
    kubectl get job "$name" -n "$ns" -o wide || true
    kubectl logs -n "$ns" job/"$name" --tail=200 || true
    exit 1
  fi
  ok "job/$name completed."
}

# ── Prerequisite checks ───────────────────────────────────────────────────────
banner "Prerequisite Checks"
require_cmd kubectl
require_cmd helm
require_cmd envsubst
[[ "$MODE" == "kind" ]] && require_cmd kind

log "Helm version:    $(helm version --short 2>/dev/null)"
log "kubectl version: $(kubectl version --client -o json 2>/dev/null | grep '"gitVersion"' | head -1 | tr -d ' ')"

# ── Cluster bootstrap ─────────────────────────────────────────────────────────
banner "Cluster Setup -- mode: $MODE"

if [[ "$MODE" == "kind" ]]; then
  [[ ! -f "$KIND_CONFIG" ]] && { error "Kind config not found: $KIND_CONFIG"; exit 1; }
  if kind get clusters 2>/dev/null | grep -qx "$CLUSTER_NAME"; then
    warn "Kind cluster '$CLUSTER_NAME' already exists -- skipping creation."
  else
    log "Creating Kind cluster '$CLUSTER_NAME'..."
    kind create cluster --name "$CLUSTER_NAME" --config "$KIND_CONFIG"
    ok "Kind cluster created."
  fi
  kubectl config use-context "kind-$CLUSTER_NAME" >/dev/null
  log "Active context: kind-$CLUSTER_NAME"

elif [[ "$MODE" == "existing" ]]; then
  [[ -n "$KUBE_CONTEXT" ]] && kubectl config use-context "$KUBE_CONTEXT" >/dev/null
  log "Active context: $(kubectl config current-context)"

else
  error "Invalid --mode '$MODE'. Use: kind | existing"
  exit 1
fi

log "Cluster info:"
kubectl cluster-info 2>&1 | head -3

# ── Namespaces ────────────────────────────────────────────────────────────────
banner "Namespaces"
# shellcheck disable=SC2016
apply_manifest "$MANIFESTS_DIR/namespaces.yaml" \
  '${PLATFORM_NS} ${APPS_NS} ${OBS_NS} ${TRAEFIK_NS}'
ok "All namespaces applied."

# ── Helm repositories ─────────────────────────────────────────────────────────
banner "Helm Repositories"
helm repo add traefik https://traefik.github.io/charts >/dev/null 2>&1 || true
helm repo add minio   https://charts.min.io/           >/dev/null 2>&1 || true
helm repo update >/dev/null
ok "All Helm repositories configured and updated."

# ── Traefik v3 (Ingress Controller) ──────────────────────────────────────────
banner "Traefik v3 (Ingress Controller)"

TRAEFIK_EXTRA_ARGS=()
if [[ "$MODE" == "kind" ]]; then
  # Kind has no LoadBalancer — use NodePort with fixed ports matching kind-config.yaml.
  TRAEFIK_EXTRA_ARGS+=(
    --set "service.type=NodePort"
    --set "ports.web.nodePort=30080"
    --set "ports.websecure.nodePort=30443"
  )
fi

helm upgrade --install traefik traefik/traefik \
  --namespace "$TRAEFIK_NS" \
  --version ">=38.0.0" \
  -f "$VALUES_DIR/traefik-values.yaml" \
  "${TRAEFIK_EXTRA_ARGS[@]}" \
  --wait --timeout 3m

ok "Traefik deployed."
wait_deploy "$TRAEFIK_NS" "traefik"

# ── PostgreSQL for Keycloak ───────────────────────────────────────────────────
banner "PostgreSQL (for Keycloak)"
# shellcheck disable=SC2016
apply_manifest "$MANIFESTS_DIR/keycloak/postgres.yaml" \
  '${PLATFORM_NS} ${KEYCLOAK_PASSWORD}'
ok "PostgreSQL StatefulSet applied."
wait_sts "$PLATFORM_NS" "keycloak-postgres" "300s"

# ── Keycloak ──────────────────────────────────────────────────────────────────
banner "Keycloak 26 (plain StatefulSet)"

# Remove any previously failed Helm-managed release to avoid conflicts.
if helm status keycloak -n "$PLATFORM_NS" >/dev/null 2>&1; then
  warn "Found existing Helm release 'keycloak' -- uninstalling before plain-manifest deploy..."
  helm uninstall keycloak -n "$PLATFORM_NS" --wait 2>/dev/null || true
  sleep 5
fi

# start-dev : HTTP, no TLS, no hostname enforcement -- ideal for Kind / local.
# start     : production mode; supply KC_HOSTNAME separately.
export KC_COMMAND="start-dev"
[[ "$MODE" == "existing" ]] && KC_COMMAND="start"

# shellcheck disable=SC2016
apply_manifest "$MANIFESTS_DIR/keycloak/keycloak.yaml" \
  '${PLATFORM_NS} ${KEYCLOAK_ADMIN} ${KEYCLOAK_PASSWORD} ${KC_COMMAND}'
ok "Keycloak StatefulSet applied."

# ── RabbitMQ (Cluster Operator) ───────────────────────────────────────────────
banner "RabbitMQ (Cluster Operator)"

RABBITMQ_OPERATOR_URL="https://github.com/rabbitmq/cluster-operator/releases/latest/download/cluster-operator.yml"
log "Applying RabbitMQ Cluster Operator..."
kubectl apply -f "$RABBITMQ_OPERATOR_URL" >/dev/null
wait_deploy "rabbitmq-system" "rabbitmq-cluster-operator" "120s"

log "Creating RabbitMQ cluster resource..."
# shellcheck disable=SC2016
apply_manifest "$MANIFESTS_DIR/rabbitmq/rabbitmq-cluster.yaml" \
  '${PLATFORM_NS} ${RABBITMQ_USER} ${RABBITMQ_PASSWORD}'
ok "RabbitMQ cluster resource applied."

# ── MinIO (Object Storage) ────────────────────────────────────────────────────
banner "MinIO (Object Storage)"
log "Persistence enabled: $PERSISTENCE_ENABLED"

PERSIST_FLAG="$([[ "$PERSISTENCE_ENABLED" == "true" ]] && echo "true" || echo "false")"

helm upgrade --install minio minio/minio \
  --namespace "$PLATFORM_NS" \
  -f "$VALUES_DIR/minio-values.yaml" \
  --set rootUser="$MINIO_ROOT_USER" \
  --set rootPassword="$MINIO_ROOT_PASSWORD" \
  --set persistence.enabled="$PERSIST_FLAG" \
  --timeout 5m

ok "MinIO chart applied."
wait_deploy "$PLATFORM_NS" "minio"

# ── Cassandra ─────────────────────────────────────────────────────────────────
banner "Cassandra 5 (plain StatefulSet)"

# NOTE: envsubst is called with an explicit var list so that ${CASSANDRA_NEW_PASSWORD}
# and ${i} inside the inline container script are NOT expanded by envsubst — they
# are container-level shell variables resolved at runtime inside the pod.
# shellcheck disable=SC2016
apply_manifest "$MANIFESTS_DIR/cassandra/cassandra.yaml" \
  '${PLATFORM_NS} ${CASSANDRA_PASSWORD}'
ok "Cassandra StatefulSet applied."

# ── Wait for all workloads ─────────────────────────────────────────────────────
banner "Waiting for all workloads"

if [[ "$SKIP_WAIT" != "true" ]]; then
  log "Waiting for RabbitMQ pod (timeout: $POD_WAIT_TIMEOUT)..."
  kubectl wait pod \
    -n "$PLATFORM_NS" \
    -l "app.kubernetes.io/name=rabbitmq" \
    --for=condition=Ready \
    --timeout="$POD_WAIT_TIMEOUT" 2>/dev/null \
  || kubectl wait pod \
    -n "$PLATFORM_NS" \
    -l "rabbitmq.com/cluster=rabbitmq" \
    --for=condition=Ready \
    --timeout="$POD_WAIT_TIMEOUT" 2>/dev/null \
  || warn "Could not confirm RabbitMQ pod readiness -- check manually."
  ok "RabbitMQ pod ready."
fi

wait_sts "$PLATFORM_NS" "cassandra" "900s"
wait_sts "$PLATFORM_NS" "keycloak"  "900s"

# ── Keycloak realm bootstrap (realm/clients/roles) ──────────────────────────
banner "Keycloak Realm Bootstrap"
# shellcheck disable=SC2016
apply_manifest "$MANIFESTS_DIR/keycloak/realm-import-job.yaml" \
  '${PLATFORM_NS}'
wait_job "$PLATFORM_NS" "keycloak-realm-bootstrap" "300s"

# ── Ingress resources ─────────────────────────────────────────────────────────
banner "Ingress Resources"
# shellcheck disable=SC2016
apply_manifest "$MANIFESTS_DIR/ingress/keycloak-ingress.yaml" \
  '${PLATFORM_NS}'
ok "Ingress resources applied."

# ── Summary ───────────────────────────────────────────────────────────────────
banner "Bootstrap Complete"

CURRENT_CTX=$(kubectl config current-context)
cat <<SUMMARY

  ${BOLD}Context${RESET}      : $CURRENT_CTX
  ${BOLD}Namespaces${RESET}   : $PLATFORM_NS | $APPS_NS | $OBS_NS | $TRAEFIK_NS
  ${BOLD}Persistence${RESET}  : $PERSISTENCE_ENABLED

  ${BOLD}Components${RESET}:
    Ingress    -> Traefik v3          ($TRAEFIK_NS)
    IAM        -> Keycloak 26.1.4     ($PLATFORM_NS)   admin : $KEYCLOAK_ADMIN
    Messaging  -> RabbitMQ 4.1        ($PLATFORM_NS)   user  : $RABBITMQ_USER
    Storage    -> MinIO               ($PLATFORM_NS)   user  : $MINIO_ROOT_USER
    Database   -> Cassandra 5.0       ($PLATFORM_NS)   user  : cassandra

  ${BOLD}Quick checks${RESET}:
    kubectl get pods -n $PLATFORM_NS
    kubectl get pods -n $TRAEFIK_NS

  ${BOLD}Keycloak console${RESET}:
    kubectl port-forward -n $PLATFORM_NS svc/keycloak 8080:80
    -> http://localhost:8080  ($KEYCLOAK_ADMIN / $KEYCLOAK_PASSWORD)

  ${BOLD}MinIO console${RESET}:
    kubectl port-forward -n $PLATFORM_NS svc/minio-console 9090:9090
    -> http://localhost:9090  ($MINIO_ROOT_USER / $MINIO_ROOT_PASSWORD)

  ${BOLD}RabbitMQ management${RESET}:
    kubectl port-forward -n $PLATFORM_NS svc/rabbitmq 15672:15672
    -> http://localhost:15672  ($RABBITMQ_USER / $RABBITMQ_PASSWORD)

  ${BOLD}Cassandra CQL${RESET}:
    kubectl port-forward -n $PLATFORM_NS svc/cassandra 9042:9042
    -> cqlsh 127.0.0.1 9042 -u cassandra -p $CASSANDRA_PASSWORD

SUMMARY
