#!/usr/bin/env bash
# Spins up a throwaway PostgreSQL 16 on 127.0.0.1:5498, loads ledger.sql, runs failure_tests.sql.
# Usage (as root, needs postgresql-16 binaries):  kernel/run.sh [workdir]
# The workdir and its parents must be traversable by the 'postgres' user.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PG=${PG:-/usr/lib/postgresql/16/bin}
D="${1:-$(mktemp -d)}/pg-lot002"
rm -rf "$D"; mkdir -p "$D"; chown -R postgres "$D"
su postgres -c "$PG/initdb -D $D/data -A trust >/dev/null"
cat >> "$D/data/postgresql.conf" <<CONF
port = 5498
listen_addresses = '127.0.0.1'
unix_socket_directories = ''
CONF
su postgres -c "$PG/pg_ctl -D $D/data -l $D/log -w start >/dev/null"
trap 'su postgres -c "$PG/pg_ctl -D $D/data stop -m fast >/dev/null"' EXIT
PSQL=(psql -h 127.0.0.1 -p 5498 -U postgres -v ON_ERROR_STOP=1 -q)
"${PSQL[@]}" -f "$HERE/ledger.sql"
"${PSQL[@]}" -f "$HERE/failure_tests.sql" 2>&1 | sed 's/^psql:[^ ]* NOTICE:  /  /'
