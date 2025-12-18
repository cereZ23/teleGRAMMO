"""User model for authentication."""

from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from telegram_scraper.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from telegram_scraper.models.scraping_job import ScrapingJob
    from telegram_scraper.models.telegram_session import TelegramSession
    from telegram_scraper.models.user_channel import UserChannel
    from telegram_scraper.models.keyword_alert import KeywordAlert


class User(Base, UUIDMixin, TimestampMixin):
    """User account for the application."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    telegram_sessions: Mapped[List["TelegramSession"]] = relationship(
        "TelegramSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    user_channels: Mapped[List["UserChannel"]] = relationship(
        "UserChannel",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    scraping_jobs: Mapped[List["ScrapingJob"]] = relationship(
        "ScrapingJob",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    keyword_alerts: Mapped[List["KeywordAlert"]] = relationship(
        "KeywordAlert",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
