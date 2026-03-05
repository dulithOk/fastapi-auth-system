"""
User repository: encapsulates all database access for the User model.
All queries go through this layer — services never touch the ORM directly.
"""

import uuid
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


class UserRepository:
    """Data access layer for User records."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ──────────────────────── Read ────────────────────────

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Fetch a single user by primary key."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetch a user by email address (case-insensitive)."""
        result = await self.db.execute(
            select(User).where(func.lower(User.email) == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Fetch a user by username."""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 20,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[User], int]:
        """
        Return a paginated list of users with optional filters.

        Returns:
            Tuple of (user list, total count).
        """
        query = select(User)
        count_query = select(func.count(User.id))

        if role is not None:
            query = query.where(User.role == role)
            count_query = count_query.where(User.role == role)

        if is_active is not None:
            query = query.where(User.is_active == is_active)
            count_query = count_query.where(User.is_active == is_active)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        users = list(result.scalars().all())

        return users, total

    # ──────────────────────── Write ───────────────────────

    async def create(self, user: User) -> User:
        """Persist a new User instance."""
        self.db.add(user)
        await self.db.flush()   # flush to get DB-generated defaults (id, timestamps)
        await self.db.refresh(user)
        return user

    async def update(self, user: User, updates: dict) -> User:
        """Apply a dict of field updates to an existing User."""
        for field, value in updates.items():
            setattr(user, field, value)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """Hard-delete a User record."""
        await self.db.delete(user)
        await self.db.flush()

    async def update_last_login(self, user_id: uuid.UUID) -> None:
        """Stamp the last_login timestamp for the given user."""
        from datetime import datetime, timezone
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login=datetime.now(timezone.utc))
        )
