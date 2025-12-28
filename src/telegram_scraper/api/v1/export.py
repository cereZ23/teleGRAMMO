"""Export endpoints for downloading data as CSV/JSON."""

import csv
import io
import json
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from telegram_scraper.api.deps import CurrentUser, DbSession
from telegram_scraper.models.channel import Channel
from telegram_scraper.models.message import Message
from telegram_scraper.models.user_channel import UserChannel

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/channels/{channel_id}/csv")
async def export_channel_csv(
    channel_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(None, description="Max rows to export"),
) -> StreamingResponse:
    """Export channel messages as CSV."""
    # Verify access
    result = await db.execute(
        select(UserChannel).where(
            UserChannel.channel_id == channel_id,
            UserChannel.user_id == current_user.id,
            UserChannel.is_active,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Channel not found")

    # Get channel info
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()

    # Get messages
    query = select(Message).where(Message.channel_id == channel_id).order_by(Message.date.desc())
    if limit:
        query = query.limit(limit)

    result = await db.execute(query)
    messages = result.scalars().all()

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(
        [
            "telegram_message_id",
            "date",
            "sender_id",
            "first_name",
            "last_name",
            "username",
            "message_text",
            "media_type",
            "views",
            "forwards",
        ]
    )

    # Data rows
    for msg in messages:
        writer.writerow(
            [
                msg.telegram_message_id,
                msg.date.isoformat() if msg.date else "",
                msg.sender_id or "",
                msg.first_name or "",
                msg.last_name or "",
                msg.username or "",
                msg.message_text or "",
                msg.media_type or "",
                msg.views or 0,
                msg.forwards or 0,
            ]
        )

    output.seek(0)

    filename = f"{channel.username or channel_id}_messages.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/channels/{channel_id}/json")
async def export_channel_json(
    channel_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(None, description="Max rows to export"),
) -> StreamingResponse:
    """Export channel messages as JSON."""
    # Verify access
    result = await db.execute(
        select(UserChannel).where(
            UserChannel.channel_id == channel_id,
            UserChannel.user_id == current_user.id,
            UserChannel.is_active,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Channel not found")

    # Get channel info
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()

    # Get messages
    query = select(Message).where(Message.channel_id == channel_id).order_by(Message.date.desc())
    if limit:
        query = query.limit(limit)

    result = await db.execute(query)
    messages = result.scalars().all()

    # Build JSON
    data = {
        "channel": {
            "id": str(channel.id),
            "telegram_id": channel.telegram_id,
            "username": channel.username,
            "title": channel.title,
        },
        "messages": [
            {
                "telegram_message_id": msg.telegram_message_id,
                "date": msg.date.isoformat() if msg.date else None,
                "sender_id": msg.sender_id,
                "first_name": msg.first_name,
                "last_name": msg.last_name,
                "username": msg.username,
                "message_text": msg.message_text,
                "media_type": msg.media_type,
                "views": msg.views,
                "forwards": msg.forwards,
                "reactions": msg.reactions,
            }
            for msg in messages
        ],
        "total_messages": len(messages),
    }

    output = json.dumps(data, indent=2, ensure_ascii=False)
    filename = f"{channel.username or channel_id}_messages.json"

    return StreamingResponse(
        iter([output]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
