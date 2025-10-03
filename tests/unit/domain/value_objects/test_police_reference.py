"""Tests for police reference number value object."""

import pytest

from src.domain.value_objects.police_reference import PoliceReference


class TestPoliceReference:
    """Test police reference number validation."""

    def test_creates_valid_police_reference(self) -> None:
        """Should create police reference with valid format."""
        # Arrange & Act
        ref = PoliceReference("CR/2024/123456")

        # Assert
        assert ref.value == "CR/2024/123456"

    def test_validates_police_reference_format(self) -> None:
        """Should validate CR/YYYY/NNNNNN format."""
        # Arrange & Act
        ref = PoliceReference("CR/2023/000001")

        # Assert
        assert ref.value == "CR/2023/000001"

    def test_rejects_invalid_format(self) -> None:
        """Should reject reference without CR prefix."""
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid police reference format"):
            PoliceReference("XY/2024/123456")

    def test_rejects_invalid_year(self) -> None:
        """Should reject reference with invalid year."""
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid police reference format"):
            PoliceReference("CR/99/123456")

    def test_rejects_invalid_case_number(self) -> None:
        """Should reject reference with non-numeric case number."""
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid police reference format"):
            PoliceReference("CR/2024/ABC123")

    def test_normalizes_to_uppercase(self) -> None:
        """Should normalize to uppercase."""
        # Arrange & Act
        ref = PoliceReference("cr/2024/123456")

        # Assert
        assert ref.value == "CR/2024/123456"

    def test_police_reference_is_immutable(self) -> None:
        """Should be immutable."""
        # Arrange
        ref = PoliceReference("CR/2024/123456")

        # Act & Assert
        with pytest.raises(AttributeError):
            ref.value = "CR/2024/999999"  # type: ignore

    def test_police_reference_equality(self) -> None:
        """Should support equality comparison."""
        # Arrange
        ref1 = PoliceReference("CR/2024/123456")
        ref2 = PoliceReference("CR/2024/123456")
        ref3 = PoliceReference("CR/2024/999999")

        # Assert
        assert ref1 == ref2
        assert ref1 != ref3

    def test_accepts_different_year_formats(self) -> None:
        """Should accept 4-digit years from 2000 onwards."""
        # Arrange & Act
        ref2020 = PoliceReference("CR/2020/123456")
        ref2024 = PoliceReference("CR/2024/123456")

        # Assert
        assert ref2020.value == "CR/2020/123456"
        assert ref2024.value == "CR/2024/123456"

    def test_rejects_empty_reference(self) -> None:
        """Should reject empty reference."""
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid police reference format"):
            PoliceReference("")
