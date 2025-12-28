"""Scheduler service for managing scheduled scraping jobs."""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from telegram_scraper.models.scraping_job import ScrapingJob
from telegram_scraper.models.telegram_session import TelegramSession
from telegram_scraper.models.user_channel import UserChannel

logger = logging.getLogger(__name__)


async def get_due_schedules(db: AsyncSession) -> list[UserChannel]:
    """Get all user_channels that are due for scheduled scraping."""
    now = datetime.now(UTC)

    result = await db.execute(
        select(UserChannel)
        .options(joinedload(UserChannel.channel), joinedload(UserChannel.user))
        .where(
            and_(
                UserChannel.schedule_enabled,
                UserChannel.is_active,
                UserChannel.next_scheduled_at <= now,
            )
        )
    )
    return list(result.scalars().unique().all())


async def get_user_session(db: AsyncSession, user_id: UUID) -> TelegramSession | None:
    """Get an authenticated Telegram session for a user."""
    result = await db.execute(
        select(TelegramSession).where(
            and_(
                TelegramSession.user_id == user_id,
                TelegramSession.is_authenticated,
            )
        )
    )
    return result.scalar_one_or_none()


async def has_active_job(db: AsyncSession, channel_id: UUID) -> bool:
    """Check if there's already an active job for this channel."""
    result = await db.execute(
        select(ScrapingJob).where(
            and_(
                ScrapingJob.channel_id == channel_id,
                ScrapingJob.status.in_(["pending", "running"]),
            )
        )
    )
    return result.scalar_one_or_none() is not None


async def update_schedule(
    db: AsyncSession,
    user_channel: UserChannel,
    enabled: bool,
    interval_hours: int | None = None,
) -> UserChannel:
    """Update the schedule settings for a user channel."""
    user_channel.schedule_enabled = enabled

    if enabled and interval_hours:
        user_channel.schedule_interval_hours = interval_hours
        # Set next scheduled time
        user_channel.next_scheduled_at = datetime.now(UTC) + timedelta(hours=interval_hours)
    elif not enabled:
        user_channel.next_scheduled_at = None

    await db.commit()
    await db.refresh(user_channel)
    return user_channel


async def calculate_next_run(user_channel: UserChannel) -> datetime:
    """Calculate the next scheduled run time."""
    interval = user_channel.schedule_interval_hours or 24
    return datetime.now(UTC) + timedelta(hours=interval)


async def mark_scheduled_run(db: AsyncSession, user_channel: UserChannel) -> None:
    """Mark that a scheduled run has been triggered."""
    user_channel.last_scheduled_at = datetime.now(UTC)
    user_channel.next_scheduled_at = await calculate_next_run(user_channel)
    await db.commit()
