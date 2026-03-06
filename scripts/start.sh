#!/bin/sh
set -e

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting uvicorn server..."
exec uvicorn app.main:app \
    --host "${APP_HOST:-0.0.0.0}" \
    --port "${APP_PORT:-8000}" \
    --workers 1
