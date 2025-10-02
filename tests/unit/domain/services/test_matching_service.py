"""Unit tests for item matching service."""

from datetime import UTC, datetime

from src.domain.entities.stolen_item import StolenItem
from src.domain.services.matching_service import ItemMatchingService
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber


class TestItemMatchingService:
    """Test suite for ItemMatchingService."""

    def test_identical_items_have_perfect_match(self) -> None:
        """Should return 1.0 similarity for identical items."""
        # Arrange
        phone = PhoneNumber("+447911123456")
        location = Location(latitude=51.5074, longitude=-0.1278)
        stolen_date = datetime.now(UTC)

        item1 = StolenItem.create(
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Red Trek Marlin 7 mountain bike",
            stolen_date=stolen_date,
            location=location,
            brand="Trek",
            model="Marlin 7",
            serial_number="ABC123",
            color="Red",
        )

        item2 = StolenItem.create(
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Red Trek Marlin 7 mountain bike",
            stolen_date=stolen_date,
            location=location,
            brand="Trek",
            model="Marlin 7",
            serial_number="ABC123",
            color="Red",
        )

        service = ItemMatchingService()

        # Act
        similarity = service.calculate_similarity(item1, item2)

        # Assert
        assert similarity == 1.0

    def test_same_serial_number_gives_high_similarity(self) -> None:
        """Should give high similarity when serial numbers match."""
        # Arrange
        phone = PhoneNumber("+447911123456")
        location = Location(latitude=51.5074, longitude=-0.1278)
        stolen_date = datetime.now(UTC)

        item1 = StolenItem.create(
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=stolen_date,
            location=location,
            serial_number="ABC123",
        )

        item2 = StolenItem.create(
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Blue road bike",
            stolen_date=stolen_date,
            location=location,
            serial_number="ABC123",
        )

        service = ItemMatchingService()

        # Act
        similarity = service.calculate_similarity(item1, item2)

        # Assert
        assert similarity > 0.7  # Serial number heavily weighted

    def test_different_serial_numbers_low_similarity(self) -> None:
        """Should give low similarity when serial numbers differ."""
        # Arrange
        phone = PhoneNumber("+447911123456")
        location = Location(latitude=51.5074, longitude=-0.1278)
        stolen_date = datetime.now(UTC)

        item1 = StolenItem.create(
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=stolen_date,
            location=location,
            serial_number="ABC123",
        )

        item2 = StolenItem.create(
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=stolen_date,
            location=location,
            serial_number="XYZ789",
        )

        service = ItemMatchingService()

        # Act
        similarity = service.calculate_similarity(item1, item2)

        # Assert
        assert similarity <= 0.5  # Different serials reduce similarity

    def test_similar_descriptions_contribute_to_match(self) -> None:
        """Should consider description similarity."""
        # Arrange
        phone = PhoneNumber("+447911123456")
        location = Location(latitude=51.5074, longitude=-0.1278)
        stolen_date = datetime.now(UTC)

        item1 = StolenItem.create(
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Red Trek mountain bike with 21 gears",
            stolen_date=stolen_date,
            location=location,
            brand="Trek",
        )

        item2 = StolenItem.create(
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Red Trek mountain bike 21 speed",
            stolen_date=stolen_date,
            location=location,
            brand="Trek",
        )

        service = ItemMatchingService()

        # Act
        similarity = service.calculate_similarity(item1, item2)

        # Assert
        assert similarity > 0.4  # Similar brand and description

    def test_items_match_above_threshold(self) -> None:
        """Should return True when similarity exceeds threshold."""
        # Arrange
        phone = PhoneNumber("+447911123456")
        location = Location(latitude=51.5074, longitude=-0.1278)
        stolen_date = datetime.now(UTC)

        item1 = StolenItem.create(
            reporter_phone=phone,
            item_type=ItemCategory.PHONE,
            description="iPhone 15 Pro Black",
            stolen_date=stolen_date,
            location=location,
            brand="Apple",
            model="iPhone 15 Pro",
        )

        item2 = StolenItem.create(
            reporter_phone=phone,
            item_type=ItemCategory.PHONE,
            description="iPhone 15 Pro Black",
            stolen_date=stolen_date,
            location=location,
            brand="Apple",
            model="iPhone 15 Pro",
        )

        service = ItemMatchingService(threshold=0.7)

        # Act
        is_match = service.is_match(item1, item2)

        # Assert
        assert is_match is True

    def test_items_do_not_match_below_threshold(self) -> None:
        """Should return False when similarity is below threshold."""
        # Arrange
        phone = PhoneNumber("+447911123456")
        location = Location(latitude=51.5074, longitude=-0.1278)
        stolen_date = datetime.now(UTC)

        item1 = StolenItem.create(
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=stolen_date,
            location=location,
        )

        item2 = StolenItem.create(
            reporter_phone=phone,
            item_type=ItemCategory.PHONE,
            description="iPhone 15 Pro Black",
            stolen_date=stolen_date,
            location=location,
        )

        service = ItemMatchingService(threshold=0.7)

        # Act
        is_match = service.is_match(item1, item2)

        # Assert
        assert is_match is False

    def test_custom_threshold_affects_matching(self) -> None:
        """Should use custom threshold for matching."""
        # Arrange
        phone = PhoneNumber("+447911123456")
        location = Location(latitude=51.5074, longitude=-0.1278)
        stolen_date = datetime.now(UTC)

        item1 = StolenItem.create(
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Red Trek bike with 21 gears",
            stolen_date=stolen_date,
            location=location,
            brand="Trek",
        )

        item2 = StolenItem.create(
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Blue Giant bike 18 speed",
            stolen_date=stolen_date,
            location=location,
            brand="Giant",
        )

        strict_service = ItemMatchingService(threshold=0.5)
        lenient_service = ItemMatchingService(threshold=0.03)

        # Act
        strict_match = strict_service.is_match(item1, item2)
        lenient_match = lenient_service.is_match(item1, item2)
        similarity = lenient_service.calculate_similarity(item1, item2)

        # Assert
        assert strict_match is False
        assert (
            lenient_match is True
        ), f"Expected match with threshold 0.03, got similarity {similarity}"

    def test_completely_different_items_near_zero_similarity(self) -> None:
        """Should return very low similarity for completely different items."""
        # Arrange
        phone = PhoneNumber("+447911123456")
        location = Location(latitude=51.5074, longitude=-0.1278)
        stolen_date = datetime.now(UTC)

        item1 = StolenItem.create(
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Red Trek mountain bike",
            stolen_date=stolen_date,
            location=location,
            brand="Trek",
            model="Marlin 7",
        )

        item2 = StolenItem.create(
            reporter_phone=phone,
            item_type=ItemCategory.LAPTOP,
            description="MacBook Pro 16 inch",
            stolen_date=stolen_date,
            location=location,
            brand="Apple",
            model="MacBook Pro",
        )

        service = ItemMatchingService()

        # Act
        similarity = service.calculate_similarity(item1, item2)

        # Assert
        assert similarity < 0.2

    def test_handles_items_with_no_serial_number(self) -> None:
        """Should handle comparison when neither item has serial number."""
        # Arrange
        phone = PhoneNumber("+447911123456")
        location = Location(latitude=51.5074, longitude=-0.1278)
        stolen_date = datetime.now(UTC)

        item1 = StolenItem.create(
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=stolen_date,
            location=location,
        )

        item2 = StolenItem.create(
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=stolen_date,
            location=location,
        )

        service = ItemMatchingService()

        # Act
        similarity = service.calculate_similarity(item1, item2)

        # Assert
        assert similarity > 0.8  # Should match on description

    def test_one_item_has_serial_other_does_not(self) -> None:
        """Should handle when only one item has serial number."""
        # Arrange
        phone = PhoneNumber("+447911123456")
        location = Location(latitude=51.5074, longitude=-0.1278)
        stolen_date = datetime.now(UTC)

        item1 = StolenItem.create(
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=stolen_date,
            location=location,
            serial_number="ABC123",
        )

        item2 = StolenItem.create(
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=stolen_date,
            location=location,
        )

        service = ItemMatchingService()

        # Act
        similarity = service.calculate_similarity(item1, item2)

        # Assert
        assert 0 < similarity < 1  # Partial match due to missing serial


class TestJaccardSimilarity:
    """Test suite for Jaccard similarity algorithm."""

    def test_identical_strings_return_one(self) -> None:
        """Should return 1.0 for identical strings."""
        # Arrange & Act
        similarity = ItemMatchingService._jaccard_similarity(
            "hello world", "hello world"
        )

        # Assert
        assert similarity == 1.0

    def test_completely_different_strings_return_zero(self) -> None:
        """Should return 0.0 for completely different strings."""
        # Arrange & Act
        similarity = ItemMatchingService._jaccard_similarity("hello", "goodbye")

        # Assert
        assert similarity == 0.0

    def test_both_empty_strings_return_one(self) -> None:
        """Should return 1.0 when both strings are empty."""
        # Arrange & Act
        similarity = ItemMatchingService._jaccard_similarity("", "")

        # Assert
        assert similarity == 1.0

    def test_one_empty_string_returns_zero(self) -> None:
        """Should return 0.0 when one string is empty."""
        # Arrange & Act
        similarity1 = ItemMatchingService._jaccard_similarity("hello", "")
        similarity2 = ItemMatchingService._jaccard_similarity("", "hello")

        # Assert
        assert similarity1 == 0.0
        assert similarity2 == 0.0

    def test_whitespace_only_strings_return_one(self) -> None:
        """Should return 1.0 when both strings are whitespace only."""
        # Arrange & Act
        similarity = ItemMatchingService._jaccard_similarity("   ", "  ")

        # Assert
        assert similarity == 1.0

    def test_one_whitespace_only_returns_zero(self) -> None:
        """Should return 0.0 when one string is whitespace only."""
        # Arrange & Act
        similarity1 = ItemMatchingService._jaccard_similarity("hello", "   ")
        similarity2 = ItemMatchingService._jaccard_similarity("  ", "hello")

        # Assert
        assert similarity1 == 0.0
        assert similarity2 == 0.0

    def test_partial_overlap_returns_correct_score(self) -> None:
        """Should calculate correct Jaccard coefficient for partial overlap."""
        # Arrange & Act
        # "red bike" vs "blue bike" = intersection: {bike}, union: {red, bike, blue}
        # Jaccard = 1/3 = 0.333...
        similarity = ItemMatchingService._jaccard_similarity("red bike", "blue bike")

        # Assert
        assert 0.3 < similarity < 0.4
