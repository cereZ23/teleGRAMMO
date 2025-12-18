"""Main API v1 router."""

from fastapi import APIRouter

from telegram_scraper.api.v1.auth import router as auth_router
from telegram_scraper.api.v1.telegram import router as telegram_router
from telegram_scraper.api.v1.channels import router as channels_router
from telegram_scraper.api.v1.jobs import router as jobs_router
from telegram_scraper.api.v1.export import router as export_router
from telegram_scraper.api.v1.media import router as media_router
from telegram_scraper.api.v1.analytics import router as analytics_router

api_router = APIRouter()

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(telegram_router)
api_router.include_router(channels_router)
api_router.include_router(jobs_router)
api_router.include_router(export_router)
api_router.include_router(media_router)
api_router.include_router(analytics_router)
