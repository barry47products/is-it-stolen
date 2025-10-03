"""Integration tests for database connection."""

import pytest
from sqlalchemy import text

from src.infrastructure.persistence.database import (
    Base,
    get_db,
    get_db_session,
    get_engine,
    init_db,
)


class TestDatabaseConnection:
    """Test database connection and session management."""

    def test_database_engine_connects_successfully(self) -> None:
        """Should connect to database successfully."""
        # Arrange
        engine = get_engine()

        # Act & Assert
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_database_session_generator_works(self) -> None:
        """Should provide working database session via generator."""
        # Arrange & Act
        for session in get_db_session():
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_database_context_manager_works(self) -> None:
        """Should provide working database session via context manager."""
        # Arrange & Act
        with get_db() as session:
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_postgis_extension_is_enabled(self) -> None:
        """Should have PostGIS extension enabled."""
        # Arrange & Act
        with get_db() as session:
            result = session.execute(text("SELECT PostGIS_Version()"))
            version = result.scalar()

            # Assert
            assert version is not None
            assert "3.6" in version

    def test_postgis_topology_extension_is_enabled(self) -> None:
        """Should have PostGIS topology extension enabled."""
        # Arrange & Act
        with get_db() as session:
            result = session.execute(
                text(
                    "SELECT COUNT(*) FROM pg_extension WHERE extname = 'postgis_topology'"
                )
            )
            count = result.scalar()

            # Assert
            assert count == 1

    def test_session_commits_on_success(self) -> None:
        """Should commit transaction on successful completion."""
        # Arrange & Act
        with get_db() as session:
            # Create a temporary table
            session.execute(text("CREATE TEMPORARY TABLE test_commit (id INTEGER)"))
            session.execute(text("INSERT INTO test_commit (id) VALUES (1)"))

        # Verify in new session
        with get_db() as session:
            result = session.execute(text("SELECT COUNT(*) FROM test_commit"))
            count = result.scalar()
            assert count == 1

    def test_session_rollback_on_exception(self) -> None:
        """Should rollback transaction on exception."""
        # Arrange & Act
        with (
            pytest.raises(Exception, match="Test rollback"),
            get_db() as session,
        ):
            session.execute(text("CREATE TEMPORARY TABLE test_rollback (id INTEGER)"))
            session.execute(text("INSERT INTO test_rollback (id) VALUES (1)"))
            raise Exception("Test rollback")

        # Verify rollback - table should not exist in new session
        with get_db() as session:
            result = session.execute(
                text("SELECT COUNT(*) FROM pg_tables WHERE tablename = 'test_rollback'")
            )
            count = result.scalar()
            assert count == 0

    def test_session_generator_rollback_on_exception(self) -> None:
        """Should rollback transaction on exception using generator."""
        # Arrange
        gen = get_db_session()
        session = next(gen)

        # Act & Assert
        try:
            session.execute(
                text("CREATE TEMPORARY TABLE test_gen_rollback (id INTEGER)")
            )
            session.execute(text("INSERT INTO test_gen_rollback (id) VALUES (1)"))
            raise Exception("Test generator rollback")
        except Exception as e:
            # Let generator handle the exception
            with pytest.raises(Exception, match="Test generator rollback"):
                gen.throw(e)

        # Verify rollback - table should not exist in new session
        with get_db() as session:
            result = session.execute(
                text(
                    "SELECT COUNT(*) FROM pg_tables WHERE tablename = 'test_gen_rollback'"
                )
            )
            count = result.scalar()
            assert count == 0

    def test_init_db_creates_tables(self) -> None:
        """Should create all tables defined in Base metadata."""
        # Arrange & Act
        init_db()

        # Assert - verify Base metadata exists and can create tables
        assert Base.metadata is not None
        # Test that init_db successfully runs without error
        # Since no models are defined yet, no tables will be created
        # but the function should execute successfully
