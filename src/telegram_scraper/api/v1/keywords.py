"""Keyword Alerts API endpoints."""

import re
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, func, select, update

from telegram_scraper.api.deps import CurrentUser, DbSession
from telegram_scraper.models.keyword_alert import KeywordAlert, KeywordMatch
from telegram_scraper.models.channel import Channel
from telegram_scraper.models.message import Message
from telegram_scraper.models.user_channel import UserChannel

router = APIRouter(prefix="/keywords", tags=["keywords"])


class KeywordAlertCreate(BaseModel):
    """Request to create a keyword alert."""
    keyword: str
    channel_id: Optional[UUID] = None  # None = all channels
    is_regex: bool = False
    is_case_sensitive: bool = False
    notify_webhook: Optional[str] = None


class KeywordAlertUpdate(BaseModel):
    """Request to update a keyword alert."""
    keyword: Optional[str] = None
    channel_id: Optional[UUID] = None
    is_regex: Optional[bool] = None
    is_case_sensitive: Optional[bool] = None
    is_active: Optional[bool] = None
    notify_webhook: Optional[str] = None


class KeywordAlertResponse(BaseModel):
    """Response for a keyword alert."""
    id: UUID
    keyword: str
    channel_id: Optional[UUID]
    channel_title: Optional[str]
    is_regex: bool
    is_case_sensitive: bool
    is_active: bool
    notify_webhook: Optional[str]
    match_count: int
    last_match_at: Optional[datetime]
    created_at: datetime


class KeywordMatchResponse(BaseModel):
    """Response for a keyword match."""
    id: UUID
    keyword_alert_id: UUID
    keyword: str
    message_id: UUID
    channel_id: UUID
    channel_title: Optional[str]
    matched_text: Optional[str]
    message_date: Optional[datetime]
    is_read: bool
    created_at: datetime


@router.get("")
async def list_keyword_alerts(
    db: DbSession,
    current_user: CurrentUser,
    channel_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
) -> dict:
    """List all keyword alerts for the current user."""
    query = select(KeywordAlert).where(KeywordAlert.user_id == current_user.id)

    if channel_id:
        query = query.where(KeywordAlert.channel_id == channel_id)
    if is_active is not None:
        query = query.where(KeywordAlert.is_active == is_active)

    result = await db.execute(query.order_by(KeywordAlert.created_at.desc()))
    alerts = result.scalars().all()

    # Get channel titles
    channel_ids = [a.channel_id for a in alerts if a.channel_id]
    channel_titles = {}
    if channel_ids:
        result = await db.execute(
            select(Channel.id, Channel.title).where(Channel.id.in_(channel_ids))
        )
        channel_titles = dict(result.all())

    return {
        "alerts": [
            {
                "id": alert.id,
                "keyword": alert.keyword,
                "channel_id": alert.channel_id,
                "channel_title": channel_titles.get(alert.channel_id) if alert.channel_id else "All Channels",
                "is_regex": alert.is_regex,
                "is_case_sensitive": alert.is_case_sensitive,
                "is_active": alert.is_active,
                "notify_webhook": alert.notify_webhook,
                "match_count": alert.match_count,
                "last_match_at": alert.last_match_at,
                "created_at": alert.created_at,
            }
            for alert in alerts
        ],
        "total": len(alerts),
    }


@router.post("", status_code=201)
async def create_keyword_alert(
    request: KeywordAlertCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Create a new keyword alert."""
    # Validate regex if provided
    if request.is_regex:
        try:
            re.compile(request.keyword)
        except re.error as e:
            raise HTTPException(status_code=400, detail=f"Invalid regex: {e}")

    # Validate channel if provided
    if request.channel_id:
        result = await db.execute(
            select(UserChannel).where(
                UserChannel.channel_id == request.channel_id,
                UserChannel.user_id == current_user.id,
                UserChannel.is_active == True,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Channel not found")

    # Check for duplicate
    result = await db.execute(
        select(KeywordAlert).where(
            KeywordAlert.user_id == current_user.id,
            KeywordAlert.keyword == request.keyword,
            KeywordAlert.channel_id == request.channel_id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Keyword alert already exists")

    alert = KeywordAlert(
        user_id=current_user.id,
        keyword=request.keyword,
        channel_id=request.channel_id,
        is_regex=request.is_regex,
        is_case_sensitive=request.is_case_sensitive,
        notify_webhook=request.notify_webhook,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    return {
        "id": alert.id,
        "keyword": alert.keyword,
        "channel_id": alert.channel_id,
        "is_regex": alert.is_regex,
        "is_case_sensitive": alert.is_case_sensitive,
        "is_active": alert.is_active,
        "created_at": alert.created_at,
    }


@router.get("/{alert_id}")
async def get_keyword_alert(
    alert_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Get a specific keyword alert."""
    result = await db.execute(
        select(KeywordAlert).where(
            KeywordAlert.id == alert_id,
            KeywordAlert.user_id == current_user.id,
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Keyword alert not found")

    channel_title = None
    if alert.channel_id:
        result = await db.execute(
            select(Channel.title).where(Channel.id == alert.channel_id)
        )
        channel_title = result.scalar()

    return {
        "id": alert.id,
        "keyword": alert.keyword,
        "channel_id": alert.channel_id,
        "channel_title": channel_title or "All Channels",
        "is_regex": alert.is_regex,
        "is_case_sensitive": alert.is_case_sensitive,
        "is_active": alert.is_active,
        "notify_webhook": alert.notify_webhook,
        "match_count": alert.match_count,
        "last_match_at": alert.last_match_at,
        "created_at": alert.created_at,
    }


@router.put("/{alert_id}")
async def update_keyword_alert(
    alert_id: UUID,
    request: KeywordAlertUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Update a keyword alert."""
    result = await db.execute(
        select(KeywordAlert).where(
            KeywordAlert.id == alert_id,
            KeywordAlert.user_id == current_user.id,
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Keyword alert not found")

    # Validate regex if updating
    if request.keyword and request.is_regex:
        try:
            re.compile(request.keyword)
        except re.error as e:
            raise HTTPException(status_code=400, detail=f"Invalid regex: {e}")

    # Update fields
    if request.keyword is not None:
        alert.keyword = request.keyword
    if request.is_regex is not None:
        alert.is_regex = request.is_regex
    if request.is_case_sensitive is not None:
        alert.is_case_sensitive = request.is_case_sensitive
    if request.is_active is not None:
        alert.is_active = request.is_active
    if request.notify_webhook is not None:
        alert.notify_webhook = request.notify_webhook

    alert.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(alert)

    return {
        "id": alert.id,
        "keyword": alert.keyword,
        "channel_id": alert.channel_id,
        "is_regex": alert.is_regex,
        "is_case_sensitive": alert.is_case_sensitive,
        "is_active": alert.is_active,
        "notify_webhook": alert.notify_webhook,
        "match_count": alert.match_count,
        "updated_at": alert.updated_at,
    }


@router.delete("/{alert_id}", status_code=204)
async def delete_keyword_alert(
    alert_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Delete a keyword alert."""
    result = await db.execute(
        select(KeywordAlert).where(
            KeywordAlert.id == alert_id,
            KeywordAlert.user_id == current_user.id,
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Keyword alert not found")

    await db.delete(alert)
    await db.commit()


@router.get("/{alert_id}/matches")
async def get_keyword_matches(
    alert_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
) -> dict:
    """Get matches for a keyword alert."""
    # Verify ownership
    result = await db.execute(
        select(KeywordAlert).where(
            KeywordAlert.id == alert_id,
            KeywordAlert.user_id == current_user.id,
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Keyword alert not found")

    # Build query
    query = select(KeywordMatch).where(KeywordMatch.keyword_alert_id == alert_id)
    count_query = select(func.count(KeywordMatch.id)).where(
        KeywordMatch.keyword_alert_id == alert_id
    )

    if unread_only:
        query = query.where(KeywordMatch.is_read == False)
        count_query = count_query.where(KeywordMatch.is_read == False)

    # Get total
    result = await db.execute(count_query)
    total = result.scalar() or 0

    # Get matches with message info
    offset = (page - 1) * limit
    result = await db.execute(
        query.order_by(KeywordMatch.created_at.desc()).limit(limit).offset(offset)
    )
    matches = result.scalars().all()

    # Get channel titles and message dates
    match_data = []
    for match in matches:
        channel_title = None
        message_date = None

        result = await db.execute(
            select(Channel.title).where(Channel.id == match.channel_id)
        )
        channel_title = result.scalar()

        result = await db.execute(
            select(Message.date).where(Message.id == match.message_id)
        )
        message_date = result.scalar()

        match_data.append({
            "id": match.id,
            "keyword_alert_id": match.keyword_alert_id,
            "keyword": alert.keyword,
            "message_id": match.message_id,
            "channel_id": match.channel_id,
            "channel_title": channel_title,
            "matched_text": match.matched_text,
            "message_date": message_date,
            "is_read": match.is_read,
            "created_at": match.created_at,
        })

    return {
        "matches": match_data,
        "total": total,
        "page": page,
        "limit": limit,
        "unread_count": total if unread_only else None,
    }


@router.post("/{alert_id}/matches/mark-read")
async def mark_matches_read(
    alert_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    match_ids: Optional[list[UUID]] = None,
) -> dict:
    """Mark keyword matches as read."""
    # Verify ownership
    result = await db.execute(
        select(KeywordAlert).where(
            KeywordAlert.id == alert_id,
            KeywordAlert.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Keyword alert not found")

    # Mark as read
    if match_ids:
        await db.execute(
            update(KeywordMatch)
            .where(
                KeywordMatch.keyword_alert_id == alert_id,
                KeywordMatch.id.in_(match_ids),
            )
            .values(is_read=True)
        )
    else:
        # Mark all as read
        await db.execute(
            update(KeywordMatch)
            .where(KeywordMatch.keyword_alert_id == alert_id)
            .values(is_read=True)
        )

    await db.commit()
    return {"status": "success"}


@router.get("/matches/unread-count")
async def get_unread_count(
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Get total unread matches count for current user."""
    result = await db.execute(
        select(func.count(KeywordMatch.id))
        .join(KeywordAlert)
        .where(
            KeywordAlert.user_id == current_user.id,
            KeywordMatch.is_read == False,
        )
    )
    unread_count = result.scalar() or 0

    return {"unread_count": unread_count}
