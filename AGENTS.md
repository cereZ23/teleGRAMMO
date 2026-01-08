# Repository Guidelines

## Project Structure & Module Organization
- `src/telegram_scraper/` — FastAPI backend (`api/v1/`, `models/`, `services/`, `workers/`, `core/`, `db/`, `schemas/`).
- `frontend/` — Next.js app (`src/app/`, components, store). 
- `tests/` — Pytest suite (async API tests live here).
- `alembic/` + `alembic.ini` — Database migrations.
- `docker/` + `docker-compose.yml` — Dev/runtime containers.

## Build, Test, and Development Commands
- `make up` / `make down` — Start/stop the full stack via Docker.
- `make logs[-api|-worker|-frontend]` — Tail logs.
- `make migrate` — Apply DB migrations; `make migration name="add_feature"` to autogenerate.
- `make test` — Run backend tests inside the API container.
- Local dev (optional): backend `uvicorn telegram_scraper.main:app --reload`, frontend `cd frontend && npm run dev`.
- Health check: `make health` (or `curl http://localhost:8000/health`).

## Coding Style & Naming Conventions
- Python 3.11+, 4-space indentation, type hints required.
- Lint/format with Ruff (line length 100): `ruff check src/` and `ruff format src/`.
- Type check with MyPy (strict): `mypy src/telegram_scraper`.
- Naming: snake_case for files/functions, PascalCase for classes, tests as `test_*.py`.

## Testing Guidelines
- Frameworks: `pytest`, `pytest-asyncio`, `httpx` ASGI client.
- Place tests under `tests/`; mirror package layout when practical.
- Run: `pytest -v --cov=src/telegram_scraper --cov-report=term-missing`.
- Write async tests with `@pytest.mark.asyncio`; include API and service-layer coverage.

## Commit & Pull Request Guidelines
- Commits: imperative, concise subject (≤ 50 chars). Examples: `Fix CI pipeline`, `Add channel scheduler`, `Refactor auth tokens`.
- PRs: clear description, linked issues, steps to verify, backend tests for server changes, screenshots/GIFs for UI changes, and updated docs. CI must pass.

## Security & Configuration Tips
- Copy `.env.example` to `.env`; set strong `SECRET_KEY` and session encryption key.
- Backend expects `SESSION_ENCRYPTION_KEY` (older envs may use `ENCRYPTION_KEY`). Do not commit secrets.
- Default CORS allows localhost in debug; review before deploying.
