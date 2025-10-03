"""Tests for flexible item attributes by category."""

import pytest

from src.domain.value_objects.item_attributes import (
    BicycleAttributes,
    LaptopAttributes,
    PhoneAttributes,
    VehicleAttributes,
)


class TestBicycleAttributes:
    """Test bicycle-specific attributes."""

    def test_creates_bicycle_attributes_with_all_fields(self) -> None:
        """Should create bicycle attributes with all fields."""
        # Arrange & Act
        attrs = BicycleAttributes(
            frame_number="FN123456", wheel_size="26 inch", gears=21
        )

        # Assert
        assert attrs.frame_number == "FN123456"
        assert attrs.wheel_size == "26 inch"
        assert attrs.gears == 21

    def test_creates_bicycle_attributes_with_optional_fields(self) -> None:
        """Should create bicycle with minimal required fields."""
        # Arrange & Act
        attrs = BicycleAttributes()

        # Assert
        assert attrs.frame_number is None
        assert attrs.wheel_size is None
        assert attrs.gears is None

    def test_validates_gears_is_positive(self) -> None:
        """Should reject negative gear count."""
        # Act & Assert
        with pytest.raises(ValueError, match="Gears must be positive"):
            BicycleAttributes(gears=-1)

    def test_normalizes_frame_number_to_uppercase(self) -> None:
        """Should normalize frame number to uppercase."""
        # Arrange & Act
        attrs = BicycleAttributes(frame_number="fn123abc")

        # Assert
        assert attrs.frame_number == "FN123ABC"


class TestPhoneAttributes:
    """Test phone-specific attributes."""

    def test_creates_phone_attributes_with_all_fields(self) -> None:
        """Should create phone attributes with all fields."""
        # Arrange & Act
        attrs = PhoneAttributes(
            imei="123456789012345", storage_capacity="128GB", carrier="Vodafone"
        )

        # Assert
        assert attrs.imei == "123456789012345"
        assert attrs.storage_capacity == "128GB"
        assert attrs.carrier == "Vodafone"

    def test_validates_imei_is_15_digits(self) -> None:
        """Should validate IMEI is exactly 15 digits."""
        # Act & Assert
        with pytest.raises(ValueError, match="IMEI must be exactly 15 digits"):
            PhoneAttributes(imei="12345")

    def test_validates_imei_contains_only_digits(self) -> None:
        """Should reject IMEI with non-digit characters."""
        # Act & Assert
        with pytest.raises(ValueError, match="IMEI must contain only digits"):
            PhoneAttributes(imei="12345678901234A")

    def test_creates_phone_without_imei(self) -> None:
        """Should allow phone without IMEI."""
        # Arrange & Act
        attrs = PhoneAttributes(storage_capacity="64GB")

        # Assert
        assert attrs.imei is None
        assert attrs.storage_capacity == "64GB"


class TestLaptopAttributes:
    """Test laptop-specific attributes."""

    def test_creates_laptop_attributes_with_all_fields(self) -> None:
        """Should create laptop attributes with all fields."""
        # Arrange & Act
        attrs = LaptopAttributes(ram="16GB", storage="512GB SSD", processor="Intel i7")

        # Assert
        assert attrs.ram == "16GB"
        assert attrs.storage == "512GB SSD"
        assert attrs.processor == "Intel i7"

    def test_creates_laptop_with_minimal_fields(self) -> None:
        """Should create laptop with no required fields."""
        # Arrange & Act
        attrs = LaptopAttributes()

        # Assert
        assert attrs.ram is None
        assert attrs.storage is None
        assert attrs.processor is None


class TestVehicleAttributes:
    """Test vehicle-specific attributes."""

    def test_creates_vehicle_attributes_with_all_fields(self) -> None:
        """Should create vehicle attributes with all fields."""
        # Arrange & Act
        attrs = VehicleAttributes(
            vin="1HGCM82633A123456", license_plate="ABC123", year=2020
        )

        # Assert
        assert attrs.vin == "1HGCM82633A123456"
        assert attrs.license_plate == "ABC123"
        assert attrs.year == 2020

    def test_validates_vin_length(self) -> None:
        """Should validate VIN is 17 characters."""
        # Act & Assert
        with pytest.raises(ValueError, match="VIN must be exactly 17 characters"):
            VehicleAttributes(vin="SHORT")

    def test_normalizes_vin_to_uppercase(self) -> None:
        """Should normalize VIN to uppercase."""
        # Arrange & Act
        attrs = VehicleAttributes(vin="1hgcm82633a123456")

        # Assert
        assert attrs.vin == "1HGCM82633A123456"

    def test_normalizes_license_plate_to_uppercase(self) -> None:
        """Should normalize license plate to uppercase."""
        # Arrange & Act
        attrs = VehicleAttributes(license_plate="abc123")

        # Assert
        assert attrs.license_plate == "ABC123"

    def test_validates_year_is_reasonable(self) -> None:
        """Should reject year before 1900 or in far future."""
        # Act & Assert
        with pytest.raises(ValueError, match="Year must be between"):
            VehicleAttributes(year=1800)

        with pytest.raises(ValueError, match="Year must be between"):
            VehicleAttributes(year=2100)

    def test_creates_vehicle_with_no_fields(self) -> None:
        """Should allow vehicle with all optional fields."""
        # Arrange & Act
        attrs = VehicleAttributes()

        # Assert
        assert attrs.vin is None
        assert attrs.license_plate is None
        assert attrs.year is None
