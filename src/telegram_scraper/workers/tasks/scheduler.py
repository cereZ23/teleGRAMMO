"""Scheduler task for checking and queuing due scraping jobs."""

import logging

from arq import ArqRedis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from telegram_scraper.config import settings
from telegram_scraper.models.scraping_job import ScrapingJob
from telegram_scraper.services.scheduler_service import (
    get_due_schedules,
    get_user_session,
    has_active_job,
    mark_scheduled_run,
)

logger = logging.getLogger(__name__)


async def get_db_session() -> AsyncSession:
    """Create a database session for the scheduler."""
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return async_session()


async def check_scheduled_jobs(ctx: dict) -> dict:
    """
    Check for due scheduled jobs and queue them.

    This task runs periodically (e.g., every minute) to check if any
    scheduled scraping jobs are due and queues them for execution.
    """
    redis: ArqRedis = ctx["redis"]
    db = await get_db_session()
    jobs_queued = 0

    try:
        # Get all due schedules
        due_schedules = await get_due_schedules(db)
        logger.info(f"Found {len(due_schedules)} due scheduled scrapes")

        for user_channel in due_schedules:
            try:
                # Skip if there's already an active job for this channel
                if await has_active_job(db, user_channel.channel_id):
                    logger.info(f"Skipping channel {user_channel.channel_id} - job already active")
                    # Still update next_scheduled_at to prevent retrying immediately
                    await mark_scheduled_run(db, user_channel)
                    continue

                # Get an authenticated session for this user
                session = await get_user_session(db, user_channel.user_id)
                if not session:
                    logger.warning(f"No authenticated session for user {user_channel.user_id}")
                    continue

                # Create a scraping job
                job = ScrapingJob(
                    user_id=user_channel.user_id,
                    channel_id=user_channel.channel_id,
                    session_id=session.id,
                    job_type="scheduled",
                    status="pending",
                )
                db.add(job)
                await db.commit()
                await db.refresh(job)

                # Queue the scraping task
                await redis.enqueue_job(
                    "scrape_channel_task",
                    job_id=str(job.id),
                    user_id=str(user_channel.user_id),
                    channel_id=str(user_channel.channel_id),
                    session_id=str(session.id),
                    from_message_id=user_channel.last_scraped_message_id or 0,
                )

                # Update the schedule
                await mark_scheduled_run(db, user_channel)
                jobs_queued += 1

                logger.info(
                    f"Queued scheduled scrape for channel {user_channel.channel.title} "
                    f"(user: {user_channel.user_id})"
                )

            except Exception as e:
                logger.error(
                    f"Error processing schedule for channel {user_channel.channel_id}: {e}"
                )
                continue

        return {"jobs_queued": jobs_queued}

    except Exception as e:
        logger.error(f"Error in scheduler task: {e}")
        return {"error": str(e)}

    finally:
        await db.close()
