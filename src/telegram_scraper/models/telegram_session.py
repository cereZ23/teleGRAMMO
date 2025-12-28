"""Telegram session model for storing user's Telegram credentials."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from telegram_scraper.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from telegram_scraper.models.user import User


class TelegramSession(Base, UUIDMixin, TimestampMixin):
    """Telegram API session for a user."""

    __tablename__ = "telegram_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    api_id: Mapped[int] = mapped_column(Integer, nullable=False)
    api_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    session_string: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_authenticated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    session_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="telegram_sessions")

    def __repr__(self) -> str:
        return f"<TelegramSession(id={self.id}, api_id={self.api_id}, authenticated={self.is_authenticated})>"
