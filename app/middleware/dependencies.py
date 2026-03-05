"""
FastAPI dependencies for authentication and role-based access control.
Injected into route handlers via Depends().
"""

import uuid
from typing import Optional

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

# Tells FastAPI where to find the token (used in OpenAPI docs too)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login/form")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Decode the JWT and return the corresponding User.

    Raises:
        UnauthorizedException: If the token is missing, invalid, or the user is gone.
    """
    payload = decode_token(token)
    if payload is None:
        raise UnauthorizedException("Token is invalid or has expired.")

    if payload.get("type") != "access":
        raise UnauthorizedException("Invalid token type.")

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise UnauthorizedException("Malformed token payload.")

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)

    if not user:
        raise UnauthorizedException("User belonging to this token no longer exists.")

    if not user.is_active:
        raise UnauthorizedException("Account is disabled.")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the current user is active (convenience alias)."""
    return current_user


def require_roles(*roles: UserRole):
    """
    Dependency factory that enforces one of the specified roles.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_roles(UserRole.ADMIN))])
    """

    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in roles:
            raise ForbiddenException(
                f"Required role(s): {[r.value for r in roles]}. "
                f"Your role: {current_user.role.value}."
            )
        return current_user

    return role_checker


# Pre-built role guards for convenience
require_admin = require_roles(UserRole.ADMIN)
require_moderator_or_admin = require_roles(UserRole.ADMIN, UserRole.MODERATOR)
