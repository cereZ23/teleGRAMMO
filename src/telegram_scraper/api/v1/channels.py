"""Channel management endpoints."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import and_, select

from telegram_scraper.api.deps import CurrentUser, DbSession
from telegram_scraper.models.user_channel import UserChannel
from telegram_scraper.services.channel_service import ChannelService

router = APIRouter(prefix="/channels", tags=["channels"])


class ScheduleRequest(BaseModel):
    """Request to update channel schedule."""

    enabled: bool
    interval_hours: int | None = None  # 1, 6, 12, 24, etc.


class ScheduleResponse(BaseModel):
    """Response for channel schedule."""

    enabled: bool
    interval_hours: int | None
    last_scheduled_at: datetime | None
    next_scheduled_at: datetime | None


class AddChannelRequest:
    def __init__(self, session_id: UUID, telegram_id: int, scrape_media: bool = True):
        self.session_id = session_id
        self.telegram_id = telegram_id
        self.scrape_media = scrape_media


@router.get("")
async def list_channels(
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """List all channels tracked by the current user."""
    channels = await ChannelService.get_channels(db, current_user.id)
    return {"channels": channels, "total": len(channels)}


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_channel(
    session_id: UUID = Query(...),
    telegram_id: int = Query(...),
    db: DbSession = None,
    current_user: CurrentUser = None,
) -> dict:
    """Add a channel to track."""
    try:
        channel = await ChannelService.add_channel(
            db=db,
            user_id=current_user.id,
            session_id=session_id,
            telegram_id=telegram_id,
        )
        return {
            "id": channel.id,
            "telegram_id": channel.telegram_id,
            "username": channel.username,
            "title": channel.title,
            "channel_type": channel.channel_type,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/available")
async def get_available_channels(
    session_id: UUID = Query(...),
    db: DbSession = None,
    current_user: CurrentUser = None,
) -> list[dict]:
    """Get available channels from a Telegram session."""
    try:
        return await ChannelService.get_available_channels(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{channel_id}")
async def get_channel(
    channel_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Get a specific channel."""
    channel = await ChannelService.get_channel(db, channel_id, current_user.id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_channel(
    channel_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Remove a channel from tracking."""
    removed = await ChannelService.remove_channel(db, channel_id, current_user.id)
    if not removed:
        raise HTTPException(status_code=404, detail="Channel not found")


@router.get("/{channel_id}/messages")
async def get_channel_messages(
    channel_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: str = Query(None, description="Full-text search in message text"),
    media_type: str = Query(
        None, description="Filter by media type (photo, video, document, audio)"
    ),
    date_from: str = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: str = Query(None, description="Filter to date (YYYY-MM-DD)"),
    sender_id: int = Query(None, description="Filter by sender ID"),
) -> dict:
    """Get messages for a channel with advanced filters."""
    offset = (page - 1) * limit
    return await ChannelService.get_messages(
        db=db,
        channel_id=channel_id,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        search_query=search,
        media_type=media_type,
        date_from=date_from,
        date_to=date_to,
        sender_id=sender_id,
    )


@router.get("/{channel_id}/schedule")
async def get_channel_schedule(
    channel_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ScheduleResponse:
    """Get the schedule settings for a channel."""
    result = await db.execute(
        select(UserChannel).where(
            and_(
                UserChannel.channel_id == channel_id,
                UserChannel.user_id == current_user.id,
            )
        )
    )
    user_channel = result.scalar_one_or_none()

    if not user_channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    return ScheduleResponse(
        enabled=user_channel.schedule_enabled,
        interval_hours=user_channel.schedule_interval_hours,
        last_scheduled_at=user_channel.last_scheduled_at,
        next_scheduled_at=user_channel.next_scheduled_at,
    )


@router.put("/{channel_id}/schedule")
async def update_channel_schedule(
    channel_id: UUID,
    request: ScheduleRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> ScheduleResponse:
    """Update the schedule settings for a channel."""
    result = await db.execute(
        select(UserChannel).where(
            and_(
                UserChannel.channel_id == channel_id,
                UserChannel.user_id == current_user.id,
            )
        )
    )
    user_channel = result.scalar_one_or_none()

    if not user_channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    # Update schedule settings
    user_channel.schedule_enabled = request.enabled

    if request.enabled:
        if not request.interval_hours or request.interval_hours < 1:
            raise HTTPException(
                status_code=400, detail="interval_hours must be at least 1 when enabling schedule"
            )
        user_channel.schedule_interval_hours = request.interval_hours
        # Set next scheduled time to now + interval
        user_channel.next_scheduled_at = datetime.now(UTC) + timedelta(hours=request.interval_hours)
    else:
        user_channel.next_scheduled_at = None

    await db.commit()
    await db.refresh(user_channel)

    return ScheduleResponse(
        enabled=user_channel.schedule_enabled,
        interval_hours=user_channel.schedule_interval_hours,
        last_scheduled_at=user_channel.last_scheduled_at,
        next_scheduled_at=user_channel.next_scheduled_at,
    )
