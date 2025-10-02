"""Category keywords configuration loader."""

from pathlib import Path
from typing import Any

import yaml


def load_category_keywords() -> dict[str, list[str]]:
    """Load item category keywords from YAML configuration.

    Returns:
        Dictionary mapping category names to lists of keywords

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config format is invalid
    """
    config_path = _get_config_path()

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with config_path.open("r") as file:
        data: dict[str, Any] = yaml.safe_load(file)

    if "categories" not in data:
        raise ValueError("Invalid config: missing 'categories' key")

    categories = data["categories"]
    if not isinstance(categories, dict):
        raise ValueError("Invalid config: 'categories' must be a dictionary")

    _validate_keywords(categories)

    return categories


def _get_config_path() -> Path:
    """Get path to category keywords configuration file."""
    return (
        Path(__file__).parent.parent.parent.parent / "config" / "item_categories.yaml"
    )


def _validate_keywords(categories: dict[str, Any]) -> None:
    """Validate keyword structure.

    Args:
        categories: Category keyword mappings to validate

    Raises:
        ValueError: If keywords structure is invalid
    """
    for category_name, keywords in categories.items():
        if not isinstance(keywords, list):
            raise ValueError(
                f"Invalid config: keywords for '{category_name}' must be a list"
            )

        if not keywords:
            raise ValueError(f"Invalid config: '{category_name}' has no keywords")

        for keyword in keywords:
            if not isinstance(keyword, str):
                raise ValueError(
                    f"Invalid config: keyword in '{category_name}' must be a string"
                )
