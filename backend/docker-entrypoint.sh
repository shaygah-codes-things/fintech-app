#!/usr/bin/env bash
set -euo pipefail

# wait for DB (best-effort)
python - <<'PY'
import os, time
import psycopg
url = os.getenv("DATABASE_URL", "")
for i in range(30):
    try:
        with psycopg.connect(url, connect_timeout=2) as _:
            break
    except Exception:
        time.sleep(1)
else:
    print("DB not reachable yet, continuing anyway…")
PY

# run migrations (ok if already up-to-date)
python -m alembic upgrade head || true

# start the app
exec uvicorn app.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000}
