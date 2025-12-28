"""Job service for managing scraping jobs."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_scraper.models.scraping_job import ScrapingJob
from telegram_scraper.models.user_channel import UserChannel


class JobService:
    """Service for managing scraping jobs."""

    @classmethod
    async def create_job(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        channel_id: uuid.UUID,
        job_type: str,
        scrape_media: bool = True,
    ) -> ScrapingJob:
        """Create a new scraping job."""
        # Verify user has access to channel
        result = await db.execute(
            select(UserChannel).where(
                UserChannel.channel_id == channel_id,
                UserChannel.user_id == user_id,
                UserChannel.is_active,
            )
        )
        user_channel = result.scalar_one_or_none()
        if not user_channel:
            raise ValueError("Channel not found or not accessible")

        # Check for existing running job on this channel
        result = await db.execute(
            select(ScrapingJob).where(
                ScrapingJob.channel_id == channel_id,
                ScrapingJob.user_id == user_id,
                ScrapingJob.status.in_(["pending", "running"]),
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError("A job is already running for this channel")

        job = ScrapingJob(
            user_id=user_id,
            channel_id=channel_id,
            job_type=job_type,
            status="pending",
            progress_percent=0,
            messages_processed=0,
            media_downloaded=0,
            job_metadata={"scrape_media": scrape_media},
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    @classmethod
    async def get_jobs(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
        status_filter: str | None = None,
    ) -> dict[str, Any]:
        """Get jobs for a user."""
        query = select(ScrapingJob).where(ScrapingJob.user_id == user_id)

        if status_filter:
            query = query.where(ScrapingJob.status == status_filter)

        # Get total count
        count_query = select(func.count(ScrapingJob.id)).where(ScrapingJob.user_id == user_id)
        if status_filter:
            count_query = count_query.where(ScrapingJob.status == status_filter)
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Get jobs
        result = await db.execute(
            query.order_by(ScrapingJob.created_at.desc()).limit(limit).offset(offset)
        )
        jobs = result.scalars().all()

        return {
            "jobs": [
                {
                    "id": job.id,
                    "channel_id": job.channel_id,
                    "job_type": job.job_type,
                    "status": job.status,
                    "progress_percent": float(job.progress_percent),
                    "messages_processed": job.messages_processed,
                    "media_downloaded": job.media_downloaded,
                    "error_message": job.error_message,
                    "started_at": job.started_at,
                    "completed_at": job.completed_at,
                    "created_at": job.created_at,
                    "job_metadata": job.job_metadata,
                }
                for job in jobs
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    @classmethod
    async def get_job(
        cls, db: AsyncSession, job_id: uuid.UUID, user_id: uuid.UUID
    ) -> dict[str, Any] | None:
        """Get a specific job."""
        result = await db.execute(
            select(ScrapingJob).where(
                ScrapingJob.id == job_id,
                ScrapingJob.user_id == user_id,
            )
        )
        job = result.scalar_one_or_none()
        if not job:
            return None

        return {
            "id": job.id,
            "channel_id": job.channel_id,
            "job_type": job.job_type,
            "status": job.status,
            "progress_percent": float(job.progress_percent),
            "messages_processed": job.messages_processed,
            "media_downloaded": job.media_downloaded,
            "error_message": job.error_message,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "created_at": job.created_at,
            "job_metadata": job.job_metadata,
        }

    @classmethod
    async def cancel_job(cls, db: AsyncSession, job_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Cancel a running job."""
        result = await db.execute(
            select(ScrapingJob).where(
                ScrapingJob.id == job_id,
                ScrapingJob.user_id == user_id,
            )
        )
        job = result.scalar_one_or_none()
        if not job:
            return False

        if job.status not in ["pending", "running"]:
            raise ValueError("Can only cancel pending or running jobs")

        job.status = "cancelled"
        job.completed_at = datetime.now(UTC)
        await db.commit()
        return True

    @classmethod
    async def update_job_progress(
        cls,
        db: AsyncSession,
        job_id: uuid.UUID,
        status: str | None = None,
        progress_percent: float | None = None,
        messages_processed: int | None = None,
        media_downloaded: int | None = None,
        error_message: str | None = None,
    ) -> None:
        """Update job progress (called by workers)."""
        result = await db.execute(select(ScrapingJob).where(ScrapingJob.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return

        if status:
            job.status = status
            if status == "running" and not job.started_at:
                job.started_at = datetime.now(UTC)
            elif status in ["completed", "failed", "cancelled"]:
                job.completed_at = datetime.now(UTC)

        if progress_percent is not None:
            job.progress_percent = progress_percent
        if messages_processed is not None:
            job.messages_processed = messages_processed
        if media_downloaded is not None:
            job.media_downloaded = media_downloaded
        if error_message is not None:
            job.error_message = error_message

        await db.commit()
