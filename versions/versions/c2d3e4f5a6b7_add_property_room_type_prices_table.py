"""add property room type prices table and room type price columns

Revision ID: c2d3e4f5a6b7
Revises: 24071b64e5fc
Create Date: 2026-09-06 17:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, Sequence[str], None] = '24071b64e5fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add price_per_night and sale_per_night to property_room_types
    op.add_column(
        'property_room_types',
        sa.Column('price_per_night', sa.Numeric(precision=12, scale=2), server_default='0', nullable=True),
    )
    op.add_column(
        'property_room_types',
        sa.Column('sale_per_night', sa.Numeric(precision=12, scale=2), server_default='0', nullable=True),
    )

    # 2. Create property_room_type_prices table
    op.create_table(
        'property_room_type_prices',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        sa.Column('property_room_type_id', sa.BigInteger(), nullable=False),
        sa.Column('occupancy', sa.Integer(), nullable=False),
        sa.Column('price_per_night', sa.Numeric(precision=12, scale=2), server_default='0', nullable=False),
        sa.Column('sale_per_night', sa.Numeric(precision=12, scale=2), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['property_room_type_id'], ['property_room_types.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('property_room_type_id', 'occupancy', name='uq_property_room_type_price_occupancy'),
        sa.CheckConstraint('occupancy > 0', name='chk_room_price_occupancy'),
        sa.CheckConstraint('price_per_night >= 0', name='chk_room_price_positive'),
        sa.CheckConstraint('sale_per_night >= 0', name='chk_room_sale_price_positive'),
    )
    op.create_index(op.f('ix_property_room_type_prices_public_id'), 'property_room_type_prices', ['public_id'], unique=True)
    op.create_index(op.f('ix_property_room_type_prices_property_room_type_id'), 'property_room_type_prices', ['property_room_type_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_property_room_type_prices_property_room_type_id'), table_name='property_room_type_prices')
    op.drop_index(op.f('ix_property_room_type_prices_public_id'), table_name='property_room_type_prices')
    op.drop_table('property_room_type_prices')
    op.drop_column('property_room_types', 'sale_per_night')
    op.drop_column('property_room_types', 'price_per_night')

