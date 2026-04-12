# Sprint 0 — Close Checklist

## Exit criteria
- [x] Kubernetes namespaces exist (`ent-platform`, `ent-apps`, `ent-observability`, `traefik`)
- [x] Platform core deployed (`Traefik`, `Keycloak`, `Postgres`, `RabbitMQ`, `MinIO`, `Cassandra`)
- [x] Keycloak bootstrap automated (realm + clients + roles)
- [x] Ingress resource defined (Keycloak via Traefik)
- [x] Minimal CI added (shell lint + yaml lint + manifest render validation)

## Files added for closure
- [infra/manifests/keycloak/realm-import-job.yaml](infra/manifests/keycloak/realm-import-job.yaml)
- [infra/manifests/ingress/keycloak-ingress.yaml](infra/manifests/ingress/keycloak-ingress.yaml)
- [.github/workflows/infra-ci.yml](.github/workflows/infra-ci.yml)

## Validation commands
1. Re-run infra bootstrap:
   - `cd infra && make kind`
2. Validate Keycloak realm import:
   - `kubectl get job -n ent-platform keycloak-realm-bootstrap`
   - `kubectl logs -n ent-platform job/keycloak-realm-bootstrap`
3. Validate ingress:
   - `kubectl get ingress -n ent-platform`
   - open `http://keycloak.localtest.me`
4. Validate CI:
   - Push branch / open PR and check `infra-ci` workflow status.
