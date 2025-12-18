# TeleGRAMMO Architecture

## Overview

TeleGRAMMO is a full-stack Telegram scraper built with a microservices-lite architecture, orchestrated via Docker Compose.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DOCKER COMPOSE                                  │
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   FRONTEND  │    │     API     │    │   WORKER    │    │   DATABASE  │  │
│  │   Next.js   │───▶│   FastAPI   │───▶│    ARQ      │    │  PostgreSQL │  │
│  │   :3000     │    │   :8000     │    │  (async)    │    │    :5432    │  │
│  └─────────────┘    └──────┬──────┘    └──────┬──────┘    └──────▲──────┘  │
│                            │                  │                  │         │
│                            │           ┌──────▼──────┐           │         │
│                            │           │    REDIS    │           │         │
│                            │           │   (queue)   │           │         │
│                            │           │    :6379    │           │         │
│                            │           └─────────────┘           │         │
│                            │                  │                  │         │
│                            └──────────────────┴──────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
                            ┌─────────────────────┐
                            │   TELEGRAM API      │
                            │   (Telethon)        │
                            └─────────────────────┘
```

---

## Components

### 1. Frontend (Next.js 15 + React 19)

| Property | Value |
|----------|-------|
| **Purpose** | User interface |
| **Port** | 3000 |
| **Tech** | TypeScript, TailwindCSS, shadcn/ui, Zustand |
| **Communicates** | API via REST (axios) |

**Responsibilities:**
- Login/registration
- Dashboard with statistics
- Channel and Telegram session management
- Message viewer with filters and full-text search
- Keyword alerts UI
- CSV/JSON export
- Dark mode support

### 2. API (FastAPI + SQLAlchemy)

| Property | Value |
|----------|-------|
| **Purpose** | REST backend, authentication, business logic |
| **Port** | 8000 |
| **Tech** | Python 3.12, Pydantic, JWT, async SQLAlchemy |
| **Communicates** | PostgreSQL (data), Redis (job queue), Worker (via Redis) |

**Responsibilities:**
- JWT authentication (access + refresh tokens)
- CRUD for channels, messages, keyword alerts
- Request validation
- Scraping job queuing
- Analytics queries

### 3. Worker (ARQ - Async Redis Queue)

| Property | Value |
|----------|-------|
| **Purpose** | Background task execution (scraping) |
| **Port** | None (daemon) |
| **Tech** | Python, Telethon, ARQ |
| **Communicates** | Redis (reads jobs), PostgreSQL (writes data), Telegram API |

**Responsibilities:**
- `scrape_channel_task`: Downloads messages from Telegram
- `download_media_task`: Downloads photos/videos/documents
- Keyword checking during scraping
- Job progress updates

### 4. PostgreSQL

| Property | Value |
|----------|-------|
| **Purpose** | Data persistence |
| **Port** | 5432 |
| **Tech** | PostgreSQL 16 + pg_trgm (full-text search) |

**Main Tables:**
- `users` - User accounts
- `telegram_sessions` - Telegram API credentials (encrypted)
- `channels` - Monitored channels
- `messages` - Scraped messages
- `media` - Media file metadata
- `scraping_jobs` - Scraping job status
- `keyword_alerts` - Alert definitions
- `keyword_matches` - Found matches

### 5. Redis

| Property | Value |
|----------|-------|
| **Purpose** | Message broker for job queue |
| **Port** | 6379 |
| **Tech** | Redis 7 |

**Usage:**
- ARQ task queue (FIFO)
- Job scheduling
- Cache (future)

---

## Request Flow: Channel Scraping

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  USER    │     │ FRONTEND │     │   API    │     │  REDIS   │     │  WORKER  │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │ Click "Scrape" │                │                │                │
     │───────────────▶│                │                │                │
     │                │ POST /jobs/    │                │                │
     │                │ scrape         │                │                │
     │                │───────────────▶│                │                │
     │                │                │                │                │
     │                │                │ Create job     │                │
     │                │                │ in DB          │                │
     │                │                │ (pending)      │                │
     │                │                │                │                │
     │                │                │ Queue task     │                │
     │                │                │───────────────▶│                │
     │                │                │                │                │
     │                │  { job_id }    │                │                │
     │                │◀───────────────│                │                │
     │                │                │                │                │
     │  "Job started" │                │                │ Pop task       │
     │◀───────────────│                │                │───────────────▶│
     │                │                │                │                │
     │                │                │                │                │ Connect to
     │                │                │                │                │ Telegram API
     │                │                │                │                │────────────▶
     │                │                │                │                │
     │                │                │                │                │ For each msg:
     │                │                │                │                │ • Save to DB
     │                │                │                │                │ • Check keywords
     │                │                │                │                │ • Update progress
     │                │                │                │                │
     │ Poll GET       │                │                │                │
     │ /jobs/{id}     │                │                │                │
     │───────────────▶│───────────────▶│                │                │
     │                │                │ Read job       │                │
     │                │  progress: 45% │ from DB        │                │
     │◀───────────────│◀───────────────│                │                │
     │                │                │                │                │
     │                │                │                │   Job done     │
     │                │                │                │   (completed)  │
     │                │                │                │◀───────────────│
     │                │                │                │                │
```

---

## Project Structure

```
telegram-scraper/
│
├── docker-compose.yml          # Container orchestration
│
├── src/telegram_scraper/       # PYTHON BACKEND
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Settings (env vars)
│   │
│   ├── api/v1/                 # REST Endpoints
│   │   ├── router.py           # Aggregates all routers
│   │   ├── auth.py             # Login, register, JWT
│   │   ├── channels.py         # Channel CRUD
│   │   ├── jobs.py             # Scraping job management
│   │   ├── keywords.py         # Keyword alerts API
│   │   └── ...
│   │
│   ├── models/                 # SQLAlchemy ORM
│   │   ├── user.py
│   │   ├── channel.py
│   │   ├── message.py
│   │   ├── keyword_alert.py
│   │   └── ...
│   │
│   ├── services/               # Business logic
│   │   ├── telegram_service.py # Telethon client management
│   │   └── ...
│   │
│   └── workers/                # Background tasks
│       ├── worker.py           # ARQ worker config
│       └── tasks/
│           ├── scrape_channel.py
│           └── download_media.py
│
├── frontend/                   # NEXT.JS FRONTEND
│   └── src/
│       ├── app/                # Pages (App Router)
│       │   ├── login/
│       │   └── dashboard/
│       │       ├── page.tsx
│       │       ├── channels/
│       │       ├── keywords/
│       │       └── ...
│       │
│       ├── components/ui/      # shadcn components
│       ├── lib/api.ts          # API client (axios)
│       └── store/              # Zustand stores
│
└── alembic/                    # Database migrations
    └── versions/
```

---

## Technology Choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **FastAPI** | vs Flask/Django | Native async, auto OpenAPI docs, Pydantic validation |
| **ARQ** | vs Celery | Lightweight, native async (matches Telethon), Redis-only |
| **PostgreSQL** | vs SQLite/MongoDB | ACID compliance, full-text search, JSONB for reactions |
| **Next.js** | vs CRA/Vite | SSR, App Router, excellent DX |
| **Redis** | vs RabbitMQ | Simple, fast, already used by ARQ |
| **Docker Compose** | vs K8s | Simplicity for dev/small deployments |

---

## Security

| Aspect | Implementation |
|--------|----------------|
| **Passwords** | bcrypt hash (cost 12) |
| **JWT** | Access token 15min, refresh token 7 days |
| **Telegram sessions** | AES-256 encrypted at rest |
| **API** | Rate limiting, Pydantic input validation |
| **Database** | Prepared statements (no SQL injection) |

---

## Database Schema

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     users       │     │    channels     │     │    messages     │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │     │ id (PK)         │     │ id (PK)         │
│ email           │     │ telegram_id     │     │ channel_id (FK) │
│ password_hash   │     │ username        │     │ telegram_msg_id │
│ is_active       │     │ title           │     │ date            │
│ created_at      │     │ channel_type    │     │ message_text    │
└────────┬────────┘     └────────┬────────┘     │ media_type      │
         │                       │              │ views, forwards │
         │                       │              │ reactions (JSON)│
         ▼                       ▼              └─────────────────┘
┌─────────────────┐     ┌─────────────────┐
│ telegram_sessions│    │  user_channels  │
├─────────────────┤     ├─────────────────┤
│ id (PK)         │     │ user_id (FK)    │
│ user_id (FK)    │     │ channel_id (FK) │
│ api_id          │     │ is_active       │
│ api_hash        │     │ scrape_media    │
│ session_string  │     │ schedule_enabled│
│ is_authenticated│     └─────────────────┘
└─────────────────┘

┌─────────────────┐     ┌─────────────────┐
│ keyword_alerts  │     │ keyword_matches │
├─────────────────┤     ├─────────────────┤
│ id (PK)         │◀────│ keyword_alert_id│
│ user_id (FK)    │     │ message_id (FK) │
│ channel_id (FK) │     │ channel_id (FK) │
│ keyword         │     │ matched_text    │
│ is_regex        │     │ is_read         │
│ is_active       │     │ created_at      │
│ match_count     │     └─────────────────┘
└─────────────────┘
```

---

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/auth/login` - Login, returns JWT
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Current user

### Telegram Sessions
- `POST /api/v1/telegram/sessions` - Create session
- `GET /api/v1/telegram/sessions` - List sessions
- `POST /api/v1/telegram/sessions/{id}/qr-login` - QR auth
- `DELETE /api/v1/telegram/sessions/{id}` - Delete session

### Channels
- `GET /api/v1/channels` - List tracked channels
- `POST /api/v1/channels` - Add channel
- `DELETE /api/v1/channels/{id}` - Remove channel
- `GET /api/v1/channels/{id}/messages` - Get messages (paginated, filtered)

### Jobs
- `POST /api/v1/jobs/scrape` - Start scrape job
- `GET /api/v1/jobs` - List jobs
- `GET /api/v1/jobs/{id}` - Job status with progress
- `POST /api/v1/jobs/{id}/cancel` - Cancel job

### Keywords
- `GET /api/v1/keywords` - List alerts
- `POST /api/v1/keywords` - Create alert
- `PUT /api/v1/keywords/{id}` - Update alert
- `DELETE /api/v1/keywords/{id}` - Delete alert
- `GET /api/v1/keywords/{id}/matches` - Get matches
- `POST /api/v1/keywords/{id}/matches/mark-read` - Mark as read

### Export
- `GET /api/v1/export/channels/{id}/csv` - Export to CSV
- `GET /api/v1/export/channels/{id}/json` - Export to JSON
