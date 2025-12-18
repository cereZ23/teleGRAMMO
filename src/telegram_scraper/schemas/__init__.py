"""Pydantic schemas for API request/response validation."""

from telegram_scraper.schemas.auth import Token, TokenPayload
from telegram_scraper.schemas.channel import (
    AvailableChannel,
    ChannelCreate,
    ChannelResponse,
    ChannelStats,
    UserChannelResponse,
)
from telegram_scraper.schemas.job import JobCreate, JobResponse, JobStatus
from telegram_scraper.schemas.message import MessageResponse, MessageSearchParams
from telegram_scraper.schemas.telegram_session import (
    TelegramSessionCreate,
    TelegramSessionResponse,
    VerifyCodeRequest,
)
from telegram_scraper.schemas.user import UserCreate, UserResponse, UserUpdate

__all__ = [
    "Token",
    "TokenPayload",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "TelegramSessionCreate",
    "TelegramSessionResponse",
    "VerifyCodeRequest",
    "ChannelCreate",
    "ChannelResponse",
    "UserChannelResponse",
    "AvailableChannel",
    "ChannelStats",
    "MessageResponse",
    "MessageSearchParams",
    "JobCreate",
    "JobResponse",
    "JobStatus",
]
