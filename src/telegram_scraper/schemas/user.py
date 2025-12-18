"""User schemas for API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=100)
    is_active: bool | None = None


class UserResponse(BaseModel):
    """Schema for user response."""

    id: UUID
    email: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
