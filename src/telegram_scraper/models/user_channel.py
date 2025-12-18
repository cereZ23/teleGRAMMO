"""UserChannel model for many-to-many relationship between users and channels."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from telegram_scraper.models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from telegram_scraper.models.channel import Channel
    from telegram_scraper.models.user import User


class UserChannel(Base, UUIDMixin):
    """Association between users and channels they track."""

    __tablename__ = "user_channels"
    __table_args__ = (
        UniqueConstraint("user_id", "channel_id", name="uq_user_channel"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    last_scraped_message_id: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    scrape_media: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Scheduling fields
    schedule_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    schedule_interval_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # e.g., 1, 6, 12, 24
    last_scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_channels")
    channel: Mapped["Channel"] = relationship("Channel", back_populates="user_channels")

    def __repr__(self) -> str:
        return f"<UserChannel(user_id={self.user_id}, channel_id={self.channel_id})>"
