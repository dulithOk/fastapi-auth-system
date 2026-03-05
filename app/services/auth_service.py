"""
Authentication service: login, token refresh, and logout logic.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.repositories.user_repository import UserRepository
from app.schemas.user import LoginRequest, TokenResponse


class AuthService:
    """Handles login, token issuance, and refresh flows."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = UserRepository(db)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        """
        Authenticate a user with email + password.

        Returns:
            TokenResponse with access and refresh tokens.

        Raises:
            UnauthorizedException: If credentials are invalid.
            BadRequestException: If the account is inactive.
        """
        user = await self.repo.get_by_email(payload.email)

        if not user or not verify_password(payload.password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password.")

        if not user.is_active:
            raise BadRequestException("Account is disabled. Contact support.")

        # Stamp last login (best-effort, no await to keep latency low)
        await self.repo.update_last_login(user.id)

        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"role": user.role.value, "email": user.email},
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        Issue a new access token from a valid refresh token.

        Raises:
            UnauthorizedException: If the refresh token is invalid or expired.
            BadRequestException: If the token type is wrong.
        """
        payload = decode_token(refresh_token)
        if payload is None:
            raise UnauthorizedException("Refresh token is invalid or expired.")

        if payload.get("type") != "refresh":
            raise BadRequestException("Provided token is not a refresh token.")

        import uuid
        user_id = uuid.UUID(payload["sub"])
        user = await self.repo.get_by_id(user_id)

        if not user or not user.is_active:
            raise UnauthorizedException("User not found or account disabled.")

        new_access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"role": user.role.value, "email": user.email},
        )
        new_refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )
