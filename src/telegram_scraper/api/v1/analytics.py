"""Analytics endpoints for channel statistics."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import and_, func, select, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_scraper.api.deps import CurrentUser, DbSession
from telegram_scraper.models.channel import Channel
from telegram_scraper.models.message import Message
from telegram_scraper.models.media import Media
from telegram_scraper.models.user_channel import UserChannel

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
async def get_overview(
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Get overall analytics for all user's channels."""
    # Get user's channel IDs
    result = await db.execute(
        select(UserChannel.channel_id).where(UserChannel.user_id == current_user.id)
    )
    channel_ids = [row[0] for row in result.fetchall()]

    if not channel_ids:
        return {
            "total_channels": 0,
            "total_messages": 0,
            "total_media": 0,
            "messages_today": 0,
            "messages_this_week": 0,
        }

    # Total messages
    result = await db.execute(
        select(func.count(Message.id)).where(Message.channel_id.in_(channel_ids))
    )
    total_messages = result.scalar() or 0

    # Total media
    result = await db.execute(
        select(func.count(Media.id)).where(Media.channel_id.in_(channel_ids))
    )
    total_media = result.scalar() or 0

    # Messages today
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.count(Message.id)).where(
            and_(
                Message.channel_id.in_(channel_ids),
                Message.date >= today,
            )
        )
    )
    messages_today = result.scalar() or 0

    # Messages this week
    week_ago = today - timedelta(days=7)
    result = await db.execute(
        select(func.count(Message.id)).where(
            and_(
                Message.channel_id.in_(channel_ids),
                Message.date >= week_ago,
            )
        )
    )
    messages_this_week = result.scalar() or 0

    return {
        "total_channels": len(channel_ids),
        "total_messages": total_messages,
        "total_media": total_media,
        "messages_today": messages_today,
        "messages_this_week": messages_this_week,
    }


@router.get("/messages-over-time")
async def get_messages_over_time(
    db: DbSession,
    current_user: CurrentUser,
    channel_id: Optional[UUID] = Query(None),
    days: int = Query(30, ge=1, le=365),
) -> dict:
    """Get message counts grouped by date."""
    # Get user's channel IDs
    if channel_id:
        # Verify user owns this channel
        result = await db.execute(
            select(UserChannel).where(
                and_(
                    UserChannel.user_id == current_user.id,
                    UserChannel.channel_id == channel_id,
                )
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Channel not found")
        channel_ids = [channel_id]
    else:
        result = await db.execute(
            select(UserChannel.channel_id).where(UserChannel.user_id == current_user.id)
        )
        channel_ids = [row[0] for row in result.fetchall()]

    if not channel_ids:
        return {"data": []}

    # Get message counts by date
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            cast(Message.date, Date).label("date"),
            func.count(Message.id).label("count"),
        )
        .where(
            and_(
                Message.channel_id.in_(channel_ids),
                Message.date >= start_date,
            )
        )
        .group_by(cast(Message.date, Date))
        .order_by(cast(Message.date, Date))
    )

    data = [{"date": str(row.date), "count": row.count} for row in result.fetchall()]

    return {"data": data}


@router.get("/top-senders")
async def get_top_senders(
    db: DbSession,
    current_user: CurrentUser,
    channel_id: Optional[UUID] = Query(None),
    limit: int = Query(10, ge=1, le=50),
) -> dict:
    """Get top message senders."""
    # Get user's channel IDs
    if channel_id:
        result = await db.execute(
            select(UserChannel).where(
                and_(
                    UserChannel.user_id == current_user.id,
                    UserChannel.channel_id == channel_id,
                )
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Channel not found")
        channel_ids = [channel_id]
    else:
        result = await db.execute(
            select(UserChannel.channel_id).where(UserChannel.user_id == current_user.id)
        )
        channel_ids = [row[0] for row in result.fetchall()]

    if not channel_ids:
        return {"data": []}

    # Get top senders (excluding null sender_id for channel posts)
    result = await db.execute(
        select(
            Message.sender_id,
            Message.first_name,
            Message.last_name,
            Message.username,
            func.count(Message.id).label("count"),
        )
        .where(
            and_(
                Message.channel_id.in_(channel_ids),
                Message.sender_id.isnot(None),
            )
        )
        .group_by(Message.sender_id, Message.first_name, Message.last_name, Message.username)
        .order_by(func.count(Message.id).desc())
        .limit(limit)
    )

    data = []
    for row in result.fetchall():
        name = ""
        if row.first_name:
            name = row.first_name
        if row.last_name:
            name = f"{name} {row.last_name}".strip()
        if not name and row.username:
            name = f"@{row.username}"
        if not name:
            name = f"User {row.sender_id}"

        data.append({
            "sender_id": row.sender_id,
            "name": name,
            "username": row.username,
            "count": row.count,
        })

    return {"data": data}


@router.get("/media-breakdown")
async def get_media_breakdown(
    db: DbSession,
    current_user: CurrentUser,
    channel_id: Optional[UUID] = Query(None),
) -> dict:
    """Get media type breakdown."""
    # Get user's channel IDs
    if channel_id:
        result = await db.execute(
            select(UserChannel).where(
                and_(
                    UserChannel.user_id == current_user.id,
                    UserChannel.channel_id == channel_id,
                )
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Channel not found")
        channel_ids = [channel_id]
    else:
        result = await db.execute(
            select(UserChannel.channel_id).where(UserChannel.user_id == current_user.id)
        )
        channel_ids = [row[0] for row in result.fetchall()]

    if not channel_ids:
        return {"data": []}

    # Get media type counts
    result = await db.execute(
        select(
            Message.media_type,
            func.count(Message.id).label("count"),
        )
        .where(
            and_(
                Message.channel_id.in_(channel_ids),
                Message.media_type.isnot(None),
            )
        )
        .group_by(Message.media_type)
        .order_by(func.count(Message.id).desc())
    )

    data = [{"type": row.media_type, "count": row.count} for row in result.fetchall()]

    return {"data": data}


@router.get("/activity-heatmap")
async def get_activity_heatmap(
    db: DbSession,
    current_user: CurrentUser,
    channel_id: Optional[UUID] = Query(None),
    days: int = Query(90, ge=1, le=365),
) -> dict:
    """Get message activity by hour of day and day of week."""
    # Get user's channel IDs
    if channel_id:
        result = await db.execute(
            select(UserChannel).where(
                and_(
                    UserChannel.user_id == current_user.id,
                    UserChannel.channel_id == channel_id,
                )
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Channel not found")
        channel_ids = [channel_id]
    else:
        result = await db.execute(
            select(UserChannel.channel_id).where(UserChannel.user_id == current_user.id)
        )
        channel_ids = [row[0] for row in result.fetchall()]

    if not channel_ids:
        return {"data": []}

    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Get activity by hour
    result = await db.execute(
        select(
            func.extract("hour", Message.date).label("hour"),
            func.count(Message.id).label("count"),
        )
        .where(
            and_(
                Message.channel_id.in_(channel_ids),
                Message.date >= start_date,
            )
        )
        .group_by(func.extract("hour", Message.date))
        .order_by(func.extract("hour", Message.date))
    )

    hourly_data = [{"hour": int(row.hour), "count": row.count} for row in result.fetchall()]

    # Get activity by day of week
    result = await db.execute(
        select(
            func.extract("dow", Message.date).label("day"),
            func.count(Message.id).label("count"),
        )
        .where(
            and_(
                Message.channel_id.in_(channel_ids),
                Message.date >= start_date,
            )
        )
        .group_by(func.extract("dow", Message.date))
        .order_by(func.extract("dow", Message.date))
    )

    day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    daily_data = [{"day": day_names[int(row.day)], "count": row.count} for row in result.fetchall()]

    return {
        "hourly": hourly_data,
        "daily": daily_data,
    }


@router.get("/channel-stats")
async def get_channel_stats(
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Get stats for each channel."""
    # Get user's channels with stats
    result = await db.execute(
        select(UserChannel)
        .where(UserChannel.user_id == current_user.id)
    )
    user_channels = result.scalars().all()

    channel_ids = [uc.channel_id for uc in user_channels]
    if not channel_ids:
        return {"data": []}

    # Get channel details
    result = await db.execute(
        select(Channel).where(Channel.id.in_(channel_ids))
    )
    channels = {c.id: c for c in result.scalars().all()}

    # Get message counts per channel
    result = await db.execute(
        select(
            Message.channel_id,
            func.count(Message.id).label("message_count"),
        )
        .where(Message.channel_id.in_(channel_ids))
        .group_by(Message.channel_id)
    )
    message_counts = {row.channel_id: row.message_count for row in result.fetchall()}

    # Get media counts per channel
    result = await db.execute(
        select(
            Media.channel_id,
            func.count(Media.id).label("media_count"),
        )
        .where(Media.channel_id.in_(channel_ids))
        .group_by(Media.channel_id)
    )
    media_counts = {row.channel_id: row.media_count for row in result.fetchall()}

    data = []
    for uc in user_channels:
        channel = channels.get(uc.channel_id)
        if channel:
            data.append({
                "id": str(channel.id),
                "title": channel.title,
                "username": channel.username,
                "message_count": message_counts.get(channel.id, 0),
                "media_count": media_counts.get(channel.id, 0),
                "schedule_enabled": uc.schedule_enabled,
            })

    # Sort by message count
    data.sort(key=lambda x: x["message_count"], reverse=True)

    return {"data": data}
