#!/usr/bin/env bash
# ArthSaathi backend startup script for Render
# Runs on every container start (including cold-start after spin-down)
set -e

echo "=== ArthSaathi Backend Startup ==="

# 1. Init SQLite schema (idempotent — safe to run every restart)
echo "[1/3] Running DB migrations..."
python -m app.db.init_db

# 2. Init LanceDB tables (idempotent)
echo "[2/3] Initialising LanceDB..."
python -m app.db.init_lancedb

# 3. Seed schemes if the LanceDB vectors table is empty
#    (detects first-run or after ephemeral storage wipe)
echo "[3/3] Checking scheme seed..."
python -c "
import lancedb, os, sys
path = os.getenv('LANCEDB_PATH', './.lancedb')
db = lancedb.connect(path)
tables = db.table_names() if hasattr(db, 'table_names') else db.list_tables()
if 'schemes_vectors' in tables:
    t = db.open_table('schemes_vectors')
    count = t.count_rows()
    if count > 0:
        print(f'Schemes already seeded ({count} vectors). Skipping.')
        sys.exit(0)
print('Seeding schemes...')
" && python scripts/seed_schemes.py && python scripts/seed_clauses.py || echo "Seeding skipped or already done."

# 4. Launch uvicorn on the port Render provides via \$PORT
echo "=== Starting uvicorn on port \${PORT:-8000} ==="
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1
