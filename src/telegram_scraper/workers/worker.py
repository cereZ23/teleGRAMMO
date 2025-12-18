"""ARQ worker configuration and entry point."""

import logging
from typing import Any

from arq import cron
from arq.connections import RedisSettings

from telegram_scraper.config import settings
from telegram_scraper.workers.tasks.scrape_channel import scrape_channel
from telegram_scraper.workers.tasks.scheduler import check_scheduled_jobs
from telegram_scraper.workers.tasks.download_media import download_single_media, download_media_batch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def startup(ctx: dict[str, Any]) -> None:
    """Worker startup hook."""
    logger.info("Worker starting up...")


async def shutdown(ctx: dict[str, Any]) -> None:
    """Worker shutdown hook."""
    logger.info("Worker shutting down...")


async def scrape_channel_task(
    ctx: dict[str, Any],
    job_id: str,
    user_id: str,
    channel_id: str,
    session_id: str,
    from_message_id: int = 0,
    scrape_media: bool = True,
) -> dict[str, Any]:
    """Scrape messages from a Telegram channel."""
    logger.info(f"Starting scrape job {job_id} for channel {channel_id}")

    result = await scrape_channel(
        job_id=job_id,
        user_id=user_id,
        channel_id=channel_id,
        session_id=session_id,
        from_message_id=from_message_id,
        scrape_media=scrape_media,
    )

    return result


async def download_media_task(
    ctx: dict[str, Any],
    media_id: str,
    session_id: str,
) -> dict[str, Any]:
    """Download a single media file."""
    logger.info(f"Starting single media download for {media_id}")

    result = await download_single_media(
        media_id=media_id,
        session_id=session_id,
    )

    return result


async def download_media_batch_task(
    ctx: dict[str, Any],
    channel_id: str,
    session_id: str,
    limit: int = 10,
) -> dict[str, Any]:
    """Download a batch of pending media for a channel."""
    logger.info(f"Starting batch media download for channel {channel_id}")

    result = await download_media_batch(
        channel_id=channel_id,
        session_id=session_id,
        limit=limit,
    )

    return result


async def continuous_scrape_task(
    ctx: dict[str, Any],
    job_id: str,
    user_id: str,
    channel_ids: list[str],
    session_id: str,
    interval_seconds: int = 60,
) -> dict[str, Any]:
    """Continuously scrape multiple channels."""
    logger.info(f"Starting continuous scrape job {job_id}")

    # TODO: Implement continuous scraping
    return {
        "job_id": job_id,
        "status": "stopped",
    }


class WorkerSettings:
    """ARQ worker settings."""

    redis_settings = RedisSettings.from_dsn(settings.redis_url)

    functions = [
        scrape_channel_task,
        download_media_task,
        download_media_batch_task,
        continuous_scrape_task,
        check_scheduled_jobs,
    ]

    on_startup = startup
    on_shutdown = shutdown

    # Cron job to check for scheduled scrapes every minute
    cron_jobs = [
        cron(check_scheduled_jobs, minute=set(range(60))),  # Run every minute
    ]

    max_jobs = 10
    job_timeout = 3600  # 1 hour max per job
    keep_result = 3600  # Keep results for 1 hour
    health_check_interval = 30


if __name__ == "__main__":
    from arq.worker import run_worker

    run_worker(WorkerSettings)
