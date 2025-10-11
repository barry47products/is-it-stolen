"""Service for calculating conversion rates and funnel metrics."""

from src.domain.value_objects.conversion_rate import ConversionRate


class ConversionCalculationService:
    """Domain service for calculating conversion metrics.

    Provides calculations for conversion rates, drop-off rates,
    and funnel analysis without external dependencies.
    """

    def calculate_conversion_rate(self, started: int, completed: int) -> ConversionRate:
        """Calculate conversion rate from started to completed.

        Args:
            started: Number who started
            completed: Number who completed

        Returns:
            ConversionRate value object

        Raises:
            ValueError: If counts are invalid
        """
        self._validate_counts(started, completed)
        if started == 0:
            return ConversionRate(0.0)
        rate = completed / started
        return ConversionRate(rate)

    def calculate_drop_off_rate(self, started: int, abandoned: int) -> ConversionRate:
        """Calculate drop-off rate.

        Args:
            started: Number who started
            abandoned: Number who abandoned

        Returns:
            Drop-off rate as ConversionRate
        """
        return self.calculate_conversion_rate(started, abandoned)

    def calculate_funnel_rates(
        self, funnel_data: dict[str, dict[str, int]]
    ) -> dict[str, ConversionRate]:
        """Calculate conversion rates for each step in funnel.

        Args:
            funnel_data: Dict mapping step names to started/completed counts

        Returns:
            Dict mapping step names to conversion rates
        """
        rates = {}
        for step_name, counts in funnel_data.items():
            started = counts["started"]
            completed = counts["completed"]
            rates[step_name] = self.calculate_conversion_rate(started, completed)
        return rates

    def identify_worst_step(self, funnel_data: dict[str, dict[str, int]]) -> str | None:
        """Identify the step with worst conversion rate.

        Args:
            funnel_data: Dict mapping step names to started/completed counts

        Returns:
            Name of worst performing step, or None if no data
        """
        if not funnel_data:
            return None
        rates = self.calculate_funnel_rates(funnel_data)
        return min(rates.items(), key=lambda x: x[1].value)[0]

    def _validate_counts(self, started: int, completed: int) -> None:
        """Validate count values.

        Args:
            started: Number who started
            completed: Number who completed

        Raises:
            ValueError: If counts are invalid
        """
        if started < 0 or completed < 0:
            raise ValueError("Counts cannot be negative")
        if completed > started:
            raise ValueError("Completed count cannot exceed started count")
