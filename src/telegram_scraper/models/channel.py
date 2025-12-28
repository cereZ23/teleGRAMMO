"""Channel model for Telegram channels/groups."""

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from telegram_scraper.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from telegram_scraper.models.keyword_alert import KeywordAlert
    from telegram_scraper.models.media import Media
    from telegram_scraper.models.message import Message
    from telegram_scraper.models.scraping_job import ScrapingJob
    from telegram_scraper.models.user_channel import UserChannel


class Channel(Base, UUIDMixin, TimestampMixin):
    """Telegram channel or group."""

    __tablename__ = "channels"

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    channel_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # channel, group, supergroup

    # Relationships
    user_channels: Mapped[list["UserChannel"]] = relationship(
        "UserChannel",
        back_populates="channel",
        cascade="all, delete-orphan",
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="channel",
        cascade="all, delete-orphan",
    )
    media: Mapped[list["Media"]] = relationship(
        "Media",
        back_populates="channel",
        cascade="all, delete-orphan",
    )
    scraping_jobs: Mapped[list["ScrapingJob"]] = relationship(
        "ScrapingJob",
        back_populates="channel",
        cascade="all, delete-orphan",
    )
    keyword_alerts: Mapped[list["KeywordAlert"]] = relationship(
        "KeywordAlert",
        back_populates="channel",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Channel(id={self.id}, telegram_id={self.telegram_id}, title={self.title})>"
