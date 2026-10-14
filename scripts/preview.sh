#!/bin/sh
# Dev/preview launcher for AI Student Learning Mentor.
#
# The application requires a running MySQL-compatible server (XAMPP/MySQL/MariaDB).
# This script makes sure one is up, then serves the Flask app on 0.0.0.0:$PORT
# so hosted preview environments can reach it.
set -e

if ! mysqladmin ping --silent >/dev/null 2>&1; then
    echo "[preview] starting local database server..."
    service mariadb start >/dev/null 2>&1 || true
    i=0
    while [ "$i" -lt 30 ]; do
        if mysqladmin ping --silent >/dev/null 2>&1; then
            break
        fi
        i=$((i + 1))
        sleep 1
    done
fi

if ! mysqladmin ping --silent >/dev/null 2>&1; then
    echo "[preview] WARNING: no database server reachable - the app will report unhealthy." >&2
fi

exec python3 -m flask --app app run --host 0.0.0.0 --port "${PORT:-5000}"
