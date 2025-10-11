"""Unit tests for MetricType enum."""

import pytest

from src.domain.value_objects.metric_type import MetricType


class TestMetricType:
    """Test suite for MetricType enum."""

    def test_has_flow_started_type(self) -> None:
        """Test MetricType has FLOW_STARTED."""
        # Act & Assert
        assert MetricType.FLOW_STARTED.value == "flow_started"

    def test_has_flow_completed_type(self) -> None:
        """Test MetricType has FLOW_COMPLETED."""
        # Act & Assert
        assert MetricType.FLOW_COMPLETED.value == "flow_completed"

    def test_has_flow_abandoned_type(self) -> None:
        """Test MetricType has FLOW_ABANDONED."""
        # Act & Assert
        assert MetricType.FLOW_ABANDONED.value == "flow_abandoned"

    def test_has_step_completed_type(self) -> None:
        """Test MetricType has STEP_COMPLETED."""
        # Act & Assert
        assert MetricType.STEP_COMPLETED.value == "step_completed"

    def test_has_session_started_type(self) -> None:
        """Test MetricType has SESSION_STARTED."""
        # Act & Assert
        assert MetricType.SESSION_STARTED.value == "session_started"

    def test_has_session_ended_type(self) -> None:
        """Test MetricType has SESSION_ENDED."""
        # Act & Assert
        assert MetricType.SESSION_ENDED.value == "session_ended"

    def test_has_report_created_type(self) -> None:
        """Test MetricType has REPORT_CREATED."""
        # Act & Assert
        assert MetricType.REPORT_CREATED.value == "report_created"

    def test_has_report_verified_type(self) -> None:
        """Test MetricType has REPORT_VERIFIED."""
        # Act & Assert
        assert MetricType.REPORT_VERIFIED.value == "report_verified"

    def test_has_item_checked_type(self) -> None:
        """Test MetricType has ITEM_CHECKED."""
        # Act & Assert
        assert MetricType.ITEM_CHECKED.value == "item_checked"

    def test_all_metric_types_are_strings(self) -> None:
        """Test all metric type values are strings."""
        # Act & Assert
        for metric_type in MetricType:
            assert isinstance(metric_type.value, str)

    def test_metric_types_are_unique(self) -> None:
        """Test all metric type values are unique."""
        # Arrange
        values = [mt.value for mt in MetricType]

        # Act & Assert
        assert len(values) == len(set(values))

    def test_can_get_metric_type_from_string(self) -> None:
        """Test getting MetricType from string value."""
        # Act
        metric_type = MetricType("flow_started")

        # Assert
        assert metric_type == MetricType.FLOW_STARTED

    def test_invalid_string_raises_value_error(self) -> None:
        """Test invalid string raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError):
            MetricType("invalid_metric_type")
