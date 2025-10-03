"""Location value object for geographic coordinates."""

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt

MIN_LATITUDE = -90.0
MAX_LATITUDE = 90.0
MIN_LONGITUDE = -180.0
MAX_LONGITUDE = 180.0
EARTH_RADIUS_KM = 6371.0


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

    def distance_to(self, other: "Location") -> float:
        """Calculate distance to another location using Haversine formula.

        Args:
            other: Another Location to calculate distance to

        Returns:
            Distance in kilometres (accurate to ~1km)
        """
        lat1_rad = radians(self.latitude)
        lat2_rad = radians(other.latitude)
        delta_lat = radians(other.latitude - self.latitude)
        delta_lon = radians(other.longitude - self.longitude)

        haversine_lat = sin(delta_lat / 2) ** 2
        haversine_lon = sin(delta_lon / 2) ** 2
        haversine_formula = (
            haversine_lat + cos(lat1_rad) * cos(lat2_rad) * haversine_lon
        )
        angular_distance = 2 * asin(sqrt(haversine_formula))

        return EARTH_RADIUS_KM * angular_distance
