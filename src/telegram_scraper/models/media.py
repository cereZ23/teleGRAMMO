"""Media model for downloaded media files."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from telegram_scraper.models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from telegram_scraper.models.channel import Channel
    from telegram_scraper.models.message import Message


class Media(Base, UUIDMixin):
    """Media file associated with a message."""

    __tablename__ = "media"
    __table_args__ = (
        Index("idx_media_status", "download_status"),
        Index("idx_media_channel", "channel_id"),
    )

    message_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
    )
    telegram_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    media_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    download_status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )  # pending, downloading, completed, failed
    download_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
    )
    downloaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    message: Mapped[Optional["Message"]] = relationship("Message", back_populates="media_files")
    channel: Mapped["Channel"] = relationship("Channel", back_populates="media")

    def __repr__(self) -> str:
        return f"<Media(id={self.id}, type={self.media_type}, status={self.download_status})>"
