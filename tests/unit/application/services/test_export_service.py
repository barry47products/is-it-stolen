"""Unit tests for ExportService."""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.services.export_service import ExportFormat, ExportService
from src.domain.entities.stolen_item import ItemStatus, StolenItem
from src.domain.exceptions.domain_exceptions import ItemNotFoundError
from src.domain.repositories.stolen_item_repository import IStolenItemRepository
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber
from src.domain.value_objects.police_reference import PoliceReference


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Create mock repository."""
    return AsyncMock(spec=IStolenItemRepository)


@pytest.fixture
def export_service(mock_repository: AsyncMock) -> ExportService:
    """Create export service with mock repository."""
    return ExportService(repository=mock_repository)


@pytest.fixture
def sample_item() -> StolenItem:
    """Create sample stolen item for testing."""
    return StolenItem(
        report_id=uuid4(),
        reporter_phone=PhoneNumber("+27821234567"),
        item_type=ItemCategory.BICYCLE,
        description="Red mountain bike with Trek logo",
        stolen_date=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
        location=Location(
            latitude=-33.9249, longitude=18.4241, address="Cape Town, South Africa"
        ),
        brand="Trek",
        model="X-Caliber 8",
        serial_number="WTU123456",
        color="Red",
        status=ItemStatus.ACTIVE,
        created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
        updated_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
    )


@pytest.fixture
def verified_item() -> StolenItem:
    """Create verified stolen item for testing."""
    return StolenItem(
        report_id=uuid4(),
        reporter_phone=PhoneNumber("+27821234567"),
        item_type=ItemCategory.PHONE,
        description="iPhone 13 Pro",
        stolen_date=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
        location=Location(latitude=-33.9249, longitude=18.4241),
        status=ItemStatus.ACTIVE,
        created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
        updated_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
        police_reference=PoliceReference("CR/2024/123456"),
        verified_at=datetime(2024, 1, 16, 12, 0, 0, tzinfo=UTC),
    )


@pytest.mark.unit
class TestExportService:
    """Unit tests for ExportService."""

    @pytest.mark.asyncio
    async def test_exports_item_as_json(
        self,
        export_service: ExportService,
        mock_repository: AsyncMock,
        sample_item: StolenItem,
    ) -> None:
        """Should export item as JSON format."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_item

        # Act
        result = await export_service.export_item(
            sample_item.report_id, ExportFormat.JSON
        )

        # Assert
        data = json.loads(result)
        assert data["report_id"] == str(sample_item.report_id)
        assert data["item_type"] == "bicycle"
        assert data["description"] == "Red mountain bike with Trek logo"
        assert data["brand"] == "Trek"
        assert data["model"] == "X-Caliber 8"
        assert data["serial_number"] == "WTU123456"
        assert data["color"] == "Red"
        assert data["status"] == "active"
        assert data["is_verified"] is False

    @pytest.mark.asyncio
    async def test_exports_item_as_text(
        self,
        export_service: ExportService,
        mock_repository: AsyncMock,
        sample_item: StolenItem,
    ) -> None:
        """Should export item as plain text format."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_item

        # Act
        result = await export_service.export_item(
            sample_item.report_id, ExportFormat.TEXT
        )

        # Assert
        assert "STOLEN ITEM REPORT" in result
        assert str(sample_item.report_id) in result
        assert "Red mountain bike with Trek logo" in result
        assert "Trek" in result
        assert "X-Caliber 8" in result
        assert "WTU123456" in result
        assert "Red" in result
        assert "Active" in result

    @pytest.mark.asyncio
    async def test_exports_verified_item_includes_police_reference(
        self,
        export_service: ExportService,
        mock_repository: AsyncMock,
        verified_item: StolenItem,
    ) -> None:
        """Should include police reference for verified items."""
        # Arrange
        mock_repository.find_by_id.return_value = verified_item

        # Act
        result_json = await export_service.export_item(
            verified_item.report_id, ExportFormat.JSON
        )
        result_text = await export_service.export_item(
            verified_item.report_id, ExportFormat.TEXT
        )

        # Assert - JSON
        data = json.loads(result_json)
        assert data["is_verified"] is True
        assert data["police_reference"] == "CR/2024/123456"
        assert data["verified_at"] is not None

        # Assert - TEXT
        assert "Verified: Yes" in result_text
        assert "CR/2024/123456" in result_text
        assert "Verified At:" in result_text

    @pytest.mark.asyncio
    async def test_exports_item_with_minimal_fields(
        self,
        export_service: ExportService,
        mock_repository: AsyncMock,
    ) -> None:
        """Should export item with only required fields."""
        # Arrange
        minimal_item = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Missing item",
            stolen_date=datetime(2024, 1, 15, tzinfo=UTC),
            location=None,
            status=ItemStatus.ACTIVE,
            created_at=datetime(2024, 1, 15, tzinfo=UTC),
            updated_at=datetime(2024, 1, 15, tzinfo=UTC),
        )
        mock_repository.find_by_id.return_value = minimal_item

        # Act
        result_json = await export_service.export_item(
            minimal_item.report_id, ExportFormat.JSON
        )
        result_text = await export_service.export_item(
            minimal_item.report_id, ExportFormat.TEXT
        )

        # Assert - JSON
        data = json.loads(result_json)
        assert data["brand"] is None
        assert data["model"] is None
        assert data["serial_number"] is None
        assert data["color"] is None
        assert data["location"] is None

        # Assert - TEXT (should not crash)
        assert "Missing item" in result_text
        assert "STOLEN ITEM REPORT" in result_text

    @pytest.mark.asyncio
    async def test_raises_error_when_item_not_found(
        self,
        export_service: ExportService,
        mock_repository: AsyncMock,
    ) -> None:
        """Should raise ItemNotFoundError when item doesn't exist."""
        # Arrange
        report_id = uuid4()
        mock_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ItemNotFoundError) as exc_info:
            await export_service.export_item(report_id, ExportFormat.JSON)

        assert str(report_id) in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_exports_user_items_as_json(
        self,
        export_service: ExportService,
        mock_repository: AsyncMock,
        sample_item: StolenItem,
    ) -> None:
        """Should export all user items as JSON."""
        # Arrange
        phone = PhoneNumber("+27821234567")
        item2 = StolenItem(
            report_id=uuid4(),
            reporter_phone=phone,
            item_type=ItemCategory.PHONE,
            description="iPhone",
            stolen_date=datetime(2024, 1, 16, tzinfo=UTC),
            location=None,
            status=ItemStatus.RECOVERED,
            created_at=datetime(2024, 1, 16, tzinfo=UTC),
            updated_at=datetime(2024, 1, 16, tzinfo=UTC),
        )
        mock_repository.find_by_reporter.return_value = [sample_item, item2]

        # Act
        result = await export_service.export_user_items(phone, ExportFormat.JSON)

        # Assert
        data = json.loads(result)
        assert data["total_count"] == 2
        assert "exported_at" in data
        assert len(data["items"]) == 2
        assert data["items"][0]["item_type"] == "bicycle"
        assert data["items"][1]["item_type"] == "phone"

    @pytest.mark.asyncio
    async def test_exports_user_items_as_text(
        self,
        export_service: ExportService,
        mock_repository: AsyncMock,
        sample_item: StolenItem,
    ) -> None:
        """Should export all user items as plain text."""
        # Arrange
        phone = PhoneNumber("+27821234567")
        item2 = StolenItem(
            report_id=uuid4(),
            reporter_phone=phone,
            item_type=ItemCategory.PHONE,
            description="iPhone",
            stolen_date=datetime(2024, 1, 16, tzinfo=UTC),
            location=None,
            status=ItemStatus.RECOVERED,
            created_at=datetime(2024, 1, 16, tzinfo=UTC),
            updated_at=datetime(2024, 1, 16, tzinfo=UTC),
        )
        mock_repository.find_by_reporter.return_value = [sample_item, item2]

        # Act
        result = await export_service.export_user_items(phone, ExportFormat.TEXT)

        # Assert
        assert "STOLEN ITEMS REPORT - 2 item(s)" in result
        assert "ITEM 1 OF 2" in result
        assert "ITEM 2 OF 2" in result
        assert "Bicycle" in result
        assert "Phone" in result

    @pytest.mark.asyncio
    async def test_exports_empty_user_items_list(
        self,
        export_service: ExportService,
        mock_repository: AsyncMock,
    ) -> None:
        """Should handle empty items list gracefully."""
        # Arrange
        phone = PhoneNumber("+27821234567")
        mock_repository.find_by_reporter.return_value = []

        # Act
        result_json = await export_service.export_user_items(phone, ExportFormat.JSON)
        result_text = await export_service.export_user_items(phone, ExportFormat.TEXT)

        # Assert - JSON
        data = json.loads(result_json)
        assert data["total_count"] == 0
        assert data["items"] == []

        # Assert - TEXT
        assert "No stolen items found" in result_text

    @pytest.mark.asyncio
    async def test_uses_default_json_format(
        self,
        export_service: ExportService,
        mock_repository: AsyncMock,
        sample_item: StolenItem,
    ) -> None:
        """Should use JSON format by default."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_item

        # Act
        result = await export_service.export_item(sample_item.report_id)

        # Assert - should be valid JSON
        data = json.loads(result)
        assert data["report_id"] == str(sample_item.report_id)

    @pytest.mark.asyncio
    async def test_truncates_long_descriptions_in_summary(
        self,
        export_service: ExportService,
        mock_repository: AsyncMock,
    ) -> None:
        """Should truncate long descriptions in text summary."""
        # Arrange
        phone = PhoneNumber("+27821234567")
        long_description = "A" * 100
        item = StolenItem(
            report_id=uuid4(),
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description=long_description,
            stolen_date=datetime(2024, 1, 15, tzinfo=UTC),
            location=None,
            status=ItemStatus.ACTIVE,
            created_at=datetime(2024, 1, 15, tzinfo=UTC),
            updated_at=datetime(2024, 1, 15, tzinfo=UTC),
        )
        mock_repository.find_by_reporter.return_value = [item]

        # Act
        result = await export_service.export_user_items(phone, ExportFormat.TEXT)

        # Assert - description should be truncated with ellipsis
        assert "A" * 50 + "..." in result
        assert "A" * 51 not in result

    @pytest.mark.asyncio
    async def test_includes_location_when_present(
        self,
        export_service: ExportService,
        mock_repository: AsyncMock,
        sample_item: StolenItem,
    ) -> None:
        """Should include location details when present."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_item

        # Act
        result_json = await export_service.export_item(
            sample_item.report_id, ExportFormat.JSON
        )
        result_text = await export_service.export_item(
            sample_item.report_id, ExportFormat.TEXT
        )

        # Assert - JSON
        data = json.loads(result_json)
        assert data["location"]["latitude"] == -33.9249
        assert data["location"]["longitude"] == 18.4241
        assert data["location"]["address"] == "Cape Town, South Africa"

        # Assert - TEXT
        assert "LOCATION" in result_text
        assert "-33.9249, 18.4241" in result_text
        assert "Cape Town, South Africa" in result_text

    @pytest.mark.asyncio
    async def test_formats_timestamps_correctly(
        self,
        export_service: ExportService,
        mock_repository: AsyncMock,
        sample_item: StolenItem,
    ) -> None:
        """Should format timestamps in readable format."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_item

        # Act
        result = await export_service.export_item(
            sample_item.report_id, ExportFormat.TEXT
        )

        # Assert - timestamps should be formatted
        assert "2024-01-15 10:30:00 UTC" in result
        assert "Reported At:" in result
        assert "Last Updated:" in result

    @pytest.mark.asyncio
    async def test_exports_verified_item_without_verified_at_edge_case(
        self,
        export_service: ExportService,
        mock_repository: AsyncMock,
    ) -> None:
        """Should handle edge case of verified item without verified_at timestamp."""
        # Arrange - create a mock item that has police_reference and is_verified=True
        # but verified_at=None (edge case that shouldn't happen in practice)
        from unittest.mock import MagicMock

        mock_item = MagicMock(spec=StolenItem)
        mock_item.report_id = uuid4()
        mock_item.reporter_phone = PhoneNumber("+27821234567")
        mock_item.item_type = ItemCategory.PHONE
        mock_item.description = "iPhone 13 Pro"
        mock_item.stolen_date = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        mock_item.location = None
        mock_item.brand = None
        mock_item.model = None
        mock_item.serial_number = None
        mock_item.color = None
        mock_item.status = ItemStatus.ACTIVE
        mock_item.is_verified = True  # Verified
        mock_item.police_reference = PoliceReference("CR/2024/123456")
        mock_item.verified_at = None  # But no timestamp (edge case)
        mock_item.created_at = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        mock_item.updated_at = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)

        mock_repository.find_by_id.return_value = mock_item

        # Act
        result = await export_service.export_item(
            mock_item.report_id, ExportFormat.TEXT
        )

        # Assert - should include police reference but not verified_at timestamp
        assert "CR/2024/123456" in result
        assert "Police Reference: CR/2024/123456" in result
        assert "Verified At:" not in result
