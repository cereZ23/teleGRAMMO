"""Job management endpoints."""

from uuid import UUID

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select

from telegram_scraper.api.deps import CurrentUser, DbSession
from telegram_scraper.config import settings
from telegram_scraper.models.telegram_session import TelegramSession
from telegram_scraper.models.user_channel import UserChannel
from telegram_scraper.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


class CreateJobRequest(BaseModel):
    channel_id: UUID
    job_type: str = "incremental"
    scrape_media: bool = True


async def get_redis_pool():
    """Get ARQ Redis pool."""
    return await create_pool(RedisSettings.from_dsn(settings.redis_url))


@router.get("")
async def list_jobs(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    status: str | None = Query(None),
) -> dict:
    """List jobs for the current user."""
    offset = (page - 1) * limit
    return await JobService.get_jobs(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        status_filter=status,
    )


@router.post("/scrape", status_code=status.HTTP_201_CREATED)
async def create_scrape_job(
    request: CreateJobRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Create a new scraping job and queue it."""
    try:
        # Create job in database
        job = await JobService.create_job(
            db=db,
            user_id=current_user.id,
            channel_id=request.channel_id,
            job_type=request.job_type,
            scrape_media=request.scrape_media,
        )

        # Get user's first authenticated session
        result = await db.execute(
            select(TelegramSession)
            .where(
                TelegramSession.user_id == current_user.id,
                TelegramSession.is_authenticated,
            )
            .limit(1)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError("No authenticated Telegram session found")

        # Get last scraped message ID for incremental
        from_message_id = 0
        if request.job_type == "incremental":
            result = await db.execute(
                select(UserChannel).where(
                    UserChannel.user_id == current_user.id,
                    UserChannel.channel_id == request.channel_id,
                )
            )
            user_channel = result.scalar_one_or_none()
            if user_channel:
                from_message_id = user_channel.last_scraped_message_id or 0

        # Queue the job with ARQ
        redis = await get_redis_pool()
        await redis.enqueue_job(
            "scrape_channel_task",
            job_id=str(job.id),
            user_id=str(current_user.id),
            channel_id=str(request.channel_id),
            session_id=str(session.id),
            from_message_id=from_message_id,
            scrape_media=request.scrape_media,
        )
        await redis.close()

        return {
            "id": job.id,
            "channel_id": job.channel_id,
            "job_type": job.job_type,
            "status": job.status,
            "created_at": job.created_at,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{job_id}")
async def get_job(
    job_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Get a specific job."""
    job = await JobService.get_job(db, job_id, current_user.id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Cancel a running job."""
    try:
        cancelled = await JobService.cancel_job(db, job_id, current_user.id)
        if not cancelled:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"status": "cancelled"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
