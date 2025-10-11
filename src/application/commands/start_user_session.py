"""Start User Session command and handler."""

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime

from src.domain.entities.user_session import UserSession
from src.domain.repositories.analytics_repository import ISessionRepository
from src.domain.value_objects.session_id import SessionId
from src.domain.value_objects.user_segment import UserSegment

POWER_USER_THRESHOLD = 10
FIRST_TIME_USER_COUNT = 0


@dataclass
class StartUserSessionCommand:
    """Command to start a new user session.

    Carries phone number which will be hashed for privacy.
    """

    phone_number: str


class StartUserSessionHandler:
    """Handler for starting user sessions.

    Creates new sessions, determines user segment, and hashes
    phone numbers for privacy-compliant storage.
    """

    def __init__(self, repository: ISessionRepository) -> None:
        """Initialize handler with session repository.

        Args:
            repository: Repository for session persistence
        """
        self._repository = repository

    async def handle(self, command: StartUserSessionCommand) -> SessionId:
        """Handle the start session command.

        Args:
            command: Command with phone number

        Returns:
            Session ID of new session
        """
        user_hash = self._hash_phone_number(command.phone_number)
        segment = await self._determine_segment(user_hash)
        session = self._create_session(user_hash, segment)
        await self._repository.save_session(session)
        return session.session_id

    async def _determine_segment(self, user_hash: str) -> UserSegment:
        """Determine user segment based on session history.

        Args:
            user_hash: Hashed phone number

        Returns:
            User segment classification
        """
        count = await self._repository.count_user_sessions(user_hash)
        if count == FIRST_TIME_USER_COUNT:
            return UserSegment.FIRST_TIME
        if count >= POWER_USER_THRESHOLD:
            return UserSegment.POWER_USER
        return UserSegment.RETURNING

    @staticmethod
    def _create_session(user_hash: str, segment: UserSegment) -> UserSession:
        """Create new user session.

        Args:
            user_hash: Hashed user identifier
            segment: User segment

        Returns:
            New UserSession entity
        """
        return UserSession(
            session_id=SessionId.generate(),
            user_hash=user_hash,
            started_at=datetime.now(UTC),
            segment=segment,
        )

    @staticmethod
    def _hash_phone_number(phone_number: str) -> str:
        """Hash phone number for privacy.

        Args:
            phone_number: Raw phone number

        Returns:
            SHA-256 hash of phone number
        """
        return hashlib.sha256(phone_number.encode()).hexdigest()
