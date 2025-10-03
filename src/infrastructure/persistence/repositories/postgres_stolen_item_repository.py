"""PostgreSQL implementation of StolenItemRepository."""

from uuid import UUID

from geoalchemy2.functions import ST_DWithin
from geoalchemy2.types import Geography
from sqlalchemy import cast

from src.domain.entities.stolen_item import ItemStatus, StolenItem
from src.domain.exceptions.domain_exceptions import RepositoryError
from src.domain.repositories.stolen_item_repository import IStolenItemRepository
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber
from src.domain.value_objects.police_reference import PoliceReference
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models import StolenItemModel

METERS_PER_KM = 1000


class PostgresStolenItemRepository(IStolenItemRepository):
    """PostgreSQL repository implementation for StolenItem."""

    def _get_db(self):  # type: ignore[no-untyped-def]
        """Get database session context manager."""
        return get_db()

    def _to_model(self, item: StolenItem) -> StolenItemModel:
        """Convert domain entity to database model.

        Args:
            item: Domain entity

        Returns:
            Database model
        """
        # Create PostGIS Point from location using WKT format
        location_point = None
        if item.location:
            from geoalchemy2.elements import WKTElement

            location_point = WKTElement(
                f"POINT({item.location.longitude} {item.location.latitude})", srid=4326
            )

        return StolenItemModel(
            report_id=item.report_id,
            reporter_phone=item.reporter_phone.value,
            item_type=item.item_type.value,
            description=item.description,
            brand=item.brand,
            model=item.model,
            serial_number=item.serial_number,
            color=item.color,
            stolen_date=item.stolen_date,
            created_at=item.created_at,
            updated_at=item.updated_at,
            status=item.status.value,
            latitude=item.location.latitude if item.location else 0.0,
            longitude=item.location.longitude if item.location else 0.0,
            address=item.location.address if item.location else None,
            location_point=location_point,
            police_reference=item.police_reference.value
            if item.police_reference
            else None,
            verified_at=item.verified_at,
        )

    def _to_entity(self, model: StolenItemModel) -> StolenItem:
        """Convert database model to domain entity.

        Args:
            model: Database model

        Returns:
            Domain entity
        """
        location = Location(
            latitude=model.latitude,  # type: ignore[arg-type]
            longitude=model.longitude,  # type: ignore[arg-type]
            address=model.address,  # type: ignore[arg-type]
        )

        return StolenItem(
            report_id=model.report_id,  # type: ignore[arg-type]
            reporter_phone=PhoneNumber(model.reporter_phone),  # type: ignore[arg-type]
            item_type=ItemCategory(model.item_type),
            description=model.description,  # type: ignore[arg-type]
            brand=model.brand,  # type: ignore[arg-type]
            model=model.model,  # type: ignore[arg-type]
            serial_number=model.serial_number,  # type: ignore[arg-type]
            color=model.color,  # type: ignore[arg-type]
            stolen_date=model.stolen_date,  # type: ignore[arg-type]
            location=location,
            status=ItemStatus(model.status),
            created_at=model.created_at,  # type: ignore[arg-type]
            updated_at=model.updated_at,  # type: ignore[arg-type]
            police_reference=PoliceReference(model.police_reference)  # type: ignore[arg-type]
            if model.police_reference
            else None,
            verified_at=model.verified_at,  # type: ignore[arg-type]
        )

    async def save(self, item: StolenItem) -> None:
        """Persist a stolen item.

        Args:
            item: Stolen item to save

        Raises:
            RepositoryError: If save operation fails
        """
        try:
            with self._get_db() as db:
                model = self._to_model(item)
                db.merge(model)
                db.commit()
        except Exception as e:
            msg = f"Failed to save stolen item {item.report_id}"
            raise RepositoryError(msg, cause=e) from e

    async def find_by_id(self, item_id: UUID) -> StolenItem | None:
        """Find stolen item by ID.

        Args:
            item_id: Unique identifier

        Returns:
            Stolen item if found, None otherwise
        """
        with self._get_db() as db:
            model = db.query(StolenItemModel).filter_by(report_id=item_id).first()
            if model is None:
                return None
            return self._to_entity(model)

    async def find_by_reporter(self, reporter_phone: PhoneNumber) -> list[StolenItem]:
        """Find all stolen items reported by a phone number.

        Args:
            reporter_phone: Reporter's phone number

        Returns:
            List of stolen items
        """
        with self._get_db() as db:
            models = (
                db.query(StolenItemModel)
                .filter_by(reporter_phone=reporter_phone.value)
                .all()
            )
            return [self._to_entity(model) for model in models]

    async def find_nearby(
        self,
        location: Location,
        radius_km: float,
        category: ItemCategory | None = None,
    ) -> list[StolenItem]:
        """Find stolen items within radius of a location.

        Uses PostGIS ST_DWithin for efficient geospatial queries.

        Args:
            location: Center point for search
            radius_km: Search radius in kilometers
            category: Optional category filter

        Returns:
            List of stolen items within radius
        """
        with self._get_db() as db:
            from geoalchemy2.elements import WKTElement

            # Create PostGIS Point for search location
            search_point = WKTElement(
                f"POINT({location.longitude} {location.latitude})", srid=4326
            )

            # Convert km to meters for PostGIS
            radius_meters = radius_km * METERS_PER_KM

            # Build query with ST_DWithin for geospatial search
            # Cast to geography for accurate distance on sphere
            query = db.query(StolenItemModel).filter(
                ST_DWithin(
                    cast(StolenItemModel.location_point, Geography),
                    cast(search_point, Geography),
                    radius_meters,
                )
            )

            # Apply category filter if specified
            if category is not None:
                query = query.filter_by(item_type=category.value)

            models = query.all()
            return [self._to_entity(model) for model in models]

    async def find_by_category(
        self,
        category: ItemCategory,
        status: ItemStatus = ItemStatus.ACTIVE,
        limit: int = 100,
    ) -> list[StolenItem]:
        """Find stolen items by category.

        Args:
            category: Item category to search for
            status: Item status filter (default: ACTIVE)
            limit: Maximum number of results (default: 100)

        Returns:
            List of stolen items
        """
        with self._get_db() as db:
            query = (
                db.query(StolenItemModel)
                .filter_by(item_type=category.value, status=status.value)
                .limit(limit)
            )

            models = query.all()
            return [self._to_entity(model) for model in models]

    async def delete(self, item_id: UUID) -> bool:
        """Delete a stolen item.

        Args:
            item_id: Unique identifier

        Returns:
            True if deleted, False if not found
        """
        with self._get_db() as db:
            count = db.query(StolenItemModel).filter_by(report_id=item_id).delete()
            db.commit()
            return bool(count > 0)
