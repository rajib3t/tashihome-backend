"""add invoice_number to bookings

Revision ID: e3a1f2b4c5d6
Revises: 638ad7af742d, 3c1f2a4b5d66
Create Date: 2026-08-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3a1f2b4c5d6'
down_revision: Union[str, Sequence[str], None] = ('638ad7af742d', '3c1f2a4b5d66')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'bookings',
        sa.Column('invoice_number', sa.String(length=30), nullable=True),
    )
    op.create_unique_constraint(
        'uq_bookings_invoice_number', 'bookings', ['invoice_number']
    )
    op.create_index(
        'ix_bookings_invoice_number', 'bookings', ['invoice_number'], unique=True
    )


def downgrade() -> None:
    op.drop_index('ix_bookings_invoice_number', table_name='bookings')
    op.drop_constraint('uq_bookings_invoice_number', 'bookings', type_='unique')
    op.drop_column('bookings', 'invoice_number')
