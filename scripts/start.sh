#!/usr/bin/env bash
set -e

echo "==> Running Alembic migrations..."
alembic upgrade head

echo "==> Seeding database (idempotent)..."
python3 scripts/seed.py

echo "==> Starting FastAPI application on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"