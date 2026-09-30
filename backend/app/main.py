"""ArthSaathi FastAPI application entry point."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import ArthSaathiError
from app.core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

settings = get_settings()


def create_app() -> FastAPI:
    """Factory function that creates and configures the FastAPI application."""
    application = FastAPI(
        title="ArthSaathi API",
        version="0.1.0",
        description="Multi-agent financial-literacy platform for gig and agricultural workers.",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ─── CORS ─────────────────────────────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─── Exception handlers ───────────────────────────────────────────────────
    @application.exception_handler(ArthSaathiError)
    async def arthsaathi_error_handler(request: Request, exc: ArthSaathiError) -> JSONResponse:
        logger.warning("Domain error: %s — %s", exc.__class__.__name__, exc.message)
        return JSONResponse(
            status_code=exc.http_status,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    # ─── Routers ──────────────────────────────────────────────────────────────
    # Phase 2: Authentication
    from app.api import auth

    application.include_router(auth.router, prefix="/api")

    # Future phases — registered here as each phase completes:
    from app.api import onboarding, profile, scam_scanner, schemes, transactions
    application.include_router(scam_scanner.router, prefix="/api")
    application.include_router(onboarding.router, prefix="/api")
    application.include_router(profile.router, prefix="/api")
    application.include_router(schemes.router, prefix="/api")
    # Phase 3: Transactions & Insights
    from app.api import guardian, transactions, katha, supervisor
    application.include_router(transactions.router, prefix="/api")
    application.include_router(guardian.router, prefix="/api")
    application.include_router(katha.router, prefix="/api")
    application.include_router(supervisor.router, prefix="/api")
    # Future phases — registered here as each phase completes:
    # from app.api import documents, nudges, ngo, notifications
    # application.include_router(documents.router, prefix="/api")
    # application.include_router(nudges.router, prefix="/api")
    # application.include_router(ngo.router, prefix="/api")
    # application.include_router(notifications.router, prefix="/api")

    # ─── Health check ─────────────────────────────────────────────────────────
    @application.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
