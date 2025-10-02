"""ItemCategory enum for categorizing stolen items."""

from enum import Enum

# Module-level keyword mappings (configured at startup)
_keyword_mappings: dict[str, "ItemCategory"] = {}


class ItemCategory(str, Enum):
    """Categories for stolen items with keyword matching."""

    BICYCLE = "bicycle"
    PHONE = "phone"
    LAPTOP = "laptop"
    VEHICLE = "vehicle"

    @classmethod
    def set_keywords(cls, category_keywords: dict[str, list[str]]) -> None:
        """Configure keyword mappings for category parsing.

        This method should be called at application startup to configure
        keyword mappings from the configuration file.

        Args:
            category_keywords: Dictionary mapping category names to keyword lists
                Example: {"BICYCLE": ["bike", "cycle"], "PHONE": ["mobile"]}

        Raises:
            ValueError: If category name is invalid or keywords are empty
        """
        global _keyword_mappings
        _keyword_mappings = {}

        for category_name, keywords in category_keywords.items():
            try:
                category = cls[category_name.upper()]
            except KeyError as error:
                raise ValueError(f"Invalid category name: {category_name}") from error

            if not keywords:
                raise ValueError(f"Keywords for {category_name} cannot be empty")

            for keyword in keywords:
                normalized_keyword = keyword.strip().lower()
                _keyword_mappings[normalized_keyword] = category

    @classmethod
    def from_user_input(cls, user_input: str) -> "ItemCategory":
        """Parse category from user input with keyword matching.

        Args:
            user_input: User-provided category name or keyword

        Returns:
            Matching ItemCategory enum value

        Raises:
            ValueError: If no matching category found
        """
        normalized = user_input.strip().lower()

        if not normalized:
            raise ValueError("Unknown item category: empty string")

        if normalized in _keyword_mappings:
            return _keyword_mappings[normalized]

        raise ValueError(f"Unknown item category: {user_input}")
