# TeleGRAMMO

A modern, full-stack Telegram channel scraper with a beautiful web interface. Scrape messages, media, and analytics from Telegram channels you have access to.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![Next.js](https://img.shields.io/badge/next.js-14-black.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

```
___________________  _________
\__    ___/  _____/ /   _____/
  |    | /   \  ___ \_____  \
  |    | \    \_\  \/        \
  |____|  \______  /_______  /
                 \/        \/
```

## Features

- **Multi-user Authentication** - Secure JWT-based authentication with registration/login
- **Telegram Integration** - Connect multiple Telegram accounts via phone verification
- **Channel Scraping** - Scrape messages from any channel you have access to
- **Scheduled Scraping** - Auto-scrape channels on a schedule (hourly, daily, weekly)
- **Analytics Dashboard** - Beautiful charts showing message trends, top senders, media breakdown
- **Export Data** - Export messages to CSV or JSON format
- **Real-time Progress** - Track scraping progress with live updates
- **Media Tracking** - Track photos, videos, documents, and other media
- **Search** - Search through scraped messages
- **Responsive UI** - Works on desktop and mobile

## Tech Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **PostgreSQL** - Robust database
- **Redis** - Job queue for background tasks
- **ARQ** - Async background workers
- **Telethon** - Telegram MTProto API client
- **SQLAlchemy 2.0** - Async ORM with type hints

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - Beautiful UI components
- **React Query** - Server state management
- **Recharts** - Analytics charts

## Prerequisites

- **Docker** & **Docker Compose** (v2.0+)
- **Git**

That's it! Everything else runs in containers.

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/cereZ23/teleGRAMMO.git
cd teleGRAMMO
```

### 2. Configure environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your favorite editor
nano .env
```

**Generate required secrets:**

```bash
# Generate SECRET_KEY (copy the output to .env)
openssl rand -hex 32

# Generate ENCRYPTION_KEY (copy the output to .env)
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Start the application

```bash
docker-compose up -d
```

Wait about 30 seconds for all services to initialize.

### 3a. Migrations

Migrations now auto-run on API/worker startup. On upgrades, you can simply:

```bash
docker-compose pull
docker-compose restart api worker
```

Manual (optional):

```bash
docker-compose run --rm migrate
```

If `pgcrypto` is missing (some Postgres images), the containers attempt to enable it automatically. You can also enable it manually and rerun migrations:

```bash
docker-compose exec postgres psql -U postgres -d telegram_scraper -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
docker-compose run --rm migrate
```

### 4. Access the application

Open your browser: **http://localhost:3000**

## First-Time Setup

### 1. Create an Account

1. Click **"Register"** on the login page
2. Enter your email and password
3. Click **"Create Account"**
4. Log in with your credentials

### 2. Connect Telegram

1. Go to **"Telegram"** in the sidebar
2. Follow the step-by-step tutorial displayed on the page
3. Get API credentials from [my.telegram.org/apps](https://my.telegram.org/apps):
   - Log in with your phone number
   - Create a new application
   - Copy **API ID** (number) and **API Hash** (string)
4. Click **"Add Session"** and enter your credentials
5. Enter your phone number (with country code, e.g., +1234567890)
6. Enter the verification code sent to your Telegram app

### 3. Add Channels

1. Go to **"Channels"** in the sidebar
2. Click **"Add Channel"**
3. Select channels from your Telegram account
4. Click **"Add"** next to each channel you want to track

### 4. Start Scraping

1. Click on a channel card to open its detail page
2. Click **"Start Scrape"** button
3. Watch the progress bar update in real-time
4. Once complete, browse messages or export data

### 5. Enable Scheduled Scraping (Optional)

1. On the channel detail page, find **"Scheduled Scraping"**
2. Click **"Configure"**
3. Select an interval (1 hour, 6 hours, 12 hours, daily, weekly)
4. Click **"Enable Auto-Scrape"**

## Docker Services

| Service | Port | Description |
|---------|------|-------------|
| `frontend` | 3000 | Next.js web interface |
| `api` | 8000 | FastAPI REST API |
| `postgres` | 5432 | PostgreSQL database |
| `redis` | 6379 | Redis job queue |
| `worker` | - | ARQ background worker |

## Environment Variables

Create a `.env` file with these variables:

```env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=change_this_secure_password
POSTGRES_DB=telegram_scraper
DATABASE_URL=postgresql+asyncpg://postgres:change_this_secure_password@postgres:5432/telegram_scraper

# Redis
REDIS_URL=redis://redis:6379

# Security - CHANGE THESE IN PRODUCTION!
SECRET_KEY=generate_with_openssl_rand_hex_32
ENCRYPTION_KEY=generate_with_fernet_generate_key

# App settings
DEBUG=true
APP_NAME=TeleGRAMMO
```

## API Documentation

Access the interactive API docs at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | Login, returns JWT tokens |
| `/api/v1/auth/me` | GET | Get current user info |
| `/api/v1/telegram/sessions` | GET/POST | Manage Telegram sessions |
| `/api/v1/telegram/sessions/{id}/send-code` | POST | Send verification code |
| `/api/v1/telegram/sessions/{id}/verify-code` | POST | Verify code |
| `/api/v1/channels` | GET/POST/DELETE | Manage tracked channels |
| `/api/v1/channels/{id}/messages` | GET | Get channel messages (paginated) |
| `/api/v1/channels/{id}/schedule` | GET/PUT | Manage scraping schedule |
| `/api/v1/jobs/scrape` | POST | Start scraping job |
| `/api/v1/jobs` | GET | List all jobs |
| `/api/v1/analytics/overview` | GET | Get analytics overview |
| `/api/v1/analytics/messages-over-time` | GET | Message trend data |
| `/api/v1/export/channels/{id}/csv` | GET | Export to CSV |
| `/api/v1/export/channels/{id}/json` | GET | Export to JSON |

## Project Structure

```
teleGRAMMO/
├── src/telegram_scraper/          # Python backend
│   ├── api/v1/                    # FastAPI routes
│   │   ├── auth.py                # Authentication endpoints
│   │   ├── telegram.py            # Telegram session management
│   │   ├── channels.py            # Channel CRUD + scheduling
│   │   ├── jobs.py                # Scraping job management
│   │   ├── analytics.py           # Analytics endpoints
│   │   └── export.py              # CSV/JSON export
│   ├── models/                    # SQLAlchemy ORM models
│   ├── services/                  # Business logic
│   │   ├── telegram_service.py    # Telethon client management
│   │   ├── channel_service.py     # Channel operations
│   │   └── scheduler_service.py   # Scheduled scraping
│   └── workers/                   # Background tasks
│       ├── worker.py              # ARQ worker config
│       └── tasks/                 # Task implementations
│           ├── scrape_channel.py  # Scraping logic
│           └── scheduler.py       # Schedule checker
├── frontend/                      # Next.js frontend
│   ├── src/
│   │   ├── app/                   # App Router pages
│   │   │   ├── dashboard/         # Dashboard pages
│   │   │   │   ├── analytics/     # Analytics page
│   │   │   │   ├── channels/      # Channel management
│   │   │   │   ├── telegram/      # Session management
│   │   │   │   └── jobs/          # Job history
│   │   │   ├── login/             # Login page
│   │   │   └── register/          # Registration page
│   │   ├── components/ui/         # shadcn/ui components
│   │   ├── lib/api.ts             # API client
│   │   └── store/                 # Zustand state
│   └── package.json
├── alembic/                       # Database migrations
├── docker-compose.yml             # Docker services
├── Dockerfile                     # Backend container
├── frontend/Dockerfile            # Frontend container
└── .env.example                   # Environment template
```

## Common Operations

### View logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f frontend
```

### Restart services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart api
docker-compose restart worker
```

### Stop the application

```bash
docker-compose down
```

### Reset everything (including data)

```bash
docker-compose down -v
docker-compose up -d
```

### Update to latest version

```bash
git pull
docker-compose build
docker-compose up -d
```

## Troubleshooting

### "Could not find the input entity" error

This is handled automatically. If you see this error, try:
1. Re-authenticate your Telegram session
2. Make sure you have access to the channel

### Scraping shows 0% progress

Check worker logs:
```bash
docker-compose logs -f worker
```

The worker might be starting up or processing the job.

### Can't connect to application

1. Check if all containers are running:
   ```bash
   docker-compose ps
   ```
2. Check for errors:
   ```bash
   docker-compose logs api
   docker-compose logs frontend
   ```

### "relation ... does not exist" or UndefinedTableError

Run DB migrations (first run or after reset):

```bash
docker-compose run --rm migrate
```

If needed, enable `pgcrypto` then rerun the migration:

```bash
docker-compose exec postgres psql -U postgres -d telegram_scraper -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
docker-compose run --rm migrate
```

### Database connection refused

Wait 30 seconds after starting - PostgreSQL needs time to initialize.

### Frontend shows "Network Error"

Make sure the API is running on port 8000:
```bash
docker-compose logs api
```

## Security Considerations

- **Passwords** are hashed with bcrypt (cost factor 12)
- **JWT tokens** expire after 30 minutes (refresh tokens: 7 days)
- **Telegram sessions** are encrypted at rest with Fernet (AES-128)
- **API endpoints** require authentication
- **CORS** is configured to allow only the frontend origin

**For production deployment:**
1. Use strong, unique values for `SECRET_KEY` and `ENCRYPTION_KEY`
2. Set `DEBUG=false`
3. Use HTTPS with a reverse proxy (nginx, Caddy, Traefik)
4. Consider rate limiting
5. Use a proper secrets manager

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Telethon](https://github.com/LonamiWebs/Telethon) - Telegram MTProto API client
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Next.js](https://nextjs.org/) - React framework
- [shadcn/ui](https://ui.shadcn.com/) - Beautiful UI components
- [Recharts](https://recharts.org/) - Chart library
- [ARQ](https://github.com/samuelcolvin/arq) - Async job queue

## Support

For issues and feature requests, please use [GitHub Issues](https://github.com/cereZ23/teleGRAMMO/issues).

---

Made with Python, TypeScript, and caffeine.
