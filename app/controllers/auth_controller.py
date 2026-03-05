"""
Authentication controller: login, logout, token refresh endpoints.
"""

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user import LoginRequest, RefreshTokenRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login with email and password",
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate with **email + password** (JSON body).

    Returns an access token (short-lived) and a refresh token (long-lived).
    """
    service = AuthService(db)
    return await service.login(payload)


@router.post(
    "/login/form",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login via OAuth2 form (Swagger UI compatible)",
    include_in_schema=True,
)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    OAuth2-compatible form login endpoint.
    Allows testing directly from the Swagger UI **Authorize** button.
    The `username` field should contain the user's **email**.
    """
    service = AuthService(db)
    return await service.login(
        LoginRequest(email=form_data.username, password=form_data.password)
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Exchange a valid **refresh token** for a new access token + refresh token pair.
    """
    service = AuthService(db)
    return await service.refresh_access_token(payload.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout (client-side token discard)",
)
async def logout() -> dict:
    """
    Logout endpoint.

    Since JWTs are stateless, true server-side invalidation would require a
    token blacklist (Redis). For now, clients should discard their tokens.
    Returns a confirmation message.
    """
    return {"message": "Successfully logged out. Please discard your tokens."}
