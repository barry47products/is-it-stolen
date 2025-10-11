"""SessionId value object for tracking user sessions."""

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class SessionId:
    """Immutable value object representing a unique session identifier.

    Sessions track user interactions with the bot over time. Each session
    has a unique identifier used for analytics and journey tracking.
    """

    value: UUID

    @classmethod
    def from_string(cls, uuid_string: str) -> "SessionId":
        """Create SessionId from UUID string.

        Args:
            uuid_string: String representation of UUID

        Returns:
            SessionId instance

        Raises:
            ValueError: If string is not a valid UUID format
        """
        try:
            uuid_value = UUID(uuid_string)
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid UUID format: {uuid_string}") from e
        return cls(value=uuid_value)

    def to_string(self) -> str:
        """Convert SessionId to string representation.

        Returns:
            String representation of the UUID
        """
        return str(self.value)

    @classmethod
    def generate(cls) -> "SessionId":
        """Generate new random SessionId.

        Returns:
            New SessionId with random UUID
        """
        return cls(value=uuid4())
