"""add agreement signing token and expand vendor agreement token

Revision ID: c7e8a9b0d1e2
Revises: 111c3b6a137c
Create Date: 2026-09-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c7e8a9b0d1e2"
down_revision: Union[str, Sequence[str], None] = "111c3b6a137c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE tokentype ADD VALUE IF NOT EXISTS 'AGREEMENT_SIGNING'")
    op.execute("ALTER TYPE tokentype ADD VALUE IF NOT EXISTS 'agreement_signing_token'")
    op.alter_column(

        'vendor_agreements',
        'token',
        type_=sa.String(length=1000),
        existing_type=sa.String(length=255),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'vendor_agreements',
        'token',
        type_=sa.String(length=255),
        existing_type=sa.String(length=1000),
        existing_nullable=False,
    )

