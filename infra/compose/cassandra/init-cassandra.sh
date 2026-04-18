#!/usr/bin/env bash
set -euo pipefail

CASSANDRA_HOST="cassandra"
CASSANDRA_PORT="9042"
CASSANDRA_USER="cassandra"
DEFAULT_PASSWORD="cassandra"
NEW_PASSWORD="${CASSANDRA_PASSWORD:-cassandra}"
KEYSPACE="${CASSANDRA_KEYSPACE:-ent_est}"

echo "[cassandra-init] waiting for Cassandra to accept CQL..."
for i in $(seq 1 90); do
  if cqlsh "$CASSANDRA_HOST" "$CASSANDRA_PORT" -u "$CASSANDRA_USER" -p "$DEFAULT_PASSWORD" -e "DESCRIBE KEYSPACES" >/dev/null 2>&1 \
     || cqlsh "$CASSANDRA_HOST" "$CASSANDRA_PORT" -u "$CASSANDRA_USER" -p "$NEW_PASSWORD" -e "DESCRIBE KEYSPACES" >/dev/null 2>&1; then
    break
  fi
  sleep 3
done

if [ "$NEW_PASSWORD" != "$DEFAULT_PASSWORD" ]; then
  echo "[cassandra-init] rotating default Cassandra password..."
  cqlsh "$CASSANDRA_HOST" "$CASSANDRA_PORT" -u "$CASSANDRA_USER" -p "$DEFAULT_PASSWORD" \
    -e "ALTER USER cassandra WITH PASSWORD '$NEW_PASSWORD';" >/dev/null 2>&1 || true
fi

echo "[cassandra-init] ensuring keyspace $KEYSPACE"
cqlsh "$CASSANDRA_HOST" "$CASSANDRA_PORT" -u "$CASSANDRA_USER" -p "$NEW_PASSWORD" \
  -e "CREATE KEYSPACE IF NOT EXISTS $KEYSPACE WITH replication = {'class':'SimpleStrategy','replication_factor':1};"

echo "[cassandra-init] done"
