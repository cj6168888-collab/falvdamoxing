#!/bin/sh
set -eu

: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"

POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
PGBOUNCER_LISTEN_PORT="${PGBOUNCER_LISTEN_PORT:-6432}"
PGBOUNCER_POOL_MODE="${PGBOUNCER_POOL_MODE:-transaction}"
PGBOUNCER_MAX_CLIENT_CONN="${PGBOUNCER_MAX_CLIENT_CONN:-2000}"
PGBOUNCER_DEFAULT_POOL_SIZE="${PGBOUNCER_DEFAULT_POOL_SIZE:-80}"
PGBOUNCER_RESERVE_POOL_SIZE="${PGBOUNCER_RESERVE_POOL_SIZE:-40}"

cat > /tmp/userlist.txt <<EOF
"${POSTGRES_USER}" "${POSTGRES_PASSWORD}"
EOF

cat > /tmp/pgbouncer.ini <<EOF
[databases]
${POSTGRES_DB} = host=${POSTGRES_HOST} port=${POSTGRES_PORT} dbname=${POSTGRES_DB}

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = ${PGBOUNCER_LISTEN_PORT}
auth_type = plain
auth_file = /tmp/userlist.txt
pool_mode = ${PGBOUNCER_POOL_MODE}
max_client_conn = ${PGBOUNCER_MAX_CLIENT_CONN}
default_pool_size = ${PGBOUNCER_DEFAULT_POOL_SIZE}
reserve_pool_size = ${PGBOUNCER_RESERVE_POOL_SIZE}
server_idle_timeout = 60
server_reset_query = DISCARD ALL
ignore_startup_parameters = extra_float_digits
admin_users = ${POSTGRES_USER}
stats_users = ${POSTGRES_USER}
log_connections = 0
log_disconnections = 0
EOF

chown pgbouncer:pgbouncer /tmp/pgbouncer.ini /tmp/userlist.txt

exec su-exec pgbouncer pgbouncer /tmp/pgbouncer.ini
