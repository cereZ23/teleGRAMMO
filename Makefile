.PHONY: up down build logs shell migrate test clean

# Start all services
up:
	docker-compose up -d

# Start with logs
up-logs:
	docker-compose up

# Stop all services
down:
	docker-compose down

# Rebuild containers
build:
	docker-compose build --no-cache

# View logs
logs:
	docker-compose logs -f

# View API logs only
logs-api:
	docker-compose logs -f api

# View worker logs only
logs-worker:
	docker-compose logs -f worker

# Shell into API container
shell:
	docker-compose exec api bash

# Shell into database
db:
	docker-compose exec postgres psql -U postgres -d telegram_scraper

# Run migrations
migrate:
	docker-compose run --rm migrate

# Create new migration
migration:
	docker-compose exec api alembic revision --autogenerate -m "$(name)"

# Run tests
test:
	docker-compose exec api pytest

# Restart API (for code changes without volume mount)
restart-api:
	docker-compose restart api

# Restart worker
restart-worker:
	docker-compose restart worker

# Clean up everything (including volumes)
clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# Show running containers
ps:
	docker-compose ps

# Health check
health:
	curl -s http://localhost:8000/health | python -m json.tool

# Frontend logs
logs-frontend:
	docker-compose logs -f frontend

# Restart frontend
restart-frontend:
	docker-compose restart frontend

# Open UI in browser (macOS)
open-ui:
	open http://localhost:3000

# Open API docs in browser (macOS)
open-docs:
	open http://localhost:8000/docs
