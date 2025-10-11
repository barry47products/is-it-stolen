"""MetricType enum for categorizing analytics events."""

from enum import Enum


class MetricType(str, Enum):
    """Types of analytics metrics tracked in the system.

    Each metric type represents a significant event in the user journey
    or business process that should be measured for analytics.
    """

    FLOW_STARTED = "flow_started"
    FLOW_COMPLETED = "flow_completed"
    FLOW_ABANDONED = "flow_abandoned"
    STEP_COMPLETED = "step_completed"
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    REPORT_CREATED = "report_created"
    REPORT_VERIFIED = "report_verified"
    ITEM_CHECKED = "item_checked"
