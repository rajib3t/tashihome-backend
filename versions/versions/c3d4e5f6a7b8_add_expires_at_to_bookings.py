"""add expires_at to bookings

Revision ID: c3d4e5f6a7b8
Revises: b8c9d0e1f2a3
Create Date: 2026-09-12 15:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'bookings',
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f('ix_bookings_expires_at'),
        'bookings',
        ['expires_at'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_bookings_expires_at'), table_name='bookings')
    op.drop_column('bookings', 'expires_at')

