"""PhoneNumber value object for international phone numbers."""

from dataclasses import dataclass

import phonenumbers
from phonenumbers import NumberParseException


@dataclass(frozen=True)
class PhoneNumber:
    """Immutable value object for international phone numbers in E.164 format.

    E.164 is the international telephone numbering plan that ensures
    each phone number is globally unique. Format: +[country code][number]
    Example: +447700900123 (UK), +12025551234 (US), +27821234567 (ZA)
    """

    value: str

    def __post_init__(self) -> None:
        """Validate and normalize phone number on creation.

        Raises:
            ValueError: If phone number is not valid E.164 format
        """
        try:
            parsed = phonenumbers.parse(self.value, None)

            if not phonenumbers.is_valid_number(parsed):
                raise ValueError(f"Invalid phone number: {self.value}")

            normalized = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )

            object.__setattr__(self, "value", normalized)

        except NumberParseException as error:
            raise ValueError(f"Invalid phone number: {self.value}") from error

    @property
    def country_code(self) -> int:
        """Extract country code from phone number.

        Returns:
            Country code as integer (e.g., 44 for UK, 1 for US, 27 for ZA)

        Raises:
            ValueError: If country code is missing (should not happen for valid numbers)
        """
        parsed = phonenumbers.parse(self.value, None)
        code = parsed.country_code
        if code is None:
            raise ValueError("Valid phone number must have country code")
        return code

    @property
    def formatted(self) -> str:
        """Get internationally formatted display version.

        Returns:
            Phone number formatted with spaces for readability
            Example: "+44 7700 900123"
        """
        parsed = phonenumbers.parse(self.value, None)
        return phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )
