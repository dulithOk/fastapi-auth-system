"""
Pydantic schemas for request validation and response serialization.
Separates API contracts from ORM models.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole


# ─────────────────────────── Auth Schemas ────────────────────────────


class LoginRequest(BaseModel):
    """Credentials submitted on login."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """JWT tokens returned after successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Refresh token submitted to obtain a new access token."""

    refresh_token: str


# ─────────────────────────── User Schemas ────────────────────────────


class UserBase(BaseModel):
    """Fields shared across create/update/read schemas."""

    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr


class UserCreate(UserBase):
    """Payload for registering a new user."""

    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Enforce basic password complexity."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


class UserUpdate(BaseModel):
    """Payload for updating an existing user (all fields optional)."""

    username: Optional[str] = Field(None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class AdminUserUpdate(UserUpdate):
    """Extended update schema available only to admins (includes role change)."""

    role: Optional[UserRole] = None


class UserResponse(UserBase):
    """Safe user representation returned from API endpoints."""

    id: uuid.UUID
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Paginated list of users."""

    users: list[UserResponse]
    total: int
    page: int
    page_size: int
