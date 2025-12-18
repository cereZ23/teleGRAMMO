"""Media endpoints for accessing downloaded files."""

import os
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select, func

from telegram_scraper.api.deps import CurrentUser, DbSession
from telegram_scraper.config import settings
from telegram_scraper.models.media import Media
from telegram_scraper.models.channel import Channel
from telegram_scraper.models.user_channel import UserChannel

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
    query = select(Media).join(Channel).join(UserChannel).where(
        UserChannel.user_id == current_user.id,
        UserChannel.is_active == True,
    )

    count_query = select(func.count(Media.id)).join(Channel).join(UserChannel).where(
        UserChannel.user_id == current_user.id,
        UserChannel.is_active == True,
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
    result = await db.execute(
        query.order_by(Media.created_at.desc()).limit(limit).offset(offset)
    )
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
        select(Media).join(Channel).join(UserChannel).where(
            Media.id == media_id,
            UserChannel.user_id == current_user.id,
            UserChannel.is_active == True,
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
        select(Media).join(Channel).join(UserChannel).where(
            Media.id == media_id,
            UserChannel.user_id == current_user.id,
            UserChannel.is_active == True,
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
