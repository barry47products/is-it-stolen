"""Service for exporting and generating reports of stolen items."""

import json
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID

from src.domain.entities.stolen_item import StolenItem
from src.domain.exceptions.domain_exceptions import ItemNotFoundError
from src.domain.repositories.stolen_item_repository import IStolenItemRepository
from src.domain.value_objects.phone_number import PhoneNumber


class ExportFormat(str, Enum):
    """Supported export formats."""

    JSON = "json"
    TEXT = "text"


class ExportService:
    """Service for generating reports and exports of stolen items."""

    def __init__(self, repository: IStolenItemRepository) -> None:
        """Initialize export service.

        Args:
            repository: Repository for accessing stolen items
        """
        self._repository = repository

    async def export_item(
        self, report_id: UUID, export_format: ExportFormat = ExportFormat.JSON
    ) -> str:
        """Export a single stolen item report.

        Args:
            report_id: ID of the item to export
            export_format: Format for export (JSON or TEXT)

        Returns:
            Formatted export string

        Raises:
            ItemNotFoundError: If item doesn't exist
        """
        item = await self._repository.find_by_id(report_id)
        if item is None:
            raise ItemNotFoundError(f"Item with ID {report_id} not found")

        if export_format == ExportFormat.JSON:
            return self._export_item_as_json(item)
        return self._export_item_as_text(item)

    async def export_user_items(
        self,
        reporter_phone: PhoneNumber,
        export_format: ExportFormat = ExportFormat.JSON,
    ) -> str:
        """Export all items for a user.

        Args:
            reporter_phone: Phone number of the reporter
            export_format: Format for export (JSON or TEXT)

        Returns:
            Formatted export string with all user's items
        """
        items = await self._repository.find_by_reporter(reporter_phone)

        if export_format == ExportFormat.JSON:
            return self._export_items_as_json(items)
        return self._export_items_as_text(items)

    def _export_item_as_json(self, item: StolenItem) -> str:
        """Export item as JSON format.

        Args:
            item: Item to export

        Returns:
            JSON string representation
        """
        data = {
            "report_id": str(item.report_id),
            "reporter_phone": item.reporter_phone.value,
            "item_type": item.item_type.value,
            "description": item.description,
            "stolen_date": item.stolen_date.isoformat(),
            "location": {
                "latitude": item.location.latitude,
                "longitude": item.location.longitude,
                "address": item.location.address,
            }
            if item.location
            else None,
            "brand": item.brand,
            "model": item.model,
            "serial_number": item.serial_number,
            "color": item.color,
            "status": item.status.value,
            "is_verified": item.is_verified,
            "police_reference": item.police_reference.value
            if item.police_reference
            else None,
            "verified_at": item.verified_at.isoformat() if item.verified_at else None,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
        }
        return json.dumps(data, indent=2)

    def _export_item_as_text(self, item: StolenItem) -> str:
        """Export item as plain text format.

        Args:
            item: Item to export

        Returns:
            Plain text representation
        """
        lines = [
            "=" * 60,
            "STOLEN ITEM REPORT",
            "=" * 60,
            "",
            f"Report ID: {item.report_id}",
            f"Reporter: {item.reporter_phone.value}",
            "",
            "ITEM DETAILS",
            "-" * 60,
            f"Type: {item.item_type.value.title()}",
            f"Description: {item.description}",
            f"Stolen Date: {self._format_datetime(item.stolen_date)}",
        ]

        if item.brand:
            lines.append(f"Brand: {item.brand}")
        if item.model:
            lines.append(f"Model: {item.model}")
        if item.serial_number:
            lines.append(f"Serial Number: {item.serial_number}")
        if item.color:
            lines.append(f"Color: {item.color}")

        if item.location:
            lines.extend(
                [
                    "",
                    "LOCATION",
                    "-" * 60,
                    f"Coordinates: {item.location.latitude}, {item.location.longitude}",
                ]
            )
            if item.location.address:
                lines.append(f"Address: {item.location.address}")

        lines.extend(
            [
                "",
                "STATUS",
                "-" * 60,
                f"Current Status: {item.status.value.title()}",
                f"Verified: {'Yes' if item.is_verified else 'No'}",
            ]
        )

        if item.is_verified and item.police_reference:
            lines.append(f"Police Reference: {item.police_reference.value}")
            if item.verified_at:
                lines.append(f"Verified At: {self._format_datetime(item.verified_at)}")

        lines.extend(
            [
                "",
                "TIMESTAMPS",
                "-" * 60,
                f"Reported At: {self._format_datetime(item.created_at)}",
                f"Last Updated: {self._format_datetime(item.updated_at)}",
                "",
                "=" * 60,
            ]
        )

        return "\n".join(lines)

    def _export_items_as_json(self, items: list[StolenItem]) -> str:
        """Export multiple items as JSON format.

        Args:
            items: List of items to export

        Returns:
            JSON string representation
        """
        data = {
            "total_count": len(items),
            "exported_at": datetime.now(UTC).isoformat(),
            "items": [json.loads(self._export_item_as_json(item)) for item in items],
        }
        return json.dumps(data, indent=2)

    def _export_items_as_text(self, items: list[StolenItem]) -> str:
        """Export multiple items as plain text format.

        Args:
            items: List of items to export

        Returns:
            Plain text representation
        """
        if not items:
            return "No stolen items found."

        lines = [
            "=" * 60,
            f"STOLEN ITEMS REPORT - {len(items)} item(s)",
            f"Exported: {self._format_datetime(datetime.now(UTC))}",
            "=" * 60,
            "",
        ]

        for i, item in enumerate(items, 1):
            lines.extend(
                [
                    f"ITEM {i} OF {len(items)}",
                    "-" * 60,
                    f"Report ID: {item.report_id}",
                    f"Type: {item.item_type.value.title()}",
                    f"Description: {item.description[:50]}{'...' if len(item.description) > 50 else ''}",
                    f"Status: {item.status.value.title()}",
                    f"Verified: {'Yes' if item.is_verified else 'No'}",
                    f"Reported: {self._format_datetime(item.created_at)}",
                    "",
                ]
            )

        lines.append("=" * 60)
        return "\n".join(lines)

    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime for display.

        Args:
            dt: Datetime to format

        Returns:
            Formatted string
        """
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
