"""Unit tests for ConversionCalculationService."""

import pytest

from src.domain.services.conversion_calculation_service import (
    ConversionCalculationService,
)
from src.domain.value_objects.conversion_rate import ConversionRate


class TestConversionCalculationService:
    """Test suite for ConversionCalculationService."""

    def test_calculates_conversion_rate(self) -> None:
        """Test calculating conversion rate from started and completed counts."""
        # Arrange
        service = ConversionCalculationService()
        started = 100
        completed = 75

        # Act
        rate = service.calculate_conversion_rate(started, completed)

        # Assert
        assert isinstance(rate, ConversionRate)
        assert rate.value == 0.75

    def test_returns_zero_rate_when_no_starts(self) -> None:
        """Test returns 0% conversion when no one started."""
        # Arrange
        service = ConversionCalculationService()
        started = 0
        completed = 0

        # Act
        rate = service.calculate_conversion_rate(started, completed)

        # Assert
        assert rate.value == 0.0

    def test_returns_one_hundred_percent_when_all_complete(self) -> None:
        """Test returns 100% when everyone completes."""
        # Arrange
        service = ConversionCalculationService()
        started = 50
        completed = 50

        # Act
        rate = service.calculate_conversion_rate(started, completed)

        # Assert
        assert rate.value == 1.0

    def test_rejects_negative_started_count(self) -> None:
        """Test rejects negative started count."""
        # Arrange
        service = ConversionCalculationService()

        # Act & Assert
        with pytest.raises(ValueError, match="cannot be negative"):
            service.calculate_conversion_rate(-10, 5)

    def test_rejects_negative_completed_count(self) -> None:
        """Test rejects negative completed count."""
        # Arrange
        service = ConversionCalculationService()

        # Act & Assert
        with pytest.raises(ValueError, match="cannot be negative"):
            service.calculate_conversion_rate(10, -5)

    def test_rejects_completed_greater_than_started(self) -> None:
        """Test rejects when completed exceeds started."""
        # Arrange
        service = ConversionCalculationService()

        # Act & Assert
        with pytest.raises(ValueError, match="cannot exceed"):
            service.calculate_conversion_rate(10, 15)

    def test_calculates_drop_off_rate(self) -> None:
        """Test calculating drop-off rate (inverse of conversion)."""
        # Arrange
        service = ConversionCalculationService()
        started = 100
        abandoned = 25

        # Act
        rate = service.calculate_drop_off_rate(started, abandoned)

        # Assert
        assert rate.value == 0.25

    def test_calculates_funnel_conversion_rates(self) -> None:
        """Test calculating conversion rates for multi-step funnel."""
        # Arrange
        service = ConversionCalculationService()
        funnel_data = {
            "step1": {"started": 100, "completed": 90},
            "step2": {"started": 90, "completed": 70},
            "step3": {"started": 70, "completed": 60},
        }

        # Act
        rates = service.calculate_funnel_rates(funnel_data)

        # Assert
        assert len(rates) == 3
        assert rates["step1"].value == 0.90
        assert rates["step2"].value == pytest.approx(0.777, abs=0.01)
        assert rates["step3"].value == pytest.approx(0.857, abs=0.01)

    def test_identifies_worst_performing_step(self) -> None:
        """Test identifying step with worst conversion."""
        # Arrange
        service = ConversionCalculationService()
        funnel_data = {
            "category": {"started": 100, "completed": 95},
            "description": {"started": 95, "completed": 50},  # Worst
            "location": {"started": 50, "completed": 48},
        }

        # Act
        worst_step = service.identify_worst_step(funnel_data)

        # Assert
        assert worst_step == "description"

    def test_identify_worst_step_with_empty_data(self) -> None:
        """Test identifying worst step returns None when no data."""
        # Arrange
        service = ConversionCalculationService()
        funnel_data = {}

        # Act
        worst_step = service.identify_worst_step(funnel_data)

        # Assert
        assert worst_step is None
