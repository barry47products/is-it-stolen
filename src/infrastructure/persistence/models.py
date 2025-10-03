"""SQLAlchemy database models for persistence layer."""

from __future__ import annotations

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Float, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from src.infrastructure.persistence.database import Base


class StolenItemModel(Base):  # type: ignore[no-any-unimported]
    """Database model for stolen item reports.

    Maps to the 'stolen_items' table with PostGIS geospatial support.
    This is the persistence representation of the StolenItem domain entity.
    """

    __tablename__ = "stolen_items"

    # Primary key
    report_id = Column(PGUUID(as_uuid=True), primary_key=True, nullable=False)

    # Reporter information
    reporter_phone = Column(String(20), nullable=False)

    # Item information
    item_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True)
    color = Column(String(50), nullable=True)

    # Temporal information
    stolen_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    # Status
    status = Column(String(20), nullable=False, default="active")

    # Location (separate columns for simple queries, plus PostGIS point)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(500), nullable=True)

    # PostGIS geometry column for geospatial queries
    # NOTE: GeoAlchemy2 automatically creates GIST index named idx_stolen_items_location_point
    location_point = Column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=True,
    )

    # Verification
    police_reference = Column(String(50), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Indexes for common queries
    __table_args__ = (
        # Index for finding items by reporter
        Index("ix_stolen_items_reporter_phone", "reporter_phone"),
        # Index for finding items by type and status
        Index("ix_stolen_items_type_status", "item_type", "status"),
        # Index for finding recent items
        Index("ix_stolen_items_created_at", "created_at"),
        # NOTE: GeoAlchemy2 automatically creates a GIST index for location_point
        # named idx_stolen_items_location_point
    )

    def __repr__(self) -> str:
        """String representation of StolenItemModel."""
        return (
            f"<StolenItemModel("
            f"report_id={self.report_id}, "
            f"item_type={self.item_type}, "
            f"status={self.status}"
            f")>"
        )
