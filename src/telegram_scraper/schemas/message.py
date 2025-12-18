"""Message schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """Schema for message response."""

    id: UUID
    telegram_message_id: int
    date: datetime
    sender_id: int | None
    first_name: str | None
    last_name: str | None
    username: str | None
    message_text: str | None
    media_type: str | None
    reply_to_message_id: int | None
    post_author: str | None
    views: int | None
    forwards: int | None
    reactions: dict[str, Any] | None

    model_config = {"from_attributes": True}


class MessageSearchParams(BaseModel):
    """Schema for message search parameters."""

    query: str | None = None
    sender_username: str | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
    has_media: bool | None = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class MessageListResponse(BaseModel):
    """Schema for paginated message list."""

    messages: list[MessageResponse]
    total: int
    limit: int
    offset: int
    has_more: bool
