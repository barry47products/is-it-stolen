"""FastAPI application entry point with dependency injection and lifecycle management."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from fastapi import FastAPI

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.domain.value_objects.item_category import ItemCategory
from src.infrastructure.config import load_category_keywords
from src.infrastructure.config.settings import get_settings
from src.infrastructure.monitoring.sentry import init_sentry
from src.infrastructure.persistence.database import init_db
from src.presentation.api.middleware import LoggingMiddleware, RequestIDMiddleware
from src.presentation.api.prometheus import router as prometheus_router
from src.presentation.api.v1 import api_router as v1_router

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load category keywords at module level (before app creation)
ItemCategory.set_keywords(load_category_keywords())


@asynccontextmanager
async def lifespan(  # type: ignore[no-any-unimported]
    _app: FastAPI,
) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown events.

    Handles:
    - Loading category keywords
    - Database initialization
    - Graceful shutdown

    Args:
        app: FastAPI application instance

    Yields:
        None during application runtime
    """
    # Startup
    logger.info("Starting Is It Stolen API...")
    settings = get_settings()
    logger.info(f"Environment: {settings.environment}")

    # Initialize Sentry error tracking
    init_sentry(settings)

    # Initialize database
    init_db()
    logger.info("Database initialized")

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Is It Stolen API...")
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:  # type: ignore[no-any-unimported]
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    settings = get_settings()

    app = FastAPI(
        title="Is It Stolen API",
        description="WhatsApp bot for checking and reporting stolen items",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure based on environment
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add custom middleware
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(LoggingMiddleware)

    # Include Prometheus metrics endpoint (at root level as per Prometheus convention)
    app.include_router(prometheus_router)

    # Include versioned API routes
    app.include_router(v1_router, prefix="/v1")

    # Root health check (not versioned)
    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint.

        Returns:
            Status message indicating service is healthy
        """
        return {"status": "healthy", "version": "0.1.0"}

    return app


# Create application instance
app = create_app()
