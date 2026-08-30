"""add razorpay fields to refund_requests

Revision ID: f4b2c1d3e5a7
Revises: e3a1f2b4c5d6
Create Date: 2026-08-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4b2c1d3e5a7'
down_revision: Union[str, Sequence[str], None] = 'e3a1f2b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'refund_requests',
        sa.Column('razorpay_refund_id', sa.String(length=255), nullable=True),
    )
    op.add_column(
        'refund_requests',
        sa.Column('razorpay_status', sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('refund_requests', 'razorpay_status')
    op.drop_column('refund_requests', 'razorpay_refund_id')

