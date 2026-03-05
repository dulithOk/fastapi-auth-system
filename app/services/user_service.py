"""
User service: business logic for user management.
Sits between controllers and repositories.
"""

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AlreadyExistsException,
    BadRequestException,
    NotFoundException,
)
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user import AdminUserUpdate, UserCreate, UserListResponse, UserUpdate


class UserService:
    """Handles all user-related business operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = UserRepository(db)

    # ──────────────────────── Create ──────────────────────

    async def create_user(
        self, payload: UserCreate, role: UserRole = UserRole.USER
    ) -> User:
        """
        Register a new user.

        Raises:
            AlreadyExistsException: If email or username is taken.
        """
        if await self.repo.get_by_email(payload.email):
            raise AlreadyExistsException("Email")
        if await self.repo.get_by_username(payload.username):
            raise AlreadyExistsException("Username")

        user = User(
            username=payload.username,
            email=payload.email.lower(),
            hashed_password=hash_password(payload.password),
            role=role,
        )
        return await self.repo.create(user)

    # ──────────────────────── Read ────────────────────────

    async def get_user_by_id(self, user_id: uuid.UUID) -> User:
        """
        Fetch a user by ID.

        Raises:
            NotFoundException: If user does not exist.
        """
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User")
        return user

    async def get_all_users(
        self,
        page: int = 1,
        page_size: int = 20,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
    ) -> UserListResponse:
        """Return a paginated, optionally filtered user list."""
        skip = (page - 1) * page_size
        users, total = await self.repo.list_users(
            skip=skip, limit=page_size, role=role, is_active=is_active
        )
        return UserListResponse(
            users=users,  # type: ignore[arg-type]
            total=total,
            page=page,
            page_size=page_size,
        )

    # ──────────────────────── Update ──────────────────────

    async def update_user(
        self,
        user_id: uuid.UUID,
        payload: UserUpdate | AdminUserUpdate,
        requesting_user: User,
    ) -> User:
        """
        Update a user's profile.

        Regular users may only update themselves; admins can update anyone.

        Raises:
            NotFoundException: If user does not exist.
            ForbiddenException: If a non-admin attempts to update another user.
            AlreadyExistsException: If new email/username is taken.
        """
        from app.core.exceptions import ForbiddenException

        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User")

        # Only admins can update other accounts
        if requesting_user.role != UserRole.ADMIN and requesting_user.id != user_id:
            raise ForbiddenException()

        updates: dict = {}
        data = payload.model_dump(exclude_unset=True)

        if "email" in data and data["email"] != user.email:
            if await self.repo.get_by_email(data["email"]):
                raise AlreadyExistsException("Email")
            updates["email"] = data["email"].lower()

        if "username" in data and data["username"] != user.username:
            if await self.repo.get_by_username(data["username"]):
                raise AlreadyExistsException("Username")
            updates["username"] = data["username"]

        if "password" in data:
            updates["hashed_password"] = hash_password(data["password"])

        for field in ("is_active", "is_verified", "role"):
            if field in data:
                updates[field] = data[field]

        if not updates:
            raise BadRequestException("No valid fields provided for update.")

        return await self.repo.update(user, updates)

    # ──────────────────────── Delete ──────────────────────

    async def delete_user(self, user_id: uuid.UUID, requesting_user: User) -> None:
        """
        Delete a user account.

        Admins can delete any user. Users can delete their own account.

        Raises:
            NotFoundException: If user does not exist.
            ForbiddenException: If unauthorized.
            BadRequestException: If admin tries to delete themselves.
        """
        from app.core.exceptions import ForbiddenException

        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User")

        if requesting_user.role != UserRole.ADMIN and requesting_user.id != user_id:
            raise ForbiddenException()

        if requesting_user.role == UserRole.ADMIN and requesting_user.id == user_id:
            raise BadRequestException("Admins cannot delete their own account.")

        await self.repo.delete(user)
