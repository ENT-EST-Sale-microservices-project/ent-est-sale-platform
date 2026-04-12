# ENT EST Salé — Infrastructure Bootstrap

> Kubernetes platform bootstrap for **local development** (Kind) and **production** (existing cluster).
> 100% open-source, no commercial licence required.

---

## Table of Contents

- [What This Script Does](#what-this-script-does)
- [Tech Stack](#tech-stack)
- [Requirements](#requirements)
  - [Local Machine (Kind)](#local-machine-kind)
  - [Production Server](#production-server)
  - [Minimum Hardware](#minimum-hardware)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
  - [kind-config.yaml (local only)](#kind-configyaml-local-only)
  - [Environment Variables](#environment-variables)
- [Running the Script](#running-the-script)
  - [Local — Kind](#local--kind)
  - [Production — Existing Cluster](#production--existing-cluster)
  - [Dry Run / Fast Iteration](#dry-run--fast-iteration)
- [Accessing Services After Bootstrap](#accessing-services-after-bootstrap)
- [Troubleshooting](#troubleshooting)
- [Licence Summary](#licence-summary)

---

## What This Script Does

`bootstrap-infra.sh` provisions a complete Kubernetes platform in a single command:

1. Creates (or reuses) a Kind cluster, or connects to an existing cluster
2. Creates three namespaces: `ent-platform`, `ent-apps`, `ent-observability`
3. Installs **Traefik v3** as the ingress controller
4. Deploys **Keycloak** (IAM / SSO)
5. Deploys **RabbitMQ** via the official Cluster Operator (messaging)
6. Deploys **MinIO** (S3-compatible object storage)
7. Deploys **Cassandra** (NoSQL database)
8. Waits for each component to become ready, with useful diagnostics on failure
9. Prints a summary with ready-to-use `port-forward` commands

---

## Tech Stack

| Component | Version | Chart / Method | Licence |
|---|---|---|---|
| **Traefik** (ingress) | v3.x | `traefik/traefik` Helm chart | MIT |
| **Keycloak** (IAM) | 26.x | `codecentric/keycloakx` + `quay.io/keycloak/keycloak` | Apache 2.0 |
| **RabbitMQ** (messaging) | 4.1.x | Official Cluster Operator + `rabbitmq:4.1.3-management` | Apache 2.0 |
| **MinIO** (object storage) | 2025.x | `minio/minio` Helm chart + `quay.io/minio/minio` | AGPL-3.0 |
| **Cassandra** (NoSQL) | 5.0 | Plain StatefulSet + `cassandra:5.0` (official Docker image) | Apache 2.0 |

> **Why not ingress-nginx?**  
> The `kubernetes/ingress-nginx` project was officially retired and its repository
> archived on **March 24, 2026**. No further security patches will be released.
> Traefik v3 is the recommended open-source replacement, now adopted by IBM Cloud,
> SUSE RKE2, Nutanix, and OVHcloud.

---

## Requirements

### Local Machine (Kind)

Install all of the following before running the script:

| Tool | Min Version | Install |
|---|---|---|
| `docker` | 24+ | https://docs.docker.com/engine/install/ |
| `kind` | 0.23+ | https://kind.sigs.k8s.io/docs/user/quick-start/#installation |
| `kubectl` | 1.28+ | https://kubernetes.io/docs/tasks/tools/ |
| `helm` | 3.14+ | https://helm.sh/docs/intro/install/ |

**Quick install on Ubuntu/Debian:**

```bash
# Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER && newgrp docker

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
sudo install -o root -g root -m 0755 ./kind /usr/local/bin/kind

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

**Quick install on macOS (Homebrew):**

```bash
brew install docker kind kubectl helm
```

**Verify everything is in place:**

```bash
docker version
kind version
kubectl version --client
helm version
```

---

### Production Server

The production server needs only `kubectl` and `helm`. It does **not** need Docker or Kind.

| Tool | Min Version | Install |
|---|---|---|
| `kubectl` | 1.28+ | https://kubernetes.io/docs/tasks/tools/ |
| `helm` | 3.14+ | https://helm.sh/docs/intro/install/ |
| A valid `kubeconfig` | — | Provided by your cloud or cluster admin |

**Verify your cluster access before running:**

```bash
kubectl config get-contexts          # list available contexts
kubectl config use-context <name>    # switch to the right one
kubectl cluster-info                 # confirm connectivity
kubectl get nodes                    # confirm nodes are Ready
```

---

### Minimum Hardware

| Environment | CPU | RAM | Disk |
|---|---|---|---|
| Local (Kind) | 4 cores | 8 GB | 20 GB free |
| Production (single node) | 4 vCPU | 16 GB | 50 GB |
| Production (multi-node, recommended) | 3 × 4 vCPU | 3 × 8 GB | 3 × 50 GB |

> Cassandra and Keycloak are the most memory-hungry components.
> On a tight local machine, set `MAX_HEAP_SIZE=256M` before running.

---

## Project Structure

```
ent-est-sale-platform/
├── bootstrap-infra.sh     ← this script
├── kind-config.yaml       ← Kind cluster definition (local only)
└── README.md              ← this file
```

---

## Configuration

### kind-config.yaml (local only)

Create this file next to the script if you don't already have one:

```yaml
# kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: ent-est
nodes:
  - role: control-plane
    extraPortMappings:
      - containerPort: 30080   # Traefik HTTP
        hostPort: 80
        protocol: TCP
      - containerPort: 30443   # Traefik HTTPS
        hostPort: 443
        protocol: TCP
  - role: worker
  - role: worker
```

> The `extraPortMappings` make Traefik reachable at `http://localhost` and `https://localhost`
> from your browser without any extra port-forward.

---

### Environment Variables

All variables are optional. Defaults are safe for local development.
**Always override passwords before running on a production cluster.**

| Variable | Default | Description |
|---|---|---|
| `PLATFORM_NS` | `ent-platform` | Namespace for platform services |
| `APPS_NS` | `ent-apps` | Namespace for application workloads |
| `OBS_NS` | `ent-observability` | Namespace for monitoring (Prometheus, Grafana) |
| `TRAEFIK_NS` | `traefik` | Namespace for the ingress controller |
| `PERSISTENCE_ENABLED` | `false` | Set to `true` on prod to enable PVCs |
| `SKIP_WAIT` | `false` | Set to `true` to skip readiness checks (faster CI) |
| `POD_WAIT_TIMEOUT` | `600s` | Per-component readiness timeout |
| `KEYCLOAK_ADMIN` | `admin` | Keycloak administrator username |
| `KEYCLOAK_PASSWORD` | `ChangeMe_123!` | Keycloak admin + PostgreSQL password |
| `RABBITMQ_USER` | `ent` | RabbitMQ default user |
| `RABBITMQ_PASSWORD` | `ChangeMe_123!` | RabbitMQ password |
| `MINIO_ROOT_USER` | `minio` | MinIO root user |
| `MINIO_ROOT_PASSWORD` | `ChangeMe_123!` | MinIO root password |
| `CASSANDRA_USER` | `cassandra` | Cassandra superuser |
| `CASSANDRA_PASSWORD` | `ChangeMe_123!` | Cassandra password |

---

## Running the Script

Make the script executable once:

```bash
chmod +x bootstrap-infra.sh
```

---

### Local — Kind

**Minimal (all defaults):**

```bash
./bootstrap-infra.sh \
  --mode kind \
  --cluster-name ent-est \
  --kind-config ./kind-config.yaml
```

**With custom passwords:**

```bash
KEYCLOAK_PASSWORD="MySecret_2026!" \
RABBITMQ_PASSWORD="MySecret_2026!" \
MINIO_ROOT_PASSWORD="MySecret_2026!" \
CASSANDRA_PASSWORD="MySecret_2026!" \
./bootstrap-infra.sh \
  --mode kind \
  --cluster-name ent-est \
  --kind-config ./kind-config.yaml
```

**With persistence enabled (survives cluster restart):**

```bash
PERSISTENCE_ENABLED=true \
./bootstrap-infra.sh \
  --mode kind \
  --cluster-name ent-est \
  --kind-config ./kind-config.yaml
```

---

### Production — Existing Cluster

**Step 1 — Make sure your kubeconfig is configured:**

```bash
# Example: copy the kubeconfig from your server
scp user@prod-server:~/.kube/config ~/.kube/prod-config
export KUBECONFIG=~/.kube/prod-config

# Verify
kubectl get nodes
```

**Step 2 — Run with production settings:**

```bash
PERSISTENCE_ENABLED=true \
KEYCLOAK_PASSWORD="ProdSecret_2026!" \
RABBITMQ_PASSWORD="ProdSecret_2026!" \
MINIO_ROOT_PASSWORD="ProdSecret_2026!" \
CASSANDRA_PASSWORD="ProdSecret_2026!" \
./bootstrap-infra.sh \
  --mode existing \
  --kube-context prod-admin@prod-cluster
```

**If your context name has spaces or is complex, quote it:**

```bash
./bootstrap-infra.sh \
  --mode existing \
  --kube-context "arn:aws:eks:eu-west-1:123456789:cluster/ent-est-prod"
```

**Run directly on the server** (if `kubectl` and `helm` are installed there):

```bash
ssh user@prod-server
cd /opt/ent-est-sale-platform
PERSISTENCE_ENABLED=true \
KEYCLOAK_PASSWORD="ProdSecret_2026!" \
... \
./bootstrap-infra.sh --mode existing
```

---

### Dry Run / Fast Iteration

Skip readiness waits entirely (useful for CI pipelines or when re-running after changes):

```bash
SKIP_WAIT=true ./bootstrap-infra.sh --mode kind --cluster-name ent-est --kind-config ./kind-config.yaml
```

Increase the per-component wait timeout on a slow machine:

```bash
POD_WAIT_TIMEOUT=1200s ./bootstrap-infra.sh --mode kind --cluster-name ent-est --kind-config ./kind-config.yaml
```

---

## Accessing Services After Bootstrap

The script prints these commands automatically at the end. They are reproduced here for reference.

**Keycloak (IAM console):**

```bash
kubectl port-forward -n ent-platform svc/keycloak-http 8080:80
# → http://localhost:8080
# Username: admin  |  Password: (your KEYCLOAK_PASSWORD)
```

**MinIO (object storage console):**

```bash
kubectl port-forward -n ent-platform svc/minio-console 9090:9090
# → http://localhost:9090
# Username: minio  |  Password: (your MINIO_ROOT_PASSWORD)
```

**RabbitMQ (management UI):**

```bash
kubectl port-forward -n ent-platform svc/rabbitmq 15672:15672
# → http://localhost:15672
# Username: ent  |  Password: (your RABBITMQ_PASSWORD)
```

**Cassandra (CQL shell):**

```bash
kubectl port-forward -n ent-platform svc/cassandra 9042:9042
cqlsh 127.0.0.1 9042 -u cassandra -p <your CASSANDRA_PASSWORD>
```

**Traefik dashboard:**

```bash
kubectl port-forward -n traefik $(kubectl get pods -n traefik -o name | head -1) 8090:8080
# → http://localhost:8090/dashboard/
```

---

## Troubleshooting

**Script is stuck and not progressing**

Run in a second terminal to inspect pod state:

```bash
kubectl get pods -n ent-platform -o wide --watch
kubectl describe pod <pod-name> -n ent-platform
kubectl logs <pod-name> -n ent-platform --previous
```

**ImagePullBackOff / ErrImagePull**

Verify the image is reachable from your cluster:

```bash
# Test manually from a debug pod
kubectl run test --rm -it --image=busybox -- sh
# Inside: wget -O- https://quay.io/v2/
```

**Keycloak pod CrashLoopBackOff**

Usually a database connection issue. Check:

```bash
kubectl logs -n ent-platform -l app.kubernetes.io/name=keycloak --tail=50
kubectl get pod -n ent-platform -l app.kubernetes.io/name=keycloak-postgresql
```

**Cassandra taking too long to become Ready**

Cassandra always takes 60–90 seconds to initialise before its readiness probe passes. This is expected. If it exceeds 15 minutes:

```bash
kubectl logs -n ent-platform statefulset/cassandra
```

**RabbitMQ pod stuck in Pending**

The RabbitMQ Cluster Operator may not have finished deploying before the CR was applied. Wait 30 seconds and re-apply:

```bash
kubectl get pods -n rabbitmq-system
kubectl apply -n ent-platform -f - <<EOF
# (paste the RabbitmqCluster CR from the script)
EOF
```

**Kind cluster networking issue (ports not reachable on localhost)**

Make sure `kind-config.yaml` has the `extraPortMappings` block (see above). Recreate the cluster if needed:

```bash
kind delete cluster --name ent-est
./bootstrap-infra.sh --mode kind --cluster-name ent-est --kind-config ./kind-config.yaml
```

**Reset everything and start fresh (local only):**

```bash
kind delete cluster --name ent-est
./bootstrap-infra.sh --mode kind --cluster-name ent-est --kind-config ./kind-config.yaml
```

---

## Licence Summary

| Component | Licence | Commercial use |
|---|---|---|
| Traefik Proxy | MIT | ✅ Free |
| Keycloak | Apache 2.0 | ✅ Free |
| RabbitMQ | Apache 2.0 | ✅ Free |
| MinIO | AGPL-3.0 | ✅ Free for open-source projects |
| Apache Cassandra | Apache 2.0 | ✅ Free |
| Kind | Apache 2.0 | ✅ Free |
| Helm | Apache 2.0 | ✅ Free |

> MinIO's AGPL-3.0 licence means that if you embed MinIO in a **proprietary closed-source product**
> and distribute it, you must open-source your product. For internal use or open-source projects
> there is no restriction. See https://min.io/compliance for details.