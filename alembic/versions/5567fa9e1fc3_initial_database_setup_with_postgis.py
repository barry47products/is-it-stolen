"""Initial database setup with PostGIS

Revision ID: 5567fa9e1fc3
Revises:
Create Date: 2025-10-03 10:05:11.131500

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5567fa9e1fc3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology")


def downgrade() -> None:
    """Downgrade schema."""
    # Disable PostGIS extensions (CASCADE to handle dependencies)
    op.execute("DROP EXTENSION IF EXISTS postgis_topology CASCADE")
    op.execute("DROP EXTENSION IF EXISTS postgis CASCADE")
