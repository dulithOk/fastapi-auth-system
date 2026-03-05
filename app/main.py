"""
FastAPI application entry point.
Configures middleware, mounts routers, and handles startup/shutdown events.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.controllers import auth_router, user_router
from app.core.config import settings
from app.core.exceptions import AppException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """Application factory: builds and configures the FastAPI app."""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Production-ready authentication and user management API built with "
            "FastAPI, SQLAlchemy 2.0, PostgreSQL, and JWT-based RBAC."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ── CORS ──────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Global exception handler ──────────────────────────
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected internal error occurred."},
        )

    # ── Routers ───────────────────────────────────────────
    API_PREFIX = "/api/v1"
    app.include_router(auth_router, prefix=API_PREFIX)
    app.include_router(user_router, prefix=API_PREFIX)

    # ── Health check ──────────────────────────────────────
    @app.get("/health", tags=["Health"], summary="Health check")
    async def health_check() -> dict:
        return {"status": "ok", "version": settings.APP_VERSION}

    # ── Startup event ─────────────────────────────────────
    @app.on_event("startup")
    async def on_startup() -> None:
        """Seed the first admin user if none exists."""
        logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
        await _seed_admin()

    return app


async def _seed_admin() -> None:
    """
    Create the initial admin account on first startup.
    Reads credentials from environment variables.
    """
    from app.core.database import AsyncSessionLocal
    from app.core.security import hash_password
    from app.models.user import User, UserRole
    from app.repositories.user_repository import UserRepository

    async with AsyncSessionLocal() as db:
        try:
            repo = UserRepository(db)
            existing = await repo.get_by_email(settings.FIRST_ADMIN_EMAIL)
            if not existing:
                admin = User(
                    username=settings.FIRST_ADMIN_USERNAME,
                    email=settings.FIRST_ADMIN_EMAIL.lower(),
                    hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
                    role=UserRole.ADMIN,
                    is_active=True,
                    is_verified=True,
                )
                await repo.create(admin)
                await db.commit()
                logger.info("Admin user seeded: %s", settings.FIRST_ADMIN_EMAIL)
            else:
                logger.info("Admin user already exists — skipping seed.")
        except Exception as exc:
            logger.warning("Could not seed admin user: %s", exc)


app = create_application()
