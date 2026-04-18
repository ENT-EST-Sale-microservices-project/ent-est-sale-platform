#!/usr/bin/env sh
set -eu

if [ -z "${MINIO_DEFAULT_BUCKETS:-}" ]; then
  echo "[minio-init] MINIO_DEFAULT_BUCKETS is empty, skipping bucket provisioning"
  exit 0
fi

MC_HOST_ALIAS="local"
MINIO_API="http://minio:9000"

echo "[minio-init] waiting for MinIO..."
for i in $(seq 1 60); do
  if mc alias set "$MC_HOST_ALIAS" "$MINIO_API" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

IFS=','
for bucket in $MINIO_DEFAULT_BUCKETS; do
  bucket_trimmed=$(echo "$bucket" | tr -d '[:space:]')
  [ -n "$bucket_trimmed" ] || continue
  echo "[minio-init] ensuring bucket: $bucket_trimmed"
  mc mb --ignore-existing "$MC_HOST_ALIAS/$bucket_trimmed" >/dev/null 2>&1 || true
  mc anonymous set private "$MC_HOST_ALIAS/$bucket_trimmed" >/dev/null 2>&1 || true
done

echo "[minio-init] bucket provisioning finished"
