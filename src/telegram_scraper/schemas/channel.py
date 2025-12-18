"""Channel schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChannelCreate(BaseModel):
    """Schema for adding a channel to track."""

    telegram_id: int
    scrape_media: bool = True


class ChannelResponse(BaseModel):
    """Schema for channel response."""

    id: UUID
    telegram_id: int
    username: str | None
    title: str | None
    channel_type: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserChannelResponse(BaseModel):
    """Schema for user's tracked channel."""

    id: UUID
    channel: ChannelResponse
    last_scraped_message_id: int
    scrape_media: bool
    is_active: bool
    added_at: datetime
    message_count: int = 0
    media_count: int = 0

    model_config = {"from_attributes": True}


class AvailableChannel(BaseModel):
    """Schema for available channel from Telegram."""

    telegram_id: int
    username: str | None
    title: str
    channel_type: str
    is_tracked: bool = False


class ChannelStats(BaseModel):
    """Schema for channel statistics."""

    total_messages: int
    total_media: int
    media_downloaded: int
    media_pending: int
    media_failed: int
    first_message_date: datetime | None
    last_message_date: datetime | None
    last_scraped_at: datetime | None


class ChannelUpdateRequest(BaseModel):
    """Schema for updating channel settings."""

    scrape_media: bool | None = None
    is_active: bool | None = None
