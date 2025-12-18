# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Modern Telegram Channel Scraper - A full-stack web application for scraping Telegram channels with:
- **FastAPI** backend with REST API
- **PostgreSQL** database
- **React (Next.js 14)** frontend (planned)
- **ARQ** background workers for async scraping
- **Multi-user authentication** with JWT

## Docker Commands (Primary Development Method)

```bash
# Start all services (PostgreSQL, Redis, API, Worker)
make up

# Run database migrations
make migrate

# View logs
make logs          # All services
make logs-api      # API only
make logs-worker   # Worker only

# Shell access
make shell         # API container bash
make db            # PostgreSQL psql

# Stop services
make down

# Clean everything (including data)
make clean

# Health check
make health
```

## Architecture

```
src/telegram_scraper/
├── main.py              # FastAPI app entry point
├── config.py            # Pydantic settings (env vars)
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic request/response schemas
├── api/v1/              # FastAPI routers
├── services/            # Business logic layer
├── workers/             # ARQ background tasks
│   ├── worker.py        # Worker config and entry point
│   └── tasks/           # Individual task implementations
├── db/                  # Database session management
└── core/                # Security, exceptions
```

## Database Schema (PostgreSQL)

- `users` - User accounts with JWT auth
- `telegram_sessions` - Per-user Telegram API credentials (StringSession)
- `channels` - Telegram channels metadata
- `user_channels` - Many-to-many user-channel tracking
- `messages` - Scraped messages with JSONB reactions
- `media` - Media file records with download status
- `scraping_jobs` - Background job tracking

## API Endpoints

- `GET /health` - Health check
- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/auth/login` - Get JWT tokens
- `GET /api/v1/auth/me` - Current user info

## Docker Services

| Service | Port | Description |
|---------|------|-------------|
| api | 8000 | FastAPI backend (hot reload enabled) |
| worker | - | ARQ background worker |
| postgres | 5432 | PostgreSQL 16 |
| redis | 6379 | Redis 7 |

## Development Workflow

1. Start services: `make up`
2. Run migrations: `make migrate`
3. Check health: `make health`
4. View API docs: http://localhost:8000/docs
5. Code changes auto-reload (volume mounted)

## Legacy CLI

The original single-file CLI (`telegram-scraper.py`) is still available for standalone use with SQLite.
