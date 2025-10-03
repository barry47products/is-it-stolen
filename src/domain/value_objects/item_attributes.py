"""Flexible item attributes that vary by category."""

from dataclasses import dataclass
from datetime import UTC, datetime

MIN_YEAR = 1900
VIN_LENGTH = 17
IMEI_LENGTH = 15


@dataclass(frozen=True)
class BicycleAttributes:
    """Attributes specific to bicycles."""

    frame_number: str | None = None
    wheel_size: str | None = None
    gears: int | None = None

    def __post_init__(self) -> None:
        """Validate bicycle attributes."""
        if self.gears is not None and self.gears <= 0:
            raise ValueError("Gears must be positive")

        if self.frame_number is not None:
            object.__setattr__(self, "frame_number", self.frame_number.upper())


@dataclass(frozen=True)
class PhoneAttributes:
    """Attributes specific to phones."""

    imei: str | None = None
    storage_capacity: str | None = None
    carrier: str | None = None

    def __post_init__(self) -> None:
        """Validate phone attributes."""
        if self.imei is not None:
            if len(self.imei) != IMEI_LENGTH:
                raise ValueError(f"IMEI must be exactly {IMEI_LENGTH} digits")
            if not self.imei.isdigit():
                raise ValueError("IMEI must contain only digits")


@dataclass(frozen=True)
class LaptopAttributes:
    """Attributes specific to laptops."""

    ram: str | None = None
    storage: str | None = None
    processor: str | None = None


@dataclass(frozen=True)
class VehicleAttributes:
    """Attributes specific to vehicles."""

    vin: str | None = None
    license_plate: str | None = None
    year: int | None = None

    def __post_init__(self) -> None:
        """Validate vehicle attributes."""
        if self.vin is not None:
            if len(self.vin) != VIN_LENGTH:
                raise ValueError(f"VIN must be exactly {VIN_LENGTH} characters")
            object.__setattr__(self, "vin", self.vin.upper())

        if self.license_plate is not None:
            object.__setattr__(self, "license_plate", self.license_plate.upper())

        if self.year is not None:
            current_year = datetime.now(UTC).year
            max_year = current_year + 1
            if not (MIN_YEAR <= self.year <= max_year):
                raise ValueError(f"Year must be between {MIN_YEAR} and {max_year}")
