# Telegram Scraper API Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies first (for caching)
COPY pyproject.toml .
RUN echo "# Telegram Scraper" > README.md

# Create src directory structure for editable install
RUN mkdir -p src/telegram_scraper && touch src/telegram_scraper/__init__.py

# Install dependencies only (not the package itself)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    "fastapi>=0.104.0" \
    "uvicorn[standard]>=0.24.0" \
    "sqlalchemy[asyncio]>=2.0.23" \
    "asyncpg>=0.29.0" \
    "alembic>=1.12.0" \
    "pydantic>=2.5.0" \
    "pydantic-settings>=2.1.0" \
    "python-jose[cryptography]>=3.3.0" \
    "passlib[bcrypt]>=1.7.4" \
    "telethon>=1.40.0" \
    "arq>=0.25.0" \
    "redis>=5.0.0" \
    "python-multipart>=0.0.6" \
    "aiofiles>=23.2.0" \
    "cryptography>=41.0.0" \
    "qrcode>=8.0" \
    "email-validator>=2.0.0"

# Copy source code (will be overwritten by volume in dev)
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

# Add src to Python path
ENV PYTHONPATH=/app/src

# Create media directory
RUN mkdir -p /app/media

# Expose port
EXPOSE 8000

# Run with hot reload for development
CMD ["uvicorn", "telegram_scraper.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
