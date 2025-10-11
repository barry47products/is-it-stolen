"""ConversionRate value object for representing conversion metrics."""

from dataclasses import dataclass

MIN_RATE = 0.0
MAX_RATE = 1.0
PERCENTAGE_MULTIPLIER = 100.0


@dataclass(frozen=True)
class ConversionRate:
    """Immutable value object representing a conversion rate.

    Conversion rates are expressed as floats between 0.0 and 1.0,
    where 0.0 is 0% and 1.0 is 100%.
    """

    value: float

    def __post_init__(self) -> None:
        """Validate conversion rate is within valid range."""
        if not MIN_RATE <= self.value <= MAX_RATE:
            raise ValueError(
                f"Conversion rate must be between {MIN_RATE} and {MAX_RATE}, "
                f"got {self.value}"
            )

    def to_percentage_string(self) -> str:
        """Format conversion rate as percentage string.

        Returns:
            Formatted percentage string (e.g., "75.60%")
        """
        percentage = self.value * PERCENTAGE_MULTIPLIER
        return f"{percentage:.2f}%"
