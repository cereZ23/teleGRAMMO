"""Authentication schemas."""

from uuid import UUID

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Schema for login request."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT tokens response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""

    sub: UUID
    type: str
    exp: int
