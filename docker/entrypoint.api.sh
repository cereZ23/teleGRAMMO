#!/usr/bin/env sh
set -euo pipefail

echo "[entrypoint] Ensuring pgcrypto extension (if available)"
python - <<'PY'
import os, asyncio
from sqlalchemy.ext.asyncio import create_async_engine

db_url = os.environ.get("DATABASE_URL")
if db_url:
    async def main():
        engine = create_async_engine(db_url, echo=False, future=True)
        try:
            async with engine.begin() as conn:
                try:
                    await conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
                except Exception:
                    # Extension may be unavailable (e.g., managed DB) — continue
                    pass
        finally:
            await engine.dispose()
    asyncio.run(main())
PY

echo "[entrypoint] Running alembic upgrade head"
alembic upgrade head || {
  echo "[entrypoint] Alembic upgrade failed" >&2
  exit 1
}

echo "[entrypoint] Starting API"
RELOAD_ARGS=""
if [ "${DEBUG:-}" = "true" ] || [ "${DEBUG:-}" = "1" ]; then
  RELOAD_ARGS="--reload"
fi
exec uvicorn telegram_scraper.main:app --host 0.0.0.0 --port 8000 $RELOAD_ARGS
