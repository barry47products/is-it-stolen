"""Unit tests for StartUserSessionCommand."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.application.commands.start_user_session import (
    StartUserSessionCommand,
    StartUserSessionHandler,
)
from src.domain.entities.user_session import UserSession
from src.domain.repositories.analytics_repository import ISessionRepository
from src.domain.value_objects.session_id import SessionId
from src.domain.value_objects.user_segment import UserSegment


class TestStartUserSessionCommand:
    """Test suite for StartUserSessionCommand."""

    def test_creates_command_with_required_fields(self) -> None:
        """Test creating command with required fields."""
        # Arrange
        phone_number = "+447700900000"

        # Act
        command = StartUserSessionCommand(phone_number=phone_number)

        # Assert
        assert command.phone_number == phone_number


@pytest.mark.asyncio
class TestStartUserSessionHandler:
    """Test suite for StartUserSessionHandler."""

    async def test_starts_new_session_for_first_time_user(self) -> None:
        """Test starting session for first-time user."""
        # Arrange
        mock_repo = AsyncMock(spec=ISessionRepository)
        mock_repo.count_user_sessions.return_value = 0
        handler = StartUserSessionHandler(repository=mock_repo)
        command = StartUserSessionCommand(phone_number="+447700900000")

        # Act
        session_id = await handler.handle(command)

        # Assert
        assert isinstance(session_id, SessionId)
        mock_repo.save_session.assert_called_once()
        saved_session = mock_repo.save_session.call_args[0][0]
        assert isinstance(saved_session, UserSession)
        assert saved_session.segment == UserSegment.FIRST_TIME

    async def test_starts_new_session_for_returning_user(self) -> None:
        """Test starting session for returning user."""
        # Arrange
        mock_repo = AsyncMock(spec=ISessionRepository)
        mock_repo.count_user_sessions.return_value = 3
        handler = StartUserSessionHandler(repository=mock_repo)
        command = StartUserSessionCommand(phone_number="+447700900000")

        # Act
        session_id = await handler.handle(command)

        # Assert
        assert isinstance(session_id, SessionId)
        saved_session = mock_repo.save_session.call_args[0][0]
        assert saved_session.segment == UserSegment.RETURNING

    async def test_starts_new_session_for_power_user(self) -> None:
        """Test starting session for power user (10+ sessions)."""
        # Arrange
        mock_repo = AsyncMock(spec=ISessionRepository)
        mock_repo.count_user_sessions.return_value = 15
        handler = StartUserSessionHandler(repository=mock_repo)
        command = StartUserSessionCommand(phone_number="+447700900000")

        # Act
        await handler.handle(command)

        # Assert
        saved_session = mock_repo.save_session.call_args[0][0]
        assert saved_session.segment == UserSegment.POWER_USER

    async def test_hashes_phone_number_for_privacy(self) -> None:
        """Test phone number is hashed before storage."""
        # Arrange
        mock_repo = AsyncMock(spec=ISessionRepository)
        mock_repo.count_user_sessions.return_value = 0
        handler = StartUserSessionHandler(repository=mock_repo)
        phone_number = "+447700900000"
        command = StartUserSessionCommand(phone_number=phone_number)

        # Act
        await handler.handle(command)

        # Assert
        saved_session = mock_repo.save_session.call_args[0][0]
        assert saved_session.user_hash != phone_number
        assert len(saved_session.user_hash) == 64  # SHA-256 hash

    async def test_session_starts_with_current_timestamp(self) -> None:
        """Test session started_at is set to current time."""
        # Arrange
        mock_repo = AsyncMock(spec=ISessionRepository)
        mock_repo.count_user_sessions.return_value = 0
        handler = StartUserSessionHandler(repository=mock_repo)
        command = StartUserSessionCommand(phone_number="+447700900000")
        before = datetime.now(UTC)

        # Act
        await handler.handle(command)

        # Assert
        after = datetime.now(UTC)
        saved_session = mock_repo.save_session.call_args[0][0]
        assert before <= saved_session.started_at <= after

    async def test_returns_session_id(self) -> None:
        """Test handler returns new session ID."""
        # Arrange
        mock_repo = AsyncMock(spec=ISessionRepository)
        mock_repo.count_user_sessions.return_value = 0
        handler = StartUserSessionHandler(repository=mock_repo)
        command = StartUserSessionCommand(phone_number="+447700900000")

        # Act
        session_id = await handler.handle(command)

        # Assert
        assert isinstance(session_id, SessionId)
        saved_session = mock_repo.save_session.call_args[0][0]
        assert saved_session.session_id == session_id
