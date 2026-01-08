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

echo "[entrypoint] Starting worker"
exec python -m telegram_scraper.workers.worker

