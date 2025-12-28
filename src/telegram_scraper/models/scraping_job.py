"""ScrapingJob model for tracking scraping tasks."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from telegram_scraper.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from telegram_scraper.models.channel import Channel
    from telegram_scraper.models.user import User


class ScrapingJob(Base, UUIDMixin, TimestampMixin):
    """Background scraping job."""

    __tablename__ = "scraping_jobs"
    __table_args__ = (
        Index("idx_jobs_status", "status"),
        Index("idx_jobs_user", "user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=True,
    )
    job_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # full_scrape, incremental, media_only, continuous
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )  # pending, running, completed, failed, cancelled
    progress_percent: Mapped[float] = mapped_column(
        Numeric(5, 2),
        default=0,
        nullable=False,
    )
    messages_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    media_downloaded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    job_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    arq_job_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="scraping_jobs")
    channel: Mapped[Optional["Channel"]] = relationship("Channel", back_populates="scraping_jobs")

    def __repr__(self) -> str:
        return f"<ScrapingJob(id={self.id}, type={self.job_type}, status={self.status})>"
