"""Police reference number value object."""

import re
from dataclasses import dataclass

POLICE_REFERENCE_PATTERN = r"^CR/\d{4}/\d{6}$"


@dataclass(frozen=True)
class PoliceReference:
    """Immutable police reference number.

    Format: CR/YYYY/NNNNNN
    Example: CR/2024/123456
    """

    value: str

    def __post_init__(self) -> None:
        """Validate and normalize police reference."""
        if not self.value:
            raise ValueError("Invalid police reference format")

        normalized = self.value.upper()

        if not re.match(POLICE_REFERENCE_PATTERN, normalized):
            raise ValueError("Invalid police reference format")

        object.__setattr__(self, "value", normalized)
