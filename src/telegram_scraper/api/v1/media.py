"""Media endpoints for accessing downloaded files."""

import os
from uuid import UUID

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import func, select

from telegram_scraper.api.deps import CurrentUser, DbSession
from telegram_scraper.config import settings
from telegram_scraper.models.channel import Channel
from telegram_scraper.models.media import Media
from telegram_scraper.models.telegram_session import TelegramSession
from telegram_scraper.models.user_channel import UserChannel


class DownloadRequest(BaseModel):
    """Request to download media."""

    session_id: UUID


class BatchDownloadRequest(BaseModel):
    """Request to download media batch."""

    session_id: UUID
    channel_id: UUID
    limit: int = 10


router = APIRouter(prefix="/media", tags=["media"])


@router.get("")
async def list_media(
    db: DbSession,
    current_user: CurrentUser,
    channel_id: UUID = Query(None),
    status: str = Query(None, description="Filter by download status"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
) -> dict:
    """List media files."""
    # Build query
    query = (
        select(Media)
        .join(Channel)
        .join(UserChannel)
        .where(
            UserChannel.user_id == current_user.id,
            UserChannel.is_active,
        )
    )

    count_query = (
        select(func.count(Media.id))
        .join(Channel)
        .join(UserChannel)
        .where(
            UserChannel.user_id == current_user.id,
            UserChannel.is_active,
        )
    )

    if channel_id:
        query = query.where(Media.channel_id == channel_id)
        count_query = count_query.where(Media.channel_id == channel_id)

    if status:
        query = query.where(Media.download_status == status)
        count_query = count_query.where(Media.download_status == status)

    # Get total
    result = await db.execute(count_query)
    total = result.scalar() or 0

    # Get media
    offset = (page - 1) * limit
    result = await db.execute(query.order_by(Media.created_at.desc()).limit(limit).offset(offset))
    media_list = result.scalars().all()

    return {
        "media": [
            {
                "id": m.id,
                "channel_id": m.channel_id,
                "telegram_message_id": m.telegram_message_id,
                "media_type": m.media_type,
                "file_name": m.file_name,
                "file_size": m.file_size,
                "mime_type": m.mime_type,
                "download_status": m.download_status,
                "created_at": m.created_at,
                "downloaded_at": m.downloaded_at,
            }
            for m in media_list
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/{media_id}")
async def get_media(
    media_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Get media file info."""
    result = await db.execute(
        select(Media)
        .join(Channel)
        .join(UserChannel)
        .where(
            Media.id == media_id,
            UserChannel.user_id == current_user.id,
            UserChannel.is_active,
        )
    )
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    return {
        "id": media.id,
        "channel_id": media.channel_id,
        "telegram_message_id": media.telegram_message_id,
        "media_type": media.media_type,
        "file_path": media.file_path,
        "file_name": media.file_name,
        "file_size": media.file_size,
        "mime_type": media.mime_type,
        "download_status": media.download_status,
        "download_attempts": media.download_attempts,
        "error_message": media.error_message,
        "created_at": media.created_at,
        "downloaded_at": media.downloaded_at,
    }


@router.get("/{media_id}/download")
async def download_media(
    media_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> FileResponse:
    """Download a media file."""
    result = await db.execute(
        select(Media)
        .join(Channel)
        .join(UserChannel)
        .where(
            Media.id == media_id,
            UserChannel.user_id == current_user.id,
            UserChannel.is_active,
        )
    )
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    if media.download_status != "completed":
        raise HTTPException(status_code=400, detail="Media not yet downloaded")

    if not media.file_path:
        raise HTTPException(status_code=400, detail="File path not available")

    file_path = os.path.join(settings.media_storage_path, media.file_path)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=file_path,
        filename=media.file_name or f"media_{media_id}",
        media_type=media.mime_type or "application/octet-stream",
    )


@router.post("/{media_id}/start-download")
async def start_media_download(
    media_id: UUID,
    request: DownloadRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Start downloading a single media file."""
    # Verify user owns this media
    result = await db.execute(
        select(Media)
        .join(Channel)
        .join(UserChannel)
        .where(
            Media.id == media_id,
            UserChannel.user_id == current_user.id,
            UserChannel.is_active,
        )
    )
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    if media.download_status == "completed":
        return {"status": "already_completed", "media_id": str(media_id)}

    if media.download_status == "downloading":
        return {"status": "already_downloading", "media_id": str(media_id)}

    # Verify session belongs to user
    result = await db.execute(
        select(TelegramSession).where(
            TelegramSession.id == request.session_id,
            TelegramSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=400, detail="Invalid session")

    # Queue the download task
    redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    await redis.enqueue_job(
        "download_media_task",
        str(media_id),
        str(request.session_id),
    )
    await redis.close()

    return {"status": "queued", "media_id": str(media_id)}


@router.post("/batch-download")
async def start_batch_download(
    request: BatchDownloadRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Start downloading a batch of pending media for a channel."""
    # Verify user owns this channel
    result = await db.execute(
        select(UserChannel).where(
            UserChannel.channel_id == request.channel_id,
            UserChannel.user_id == current_user.id,
            UserChannel.is_active,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Channel not found")

    # Verify session belongs to user
    result = await db.execute(
        select(TelegramSession).where(
            TelegramSession.id == request.session_id,
            TelegramSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=400, detail="Invalid session")

    # Count pending media
    result = await db.execute(
        select(func.count(Media.id)).where(
            Media.channel_id == request.channel_id,
            Media.download_status == "pending",
        )
    )
    pending_count = result.scalar() or 0

    if pending_count == 0:
        return {"status": "no_pending_media", "pending_count": 0}

    # Queue the batch download task
    redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    await redis.enqueue_job(
        "download_media_batch_task",
        str(request.channel_id),
        str(request.session_id),
        request.limit,
    )
    await redis.close()

    return {
        "status": "queued",
        "channel_id": str(request.channel_id),
        "pending_count": pending_count,
        "batch_size": min(request.limit, pending_count),
    }


@router.get("/channel/{channel_id}/stats")
async def get_channel_media_stats(
    channel_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Get media download stats for a channel."""
    # Verify user owns this channel
    result = await db.execute(
        select(UserChannel).where(
            UserChannel.channel_id == channel_id,
            UserChannel.user_id == current_user.id,
            UserChannel.is_active,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Channel not found")

    # Get stats by status
    result = await db.execute(
        select(Media.download_status, func.count(Media.id))
        .where(Media.channel_id == channel_id)
        .group_by(Media.download_status)
    )
    status_counts = dict(result.all())

    # Get stats by type
    result = await db.execute(
        select(Media.media_type, func.count(Media.id))
        .where(Media.channel_id == channel_id)
        .group_by(Media.media_type)
    )
    type_counts = dict(result.all())

    # Get total size of downloaded media
    result = await db.execute(
        select(func.sum(Media.file_size)).where(
            Media.channel_id == channel_id,
            Media.download_status == "completed",
        )
    )
    total_size = result.scalar() or 0

    return {
        "channel_id": str(channel_id),
        "by_status": {
            "pending": status_counts.get("pending", 0),
            "downloading": status_counts.get("downloading", 0),
            "completed": status_counts.get("completed", 0),
            "failed": status_counts.get("failed", 0),
        },
        "by_type": type_counts,
        "total_downloaded_size": total_size,
    }
