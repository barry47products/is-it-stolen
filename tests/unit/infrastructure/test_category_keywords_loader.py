"""Tests for category keywords configuration loader."""

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from src.infrastructure.config.category_keywords import (
    _validate_keywords,
    load_category_keywords,
)

pytestmark = pytest.mark.unit


class TestLoadCategoryKeywords:
    """Test suite for load_category_keywords function."""

    def test_loads_keywords_from_yaml_file(self) -> None:
        """Should load keywords from YAML configuration file."""
        keywords = load_category_keywords()

        assert isinstance(keywords, dict)
        assert "BICYCLE" in keywords
        assert "PHONE" in keywords
        assert "LAPTOP" in keywords
        assert "VEHICLE" in keywords

    def test_bicycle_keywords_match_config(self) -> None:
        """Should load correct bicycle keywords."""
        keywords = load_category_keywords()

        assert "bicycle" in keywords["BICYCLE"]
        assert "bike" in keywords["BICYCLE"]
        assert "cycle" in keywords["BICYCLE"]

    def test_raises_error_when_file_not_found(self) -> None:
        """Should raise FileNotFoundError when config file doesn't exist."""
        with (
            patch("pathlib.Path.exists", return_value=False),
            pytest.raises(FileNotFoundError, match="Configuration file not found"),
        ):
            load_category_keywords()

    def test_raises_error_when_categories_key_missing(self) -> None:
        """Should raise ValueError when 'categories' key is missing."""
        yaml_content = "invalid: data"
        mock_path = Path("/fake/path/config/item_categories.yaml")

        with (
            patch(
                "src.infrastructure.config.category_keywords._get_config_path",
                return_value=mock_path,
            ),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.open", mock_open(read_data=yaml_content)),
            pytest.raises(ValueError, match="missing 'categories' key"),
        ):
            load_category_keywords()

    def test_raises_error_when_categories_not_dict(self) -> None:
        """Should raise ValueError when 'categories' is not a dictionary."""
        yaml_content = "categories: not_a_dict"
        mock_path = Path("/fake/path/config/item_categories.yaml")

        with (
            patch(
                "src.infrastructure.config.category_keywords._get_config_path",
                return_value=mock_path,
            ),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.open", mock_open(read_data=yaml_content)),
            pytest.raises(ValueError, match="must be a dictionary"),
        ):
            load_category_keywords()


class TestValidateKeywords:
    """Test suite for _validate_keywords function."""

    def test_validates_keywords_must_be_list(self) -> None:
        """Should raise ValueError when keywords is not a list."""
        with pytest.raises(ValueError, match="must be a list"):
            _validate_keywords({"BICYCLE": "not_a_list"})

    def test_validates_keywords_not_empty(self) -> None:
        """Should raise ValueError when keyword list is empty."""
        with pytest.raises(ValueError, match="has no keywords"):
            _validate_keywords({"BICYCLE": []})

    def test_validates_keyword_is_string(self) -> None:
        """Should raise ValueError when keyword is not a string."""
        with pytest.raises(ValueError, match="must be a string"):
            _validate_keywords({"BICYCLE": [123]})

    def test_accepts_valid_keywords(self) -> None:
        """Should not raise error for valid keyword structure."""
        valid_keywords = {
            "BICYCLE": ["bike", "cycle"],
            "PHONE": ["mobile", "phone"],
        }
        _validate_keywords(valid_keywords)  # Should not raise
