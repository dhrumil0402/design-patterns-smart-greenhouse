"""devices_zone_assignment

Revision ID: c5f7fd775f00
Revises: 11bc62ffc4ae
Create Date: 2026-10-08 13:38:54.849394

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5f7fd775f00'
down_revision: Union[str, Sequence[str], None] = '11bc62ffc4ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('devices', sa.Column('zone_id', sa.UUID(), nullable=True))
    op.add_column('devices', sa.Column('location_id', sa.UUID(), nullable=True))
    op.create_index('ix_devices_location_id', 'devices', ['location_id'], unique=False)
    op.create_index('ix_devices_zone_id', 'devices', ['zone_id'], unique=False)
    op.create_foreign_key(
        'devices_zone_id_fkey', 'devices', 'zones', ['zone_id'], ['id'], ondelete='SET NULL'
    )
    op.create_foreign_key(
        'devices_location_id_fkey', 'devices', 'locations', ['location_id'], ['id'], ondelete='SET NULL'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('devices_location_id_fkey', 'devices', type_='foreignkey')
    op.drop_constraint('devices_zone_id_fkey', 'devices', type_='foreignkey')
    op.drop_index('ix_devices_zone_id', table_name='devices')
    op.drop_index('ix_devices_location_id', table_name='devices')
    op.drop_column('devices', 'location_id')
    op.drop_column('devices', 'zone_id')