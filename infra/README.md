# ENT EST Salé — Kubernetes Infrastructure

100 % open-source bootstrap for local (Kind) and production clusters.

| Component  | Version  | Deployed via       |
|------------|----------|--------------------|
| Traefik    | v3 ≥38   | Helm               |
| Keycloak   | 26.1.4   | Plain StatefulSet  |
| PostgreSQL | 16       | Plain StatefulSet  |
| RabbitMQ   | 4.1.3    | Cluster Operator   |
| MinIO      | latest   | Helm               |
| Cassandra  | 5.0      | Plain StatefulSet  |

## Quick start

```bash
# 1. Configure your environment
cp .env.example .env
$EDITOR .env           # set passwords, mode, etc.

# 2a. Local Kind cluster
make kind

# 2b. Existing cluster
make prod KUBE_CONTEXT=prod-admin@prod-cluster
```

## Directory layout

```
infra/
├── .env.example              # All configurable variables (safe to commit)
├── .env                      # Your real values         (git-ignored)
├── .gitignore
├── Makefile                  # make kind | prod | clean
│
├── bootstrap/
│   └── bootstrap-infra.sh   # Orchestrator — sources .env, calls everything
│
├── cluster/
│   └── kind-config.yaml     # Kind node config (host port mappings)
│
├── manifests/               # Pure YAML, rendered by envsubst at apply time
│   ├── namespaces.yaml
│   ├── keycloak/
│   │   ├── postgres.yaml
│   │   └── keycloak.yaml
│   ├── rabbitmq/
│   │   └── rabbitmq-cluster.yaml
│   └── cassandra/
│       └── cassandra.yaml
│
├── values/                  # Helm values — no secrets here
│   ├── traefik-values.yaml
│   └── minio-values.yaml
│
└── secrets/                 # git-ignored; place sensitive override files here
    └── .gitignore
```

## Environment variables

All variables are documented in `.env.example`.
CLI flags passed to `bootstrap-infra.sh` always override `.env` values.

## Manifest templating

Manifests use `${VAR}` placeholders rendered by `envsubst` with an **explicit
variable list**, so container-level shell variables (e.g. `${CASSANDRA_NEW_PASSWORD}`
inside a postStart script) are never accidentally expanded by the host shell.

## Helm values

Static, non-secret config lives in `values/`.  
Secrets (`rootPassword`, `rootUser`, etc.) are passed via `--set` at install
time and never written to disk.
