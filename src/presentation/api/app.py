"""FastAPI application entry point with dependency injection and lifecycle management."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from fastapi import FastAPI

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from src.domain.value_objects.item_category import ItemCategory
from src.infrastructure.config import load_category_keywords
from src.infrastructure.config.settings import get_settings
from src.infrastructure.logging import configure_logging, get_logger
from src.infrastructure.monitoring.sentry import init_sentry
from src.infrastructure.persistence.database import init_db
from src.infrastructure.tracing import instrument_all, setup_tracing, shutdown_tracing
from src.presentation.api.middleware import LoggingMiddleware, RequestIDMiddleware
from src.presentation.api.prometheus import router as prometheus_router
from src.presentation.api.v1 import api_router as v1_router

# Get settings and configure logging early
settings = get_settings()
configure_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    redact_sensitive=settings.log_redact_sensitive,
)
logger = get_logger(__name__)

# Load category keywords at module level (before app creation)
ItemCategory.set_keywords(load_category_keywords())


@asynccontextmanager
async def lifespan(  # type: ignore[no-any-unimported]
    _app: FastAPI,
) -> AsyncGenerator[None]:
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
    logger.info("Starting Is It Stolen API", version="0.1.0")
    startup_settings = get_settings()
    logger.info(
        "Configuration loaded",
        environment=startup_settings.environment,
        log_level=startup_settings.log_level,
        log_format=startup_settings.log_format,
        debug=startup_settings.debug,
    )

    # Initialize OpenTelemetry tracing
    setup_tracing()
    if startup_settings.otel_enabled:
        logger.info(
            "OpenTelemetry tracing initialized",
            service_name=startup_settings.otel_service_name,
            sample_rate=startup_settings.otel_traces_sample_rate,
        )
        # Instrument libraries after tracing is configured
        instrument_all()
        logger.info("Auto-instrumentation enabled for database, HTTP, and Redis")

    # Initialize Sentry error tracking
    init_sentry(startup_settings)
    if startup_settings.sentry_dsn:
        logger.info(
            "Sentry initialized",
            sentry_environment=startup_settings.sentry_environment,
        )

    # Initialize database
    init_db()
    logger.info("Database initialized")

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Is It Stolen API")

    # Shutdown tracing and flush pending spans
    shutdown_tracing()
    logger.info("OpenTelemetry tracing shutdown complete")

    logger.info("Application shutdown complete")


def create_app() -> FastAPI:  # type: ignore[no-any-unimported]
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    settings = get_settings()

    app = FastAPI(
        title="Is It Stolen API",
        description="""
WhatsApp bot for checking and reporting stolen items.

## Features

* **Check stolen items** - Verify if items are reported as stolen
* **Report stolen items** - Submit theft reports with location data
* **Location-based search** - Find nearby reported thefts
* **Police verification** - Link reports with official police references
* **Real-time notifications** - Receive updates via WhatsApp

## Authentication

Webhook endpoints require HMAC-SHA256 signature validation using the `X-Hub-Signature-256` header.

## Architecture

Built with Domain-Driven Design principles:
- **Domain Layer** - Core business logic with no external dependencies
- **Application Layer** - Use cases and orchestration
- **Infrastructure Layer** - Database, WhatsApp API, Redis, messaging
- **Presentation Layer** - FastAPI endpoints and WhatsApp bot conversation flow

## Technology Stack

- **Framework**: FastAPI with async/await
- **Database**: PostgreSQL with PostGIS (geospatial)
- **Cache**: Redis
- **Observability**: OpenTelemetry, Prometheus, Sentry
- **Testing**: pytest with 80%+ coverage
        """,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        contact={
            "name": "Is It Stolen Team",
            "url": "https://github.com/barry47products/is-it-stolen",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        openapi_tags=[
            {
                "name": "webhook",
                "description": "WhatsApp webhook endpoints for receiving messages and verification",
            },
            {
                "name": "health",
                "description": "Service health monitoring endpoints (liveness, readiness)",
            },
            {
                "name": "metrics",
                "description": "Prometheus metrics endpoint for observability",
            },
        ],
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

    # Instrument FastAPI with OpenTelemetry
    FastAPIInstrumentor.instrument_app(app)

    return app


# Create application instance
app = create_app()
