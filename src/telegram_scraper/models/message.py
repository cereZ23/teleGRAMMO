"""Message model for scraped Telegram messages."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from telegram_scraper.models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from telegram_scraper.models.channel import Channel
    from telegram_scraper.models.media import Media


class Message(Base, UUIDMixin):
    """Scraped Telegram message."""

    __tablename__ = "messages"
    __table_args__ = (
        Index("idx_messages_channel_date", "channel_id", "date"),
        Index("idx_messages_telegram_id", "telegram_message_id"),
        Index("idx_messages_sender", "sender_id"),
        {"postgresql_partition_by": None},  # Can be partitioned by date in future
    )

    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    telegram_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sender_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    message_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reply_to_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    post_author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    views: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    forwards: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reactions: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
    )

    # Relationships
    channel: Mapped["Channel"] = relationship("Channel", back_populates="messages")
    media_files: Mapped[List["Media"]] = relationship(
        "Media",
        back_populates="message",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, telegram_id={self.telegram_message_id})>"
