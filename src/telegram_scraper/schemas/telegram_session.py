"""Telegram session schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TelegramSessionCreate(BaseModel):
    """Schema for creating a Telegram session."""

    api_id: int = Field(gt=0)
    api_hash: str = Field(min_length=32, max_length=32)
    session_name: str | None = Field(default=None, max_length=255)


class TelegramSessionResponse(BaseModel):
    """Schema for Telegram session response."""

    id: UUID
    api_id: int
    session_name: str | None
    phone_number: str | None
    is_authenticated: bool
    telegram_user_id: int | None
    last_used_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class QRLoginResponse(BaseModel):
    """Schema for QR login response."""

    qr_url: str
    expires_at: datetime


class PhoneLoginRequest(BaseModel):
    """Schema for phone login request."""

    phone_number: str = Field(min_length=5, max_length=50)


class VerifyCodeRequest(BaseModel):
    """Schema for verification code request."""

    code: str = Field(min_length=4, max_length=10)
    phone_hash: str | None = None


class Verify2FARequest(BaseModel):
    """Schema for 2FA password request."""

    password: str


class SessionStatusResponse(BaseModel):
    """Schema for session authentication status."""

    is_authenticated: bool
    needs_code: bool = False
    needs_2fa: bool = False
    phone_hash: str | None = None
