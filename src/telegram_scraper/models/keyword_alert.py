"""Keyword Alert model for tracking keyword mentions."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from telegram_scraper.models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from telegram_scraper.models.user import User
    from telegram_scraper.models.channel import Channel


class KeywordAlert(Base, UUIDMixin):
    """Keyword to monitor in channel messages."""

    __tablename__ = "keyword_alerts"
    __table_args__ = (
        Index("idx_keyword_user", "user_id"),
        Index("idx_keyword_active", "is_active"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=True,  # NULL = all channels
    )
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    is_regex: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_case_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Notification settings
    notify_email: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notify_webhook: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Stats
    match_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_match_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="keyword_alerts")
    channel: Mapped[Optional["Channel"]] = relationship("Channel", back_populates="keyword_alerts")
    matches: Mapped[list["KeywordMatch"]] = relationship(
        "KeywordMatch", back_populates="keyword_alert", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<KeywordAlert(id={self.id}, keyword='{self.keyword}', active={self.is_active})>"


class KeywordMatch(Base, UUIDMixin):
    """Record of a keyword match in a message."""

    __tablename__ = "keyword_matches"
    __table_args__ = (
        Index("idx_match_alert", "keyword_alert_id"),
        Index("idx_match_message", "message_id"),
        Index("idx_match_created", "created_at"),
    )

    keyword_alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("keyword_alerts.id", ondelete="CASCADE"),
        nullable=False,
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Snippet of matched text for quick preview
    matched_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Whether user has seen this match
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
    )

    # Relationships
    keyword_alert: Mapped["KeywordAlert"] = relationship("KeywordAlert", back_populates="matches")
    message: Mapped["Message"] = relationship("Message")
    channel: Mapped["Channel"] = relationship("Channel")

    def __repr__(self) -> str:
        return f"<KeywordMatch(id={self.id}, alert_id={self.keyword_alert_id})>"
