"""UserSegment enum for categorizing users by behavior."""

from enum import Enum


class UserSegment(str, Enum):
    """User segmentation categories for analytics.

    Segments help analyze behavior patterns across different user types.
    """

    FIRST_TIME = "first_time"
    RETURNING = "returning"
    POWER_USER = "power_user"
