"""Database connection and session management."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from src.infrastructure.config.settings import get_settings

if TYPE_CHECKING:
    from collections.abc import Generator

# Base class for all SQLAlchemy models
Base = declarative_base()

# Get database URL from settings
settings = get_settings()
DATABASE_URL = str(settings.database_url)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,  # Number of connections to maintain
    max_overflow=10,  # Max connections beyond pool_size
    echo=False,  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_engine():  # type: ignore[no-untyped-def]
    """Get database engine.

    Returns:
        SQLAlchemy engine instance
    """
    return engine


def get_db_session() -> Generator[Session]:
    """Get database session with automatic cleanup.

    Yields:
        Database session

    Usage:
        for session in get_db_session():
            # Use session here
            pass
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def get_db() -> Generator[Session]:
    """Context manager for database sessions.

    Yields:
        Database session

    Usage:
        with get_db() as db:
            # Use db here
            pass
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Initialize database tables.

    This creates all tables defined by SQLAlchemy models.
    In production, use Alembic migrations instead.
    """
    Base.metadata.create_all(bind=engine)
