"""Auto-instrumentation for common libraries."""

from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

from src.infrastructure.persistence.database import get_engine


def instrument_database() -> None:
    """Instrument SQLAlchemy database operations."""
    engine = get_engine()
    SQLAlchemyInstrumentor().instrument(engine=engine)


def instrument_http_client() -> None:
    """Instrument httpx HTTP client operations."""
    HTTPXClientInstrumentor().instrument()


def instrument_redis() -> None:
    """Instrument Redis operations."""
    RedisInstrumentor().instrument()


def instrument_all() -> None:
    """Instrument all supported libraries for tracing."""
    instrument_database()
    instrument_http_client()
    instrument_redis()
