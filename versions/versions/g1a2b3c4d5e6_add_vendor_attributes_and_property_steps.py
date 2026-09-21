"""add vendor_id to attributes and property setup steps

Revision ID: g1a2b3c4d5e6
Revises: f2a3b4c5d6e7
Create Date: 2026-09-21 08:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'g1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'f2a3b4c5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Amenities: add vendor_id, update uniqueness
    op.add_column('amenities', sa.Column('vendor_id', sa.BigInteger(), nullable=True))
    op.create_foreign_key('fk_amenities_vendor_id_users', 'amenities', 'users', ['vendor_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_amenities_vendor_id', 'amenities', ['vendor_id'])
    
    op.drop_index('ix_amenities_name', table_name='amenities')
    op.create_index('ix_amenities_name', 'amenities', ['name'], unique=False)
    op.create_index(
        'uq_amenity_global_name',
        'amenities',
        [sa.text('lower(name)')],
        unique=True,
        postgresql_where=sa.text('vendor_id IS NULL'),
    )
    op.create_unique_constraint('uq_amenity_vendor_name', 'amenities', ['vendor_id', 'name'])

    # 2. Facilities: add vendor_id, update uniqueness
    op.add_column('facilities', sa.Column('vendor_id', sa.BigInteger(), nullable=True))
    op.create_foreign_key('fk_facilities_vendor_id_users', 'facilities', 'users', ['vendor_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_facilities_vendor_id', 'facilities', ['vendor_id'])
    
    op.drop_index('ix_facilities_name', table_name='facilities')
    op.create_index('ix_facilities_name', 'facilities', ['name'], unique=False)
    op.create_index(
        'uq_facility_global_name',
        'facilities',
        [sa.text('lower(name)')],
        unique=True,
        postgresql_where=sa.text('vendor_id IS NULL'),
    )
    op.create_unique_constraint('uq_facility_vendor_name', 'facilities', ['vendor_id', 'name'])

    # 3. Room Types: add vendor_id, update uniqueness
    op.add_column('room_types', sa.Column('vendor_id', sa.BigInteger(), nullable=True))
    op.create_foreign_key('fk_room_types_vendor_id_users', 'room_types', 'users', ['vendor_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_room_types_vendor_id', 'room_types', ['vendor_id'])
    
    op.drop_index('ix_room_types_name', table_name='room_types')
    op.create_index('ix_room_types_name', 'room_types', ['name'], unique=False)
    op.create_index(
        'uq_room_type_global_name',
        'room_types',
        [sa.text('lower(name)')],
        unique=True,
        postgresql_where=sa.text('vendor_id IS NULL'),
    )
    op.create_unique_constraint('uq_room_type_vendor_name', 'room_types', ['vendor_id', 'name'])

    # 4. Properties: add completed_steps and current_step
    op.add_column('properties', sa.Column('completed_steps', postgresql.ARRAY(sa.String()), nullable=True, server_default='{}'))
    op.add_column('properties', sa.Column('current_step', sa.String(length=50), nullable=True))


def downgrade() -> None:
    # 4. Properties
    op.drop_column('properties', 'current_step')
    op.drop_column('properties', 'completed_steps')

    # 3. Room Types
    op.drop_constraint('uq_room_type_vendor_name', 'room_types', type_='unique')
    op.drop_index('uq_room_type_global_name', table_name='room_types')
    op.drop_index('ix_room_types_name', table_name='room_types')
    op.create_index('ix_room_types_name', 'room_types', ['name'], unique=True)
    op.drop_index('ix_room_types_vendor_id', table_name='room_types')
    op.drop_constraint('fk_room_types_vendor_id_users', 'room_types', type_='foreignkey')
    op.drop_column('room_types', 'vendor_id')

    # 2. Facilities
    op.drop_constraint('uq_facility_vendor_name', 'facilities', type_='unique')
    op.drop_index('uq_facility_global_name', table_name='facilities')
    op.drop_index('ix_facilities_name', table_name='facilities')
    op.create_index('ix_facilities_name', 'facilities', ['name'], unique=True)
    op.drop_index('ix_facilities_vendor_id', table_name='facilities')
    op.drop_constraint('fk_facilities_vendor_id_users', 'facilities', type_='foreignkey')
    op.drop_column('facilities', 'vendor_id')

    # 1. Amenities
    op.drop_constraint('uq_amenity_vendor_name', 'amenities', type_='unique')
    op.drop_index('uq_amenity_global_name', table_name='amenities')
    op.drop_index('ix_amenities_name', table_name='amenities')
    op.create_index('ix_amenities_name', 'amenities', ['name'], unique=True)
    op.drop_index('ix_amenities_vendor_id', table_name='amenities')
    op.drop_constraint('fk_amenities_vendor_id_users', 'amenities', type_='foreignkey')
    op.drop_column('amenities', 'vendor_id')

