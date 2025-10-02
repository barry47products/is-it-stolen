"""Tests for ItemCategory enum."""

import pytest

from src.domain.value_objects.item_category import ItemCategory

pytestmark = pytest.mark.unit


class TestItemCategory:
    """Test suite for ItemCategory enum."""

    @pytest.fixture(autouse=True)
    def setup_keywords(self) -> None:
        """Set up test keyword mappings before each test."""
        test_keywords = {
            "BICYCLE": ["bicycle", "bike", "cycle", "mountain bike"],
            "PHONE": ["phone", "mobile", "cellphone", "smartphone", "iphone"],
            "LAPTOP": ["laptop", "computer", "notebook", "macbook"],
            "VEHICLE": ["vehicle", "car", "motorcycle", "motorbike", "scooter"],
        }
        ItemCategory.set_keywords(test_keywords)

    def test_creates_category_from_enum_value(self) -> None:
        """Should create category from valid enum value."""
        category = ItemCategory.BICYCLE
        assert category == ItemCategory.BICYCLE

    def test_has_all_required_categories(self) -> None:
        """Should have all required category types."""
        assert ItemCategory.BICYCLE
        assert ItemCategory.PHONE
        assert ItemCategory.LAPTOP
        assert ItemCategory.VEHICLE

    def test_parses_exact_category_name(self) -> None:
        """Should parse exact category name."""
        category = ItemCategory.from_user_input("bicycle")
        assert category == ItemCategory.BICYCLE

    def test_parses_category_name_case_insensitive(self) -> None:
        """Should parse category name case-insensitively."""
        assert ItemCategory.from_user_input("BICYCLE") == ItemCategory.BICYCLE
        assert ItemCategory.from_user_input("BiCyCLe") == ItemCategory.BICYCLE

    def test_parses_bicycle_keywords(self) -> None:
        """Should parse bicycle keywords."""
        assert ItemCategory.from_user_input("bike") == ItemCategory.BICYCLE
        assert ItemCategory.from_user_input("cycle") == ItemCategory.BICYCLE
        assert ItemCategory.from_user_input("mountain bike") == ItemCategory.BICYCLE

    def test_parses_phone_keywords(self) -> None:
        """Should parse phone keywords."""
        assert ItemCategory.from_user_input("mobile") == ItemCategory.PHONE
        assert ItemCategory.from_user_input("cellphone") == ItemCategory.PHONE
        assert ItemCategory.from_user_input("smartphone") == ItemCategory.PHONE
        assert ItemCategory.from_user_input("iphone") == ItemCategory.PHONE

    def test_parses_laptop_keywords(self) -> None:
        """Should parse laptop keywords."""
        assert ItemCategory.from_user_input("computer") == ItemCategory.LAPTOP
        assert ItemCategory.from_user_input("notebook") == ItemCategory.LAPTOP
        assert ItemCategory.from_user_input("macbook") == ItemCategory.LAPTOP

    def test_parses_vehicle_keywords(self) -> None:
        """Should parse vehicle keywords."""
        assert ItemCategory.from_user_input("car") == ItemCategory.VEHICLE
        assert ItemCategory.from_user_input("motorcycle") == ItemCategory.VEHICLE
        assert ItemCategory.from_user_input("motorbike") == ItemCategory.VEHICLE
        assert ItemCategory.from_user_input("scooter") == ItemCategory.VEHICLE

    def test_raises_error_for_invalid_category(self) -> None:
        """Should raise ValueError for invalid category."""
        with pytest.raises(ValueError, match="Unknown item category"):
            ItemCategory.from_user_input("invalid")

    def test_raises_error_for_empty_string(self) -> None:
        """Should raise ValueError for empty string."""
        with pytest.raises(ValueError, match="Unknown item category"):
            ItemCategory.from_user_input("")

    def test_keyword_matching_with_whitespace(self) -> None:
        """Should handle whitespace in keywords."""
        assert ItemCategory.from_user_input("  bike  ") == ItemCategory.BICYCLE
        assert ItemCategory.from_user_input("\tmobile\n") == ItemCategory.PHONE

    def test_set_keywords_validates_category_name(self) -> None:
        """Should raise ValueError for invalid category name."""
        with pytest.raises(ValueError, match="Invalid category name"):
            ItemCategory.set_keywords({"INVALID": ["keyword"]})

    def test_set_keywords_validates_empty_keywords(self) -> None:
        """Should raise ValueError for empty keyword list."""
        with pytest.raises(ValueError, match="cannot be empty"):
            ItemCategory.set_keywords({"BICYCLE": []})
