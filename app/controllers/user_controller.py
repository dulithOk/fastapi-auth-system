"""
User management controller: CRUD endpoints with role-based access control.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.dependencies import (
    get_current_active_user,
    require_admin,
    require_moderator_or_admin,
)
from app.models.user import User, UserRole
from app.schemas.user import (
    AdminUserUpdate,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


# ──────────────────────── Public ──────────────────────────


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Public endpoint to create a new **user** account.
    Role is always set to `user`; admins must be created by other admins.
    """
    service = UserService(db)
    user = await service.create_user(payload, role=UserRole.USER)
    return UserResponse.model_validate(user)


# ──────────────────────── Me ──────────────────────────────


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Return the authenticated user's own profile."""
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
)
async def update_me(
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Update the authenticated user's own profile (username, email, password)."""
    service = UserService(db)
    updated = await service.update_user(current_user.id, payload, current_user)
    return UserResponse.model_validate(updated)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete own account",
)
async def delete_me(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Permanently delete the authenticated user's own account."""
    service = UserService(db)
    await service.delete_user(current_user.id, current_user)


# ──────────────────────── Admin: List / Create ────────────


@router.get(
    "/",
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,
    summary="[Admin/Moderator] List all users",
    dependencies=[Depends(require_moderator_or_admin)],
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
) -> UserListResponse:
    """
    Paginated list of all users.

    - **Moderators** and **admins** can access this endpoint.
    - Supports filtering by `role` and `is_active`.
    """
    service = UserService(db)
    return await service.get_all_users(
        page=page, page_size=page_size, role=role, is_active=is_active
    )


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Create a user with a specific role",
    dependencies=[Depends(require_admin)],
)
async def admin_create_user(
    payload: UserCreate,
    role: UserRole = Query(UserRole.USER, description="Role to assign"),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Admin-only endpoint to create a user with an arbitrary role."""
    service = UserService(db)
    user = await service.create_user(payload, role=role)
    return UserResponse.model_validate(user)


# ──────────────────────── Admin: Single User ──────────────


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="[Admin/Moderator] Get user by ID",
    dependencies=[Depends(require_moderator_or_admin)],
)
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Fetch a single user by their UUID."""
    service = UserService(db)
    user = await service.get_user_by_id(user_id)
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="[Admin] Update any user",
    dependencies=[Depends(require_admin)],
)
async def admin_update_user(
    user_id: uuid.UUID,
    payload: AdminUserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> UserResponse:
    """Admin can update any user's profile, including their role."""
    service = UserService(db)
    updated = await service.update_user(user_id, payload, current_user)
    return UserResponse.model_validate(updated)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] Delete any user",
)
async def admin_delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """Admin can hard-delete any user account (except their own)."""
    service = UserService(db)
    await service.delete_user(user_id, current_user)
