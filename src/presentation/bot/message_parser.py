"""Message parser for extracting structured data from user input."""

from datetime import UTC, datetime

import dateparser

from src.domain.value_objects.item_category import ItemCategory
from src.infrastructure.config.category_keywords import load_category_keywords


class MessageParser:
    """Parser for extracting structured data from user messages."""

    def __init__(self) -> None:
        """Initialize message parser with category keywords."""
        self.category_keywords = load_category_keywords()

    def parse_category(self, text: str) -> ItemCategory | None:
        """Parse item category from text using keyword matching.

        Args:
            text: User input text

        Returns:
            ItemCategory if match found, None otherwise
        """
        text_lower = text.lower()

        # Check each category's keywords
        # category_keywords has keys like "BICYCLE" (enum names)
        for category_name, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    # Convert enum name to ItemCategory
                    # e.g., "BICYCLE" -> ItemCategory.BICYCLE
                    try:
                        return ItemCategory[category_name]
                    except KeyError:
                        continue

        return None

    def extract_brand_model(self, text: str) -> str:
        """Extract brand and model information from text.

        Uses simple extraction - looks for capitalized words and numbers
        that likely represent brands and models.

        Args:
            text: User input text

        Returns:
            Extracted brand/model string, empty if none found
        """
        # Known brands (case-insensitive)
        known_brands = {
            "apple",
            "iphone",
            "samsung",
            "huawei",
            "trek",
            "giant",
            "specialized",
            "macbook",
            "dell",
            "hp",
            "lenovo",
            "asus",
            "acer",
        }

        # Remove common words that aren't brands
        common_words = {
            "my",
            "the",
            "was",
            "is",
            "stolen",
            "lost",
            "yesterday",
            "today",
            "red",
            "blue",
            "black",
            "white",
            "silver",
            "gold",
            "it",
            "at",
            "on",
            "in",
            "near",
            "from",
        }

        # Split into words
        words = text.split()

        # Extract potential brand/model words
        brand_model_words = []
        for word in words:
            # Clean punctuation
            clean_word = word.strip(",.!?;:")

            # Skip if common word
            if clean_word.lower() in common_words:
                continue

            # Keep if:
            # - Known brand
            # - Capitalized word
            # - Contains digits
            # - Common model suffix
            if clean_word and (
                clean_word.lower() in known_brands
                or clean_word[0].isupper()
                or any(c.isdigit() for c in clean_word)
                or clean_word.lower() in ["pro", "max", "air", "mini", "plus"]
            ):
                brand_model_words.append(clean_word)

        return " ".join(brand_model_words)

    def parse_location_text(self, text: str) -> str:
        """Parse location from text description.

        For now, just returns the full text. Future enhancement:
        extract specific location patterns.

        Args:
            text: User input text with location

        Returns:
            Location text
        """
        # For now, return the cleaned text
        # Future: implement NLP-based location extraction
        return text.strip()

    def parse_date(self, text: str) -> datetime | None:
        """Parse date from natural language text.

        Supports formats like:
        - "today"
        - "yesterday"
        - "2 days ago"
        - "15 Jan 2024"
        - "last week"

        Args:
            text: User input text with date

        Returns:
            Parsed datetime in UTC, or None if parsing fails or date is invalid
        """
        text_lower = text.lower().strip()

        # Handle skip/unknown - return current time as default
        if text_lower in ["skip", "unknown", "don't know", "dont know", "not sure"]:
            return datetime.now(UTC)

        # Quick validation: reject obviously invalid text to avoid slow dateparser calls
        # Text should be reasonably short and contain date-related keywords or numbers
        if len(text) > 100:
            return None

        has_date_indicator = any(
            keyword in text_lower
            for keyword in [
                "today",
                "yesterday",
                "tomorrow",
                "ago",
                "last",
                "week",
                "month",
                "year",
                "jan",
                "feb",
                "mar",
                "apr",
                "may",
                "jun",
                "jul",
                "aug",
                "sep",
                "oct",
                "nov",
                "dec",
            ]
        ) or any(char.isdigit() for char in text)

        if not has_date_indicator:
            return None

        # Parse the date using dateparser
        parsed = dateparser.parse(
            text,
            settings={
                "TIMEZONE": "UTC",
                "RETURN_AS_TIMEZONE_AWARE": True,
                "PREFER_DATES_FROM": "past",  # Prefer past dates for "2 days"
                "STRICT_PARSING": True,  # Stricter parsing to avoid false positives
            },
        )

        if parsed is None:
            return None

        # Type narrowing for MyPy - ensure we have a datetime object
        if not isinstance(parsed, datetime):
            return None

        # Validate: date must not be in the future
        now = datetime.now(UTC)
        if parsed > now:
            return None

        return parsed
