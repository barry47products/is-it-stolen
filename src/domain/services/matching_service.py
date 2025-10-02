"""Item matching service using text similarity algorithms."""

from src.domain.entities.stolen_item import StolenItem

DEFAULT_THRESHOLD = 0.7
SERIAL_NUMBER_WEIGHT = 0.5
BRAND_WEIGHT = 0.2
MODEL_WEIGHT = 0.2
DESCRIPTION_WEIGHT = 0.1


class ItemMatchingService:
    """Service for matching stolen items based on text similarity.

    Uses weighted Jaccard similarity to compare items across multiple fields.
    Serial numbers are weighted highest, followed by brand, model, and description.
    """

    def __init__(self, threshold: float = DEFAULT_THRESHOLD) -> None:
        """Initialize matching service with similarity threshold.

        Args:
            threshold: Minimum similarity score (0-1) for items to be considered a match
        """
        self.threshold = threshold

    def calculate_similarity(self, item1: StolenItem, item2: StolenItem) -> float:
        """Calculate similarity score between two items.

        Args:
            item1: First stolen item
            item2: Second stolen item

        Returns:
            Similarity score between 0.0 (completely different) and 1.0 (identical)
        """
        scores: list[float] = []
        weights: list[float] = []

        # Serial number comparison (highest weight)
        if item1.serial_number and item2.serial_number:
            serial_match = 1.0 if item1.serial_number == item2.serial_number else 0.0
            scores.append(serial_match)
            weights.append(SERIAL_NUMBER_WEIGHT)
        elif item1.serial_number or item2.serial_number:
            # One has serial, other doesn't - add as no match
            scores.append(0.0)
            weights.append(SERIAL_NUMBER_WEIGHT)

        # Brand comparison
        if item1.brand or item2.brand:
            brand_sim = self._jaccard_similarity(item1.brand or "", item2.brand or "")
            scores.append(brand_sim)
            weights.append(BRAND_WEIGHT)

        # Model comparison
        if item1.model or item2.model:
            model_sim = self._jaccard_similarity(item1.model or "", item2.model or "")
            scores.append(model_sim)
            weights.append(MODEL_WEIGHT)

        # Description comparison (always present)
        desc_sim = self._jaccard_similarity(item1.description, item2.description)
        scores.append(desc_sim)
        weights.append(DESCRIPTION_WEIGHT)

        # Calculate weighted average
        total_weighted_score = sum(s * w for s, w in zip(scores, weights, strict=True))
        total_weight = sum(weights)

        return total_weighted_score / total_weight

    def is_match(self, item1: StolenItem, item2: StolenItem) -> bool:
        """Determine if two items match based on threshold.

        Args:
            item1: First stolen item
            item2: Second stolen item

        Returns:
            True if similarity score exceeds threshold, False otherwise
        """
        similarity = self.calculate_similarity(item1, item2)
        return similarity >= self.threshold

    @staticmethod
    def _jaccard_similarity(text1: str, text2: str) -> float:
        """Calculate Jaccard similarity between two text strings.

        Jaccard similarity = |intersection| / |union| of word sets

        Args:
            text1: First text string
            text2: Second text string

        Returns:
            Jaccard similarity coefficient (0-1)
        """
        if not text1 and not text2:
            return 1.0  # Both empty is considered identical
        if not text1 or not text2:
            return 0.0  # One empty, one not

        # Normalize and tokenize
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0

        # Calculate Jaccard coefficient
        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0
