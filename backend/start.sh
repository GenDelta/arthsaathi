#!/usr/bin/env bash
# ArthSaathi backend startup script for Render
# Seeding is done at BUILD time — this script just runs idempotent
# migration checks (catches new migrations on redeploy) then starts uvicorn.
set -e

echo "=== ArthSaathi Backend Startup ==="

# Run migrations (idempotent — safe every restart, picks up new migrations)
echo "[1/2] Running DB migrations..."
python -m app.db.init_db

# LanceDB table check (idempotent — tables already exist from build)
echo "[2/2] LanceDB check..."
python -m app.db.init_lancedb

echo "=== Starting uvicorn on port ${PORT:-8000} ==="
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1
