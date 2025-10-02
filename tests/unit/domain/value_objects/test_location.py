"""Tests for Location value object."""
import pytest

from src.domain.value_objects.location import Location

MIN_LATITUDE = -90.0
MAX_LATITUDE = 90.0
MIN_LONGITUDE = -180.0
MAX_LONGITUDE = 180.0


@pytest.mark.unit
def test_creates_valid_location_with_coordinates() -> None:
    """Test that Location can be created with valid coordinates.

    Given: Valid latitude and longitude coordinates
    When: Location is instantiated
    Then: Location object is created with correct coordinates
    """
    # Arrange & Act
    location = Location(latitude=51.5074, longitude=-0.1278)

    # Assert
    assert location.latitude == 51.5074
    assert location.longitude == -0.1278
    assert location.address is None


@pytest.mark.unit
def test_creates_location_with_optional_address() -> None:
    """Test that Location can be created with optional address.

    Given: Valid coordinates and an address string
    When: Location is instantiated with address
    Then: Location object includes the address
    """
    # Arrange & Act
    location = Location(latitude=51.5074, longitude=-0.1278, address="London, UK")

    # Assert
    assert location.latitude == 51.5074
    assert location.longitude == -0.1278
    assert location.address == "London, UK"


@pytest.mark.unit
def test_location_is_immutable() -> None:
    """Test that Location is immutable (frozen dataclass).

    Given: A Location instance
    When: Attempting to modify a field
    Then: Raises FrozenInstanceError
    """
    # Arrange
    location = Location(latitude=51.5074, longitude=-0.1278)

    # Act & Assert
    with pytest.raises(AttributeError):
        location.latitude = 52.0  # type: ignore[misc]


@pytest.mark.unit
def test_rejects_latitude_below_minimum() -> None:
    """Test that Location rejects latitude below -90.

    Given: Latitude below minimum valid value
    When: Location is instantiated
    Then: Raises ValueError
    """
    # Act & Assert
    with pytest.raises(ValueError, match="Invalid latitude"):
        Location(latitude=-91.0, longitude=0.0)


@pytest.mark.unit
def test_rejects_latitude_above_maximum() -> None:
    """Test that Location rejects latitude above 90.

    Given: Latitude above maximum valid value
    When: Location is instantiated
    Then: Raises ValueError
    """
    # Act & Assert
    with pytest.raises(ValueError, match="Invalid latitude"):
        Location(latitude=91.0, longitude=0.0)


@pytest.mark.unit
def test_rejects_longitude_below_minimum() -> None:
    """Test that Location rejects longitude below -180.

    Given: Longitude below minimum valid value
    When: Location is instantiated
    Then: Raises ValueError
    """
    # Act & Assert
    with pytest.raises(ValueError, match="Invalid longitude"):
        Location(latitude=0.0, longitude=-181.0)


@pytest.mark.unit
def test_rejects_longitude_above_maximum() -> None:
    """Test that Location rejects longitude above 180.

    Given: Longitude above maximum valid value
    When: Location is instantiated
    Then: Raises ValueError
    """
    # Act & Assert
    with pytest.raises(ValueError, match="Invalid longitude"):
        Location(latitude=0.0, longitude=181.0)


@pytest.mark.unit
def test_accepts_boundary_latitude_values() -> None:
    """Test that Location accepts boundary latitude values.

    Given: Latitude at exact min/max boundaries
    When: Location is instantiated
    Then: Location is created successfully
    """
    # Act
    min_location = Location(latitude=MIN_LATITUDE, longitude=0.0)
    max_location = Location(latitude=MAX_LATITUDE, longitude=0.0)

    # Assert
    assert min_location.latitude == MIN_LATITUDE
    assert max_location.latitude == MAX_LATITUDE


@pytest.mark.unit
def test_accepts_boundary_longitude_values() -> None:
    """Test that Location accepts boundary longitude values.

    Given: Longitude at exact min/max boundaries
    When: Location is instantiated
    Then: Location is created successfully
    """
    # Act
    min_location = Location(latitude=0.0, longitude=MIN_LONGITUDE)
    max_location = Location(latitude=0.0, longitude=MAX_LONGITUDE)

    # Assert
    assert min_location.longitude == MIN_LONGITUDE
    assert max_location.longitude == MAX_LONGITUDE


@pytest.mark.unit
def test_location_equality() -> None:
    """Test that Locations with same coordinates are equal.

    Given: Two Location instances with identical coordinates
    When: Compared for equality
    Then: They are equal
    """
    # Arrange
    location1 = Location(latitude=51.5074, longitude=-0.1278, address="London")
    location2 = Location(latitude=51.5074, longitude=-0.1278, address="London")

    # Act & Assert
    assert location1 == location2


@pytest.mark.unit
def test_location_repr() -> None:
    """Test that Location has a readable string representation.

    Given: A Location instance
    When: Converted to string representation
    Then: Returns readable format with coordinates
    """
    # Arrange
    location = Location(latitude=51.5074, longitude=-0.1278)

    # Act
    repr_str = repr(location)

    # Assert
    assert "51.5074" in repr_str
    assert "-0.1278" in repr_str
    assert "Location" in repr_str
