"""Location value object for geographic coordinates."""
from dataclasses import dataclass

MIN_LATITUDE = -90.0
MAX_LATITUDE = 90.0
MIN_LONGITUDE = -180.0
MAX_LONGITUDE = 180.0


@dataclass(frozen=True)
class Location:
    """Immutable value object representing a geographical location.

    Attributes:
        latitude: Latitude coordinate (-90 to 90 degrees)
        longitude: Longitude coordinate (-180 to 180 degrees)
        address: Optional human-readable address string
    """

    latitude: float
    longitude: float
    address: str | None = None

    def __post_init__(self) -> None:
        """Validate coordinates on instantiation.

        Raises:
            ValueError: If latitude or longitude is out of valid range
        """
        if not MIN_LATITUDE <= self.latitude <= MAX_LATITUDE:
            raise ValueError(
                f"Invalid latitude: {self.latitude}. "
                f"Must be between {MIN_LATITUDE} and {MAX_LATITUDE}"
            )
        if not MIN_LONGITUDE <= self.longitude <= MAX_LONGITUDE:
            raise ValueError(
                f"Invalid longitude: {self.longitude}. "
                f"Must be between {MIN_LONGITUDE} and {MAX_LONGITUDE}"
            )
