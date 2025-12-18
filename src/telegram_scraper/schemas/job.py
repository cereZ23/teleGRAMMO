"""Scraping job schemas."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class JobType(str, Enum):
    """Types of scraping jobs."""

    FULL_SCRAPE = "full_scrape"
    INCREMENTAL = "incremental"
    MEDIA_ONLY = "media_only"
    CONTINUOUS = "continuous"


class JobStatus(str, Enum):
    """Job status values."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobCreate(BaseModel):
    """Schema for creating a scraping job."""

    channel_id: UUID
    job_type: JobType = JobType.INCREMENTAL
    scrape_media: bool = True


class ContinuousJobCreate(BaseModel):
    """Schema for creating a continuous scraping job."""

    channel_ids: list[UUID] = Field(min_length=1)
    interval_seconds: int = Field(default=60, ge=30, le=3600)


class JobResponse(BaseModel):
    """Schema for job response."""

    id: UUID
    channel_id: UUID | None
    job_type: str
    status: str
    progress_percent: float
    messages_processed: int
    media_downloaded: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    job_metadata: dict[str, Any] | None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    """Schema for paginated job list."""

    jobs: list[JobResponse]
    total: int
    limit: int
    offset: int


class JobProgressUpdate(BaseModel):
    """Schema for job progress update (SSE)."""

    job_id: UUID
    status: str
    progress_percent: float
    messages_processed: int
    media_downloaded: int
    error_message: str | None = None
