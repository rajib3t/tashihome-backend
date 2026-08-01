"""add account activation to token type

Revision ID: 7f3c2d9a1b44
Revises: 98e1364a159c
Create Date: 2026-08-01 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "7f3c2d9a1b44"
down_revision: Union[str, Sequence[str], None] = "4c2b1a7e9d10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE tokentype ADD VALUE IF NOT EXISTS 'ACCOUNT_ACTIVATION'")


def downgrade() -> None:
    """Downgrade schema."""
    # PostgreSQL enum values cannot be removed cleanly; rollback requires enum recreation.
    pass
