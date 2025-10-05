"""Message parser for extracting structured data from user input."""

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
