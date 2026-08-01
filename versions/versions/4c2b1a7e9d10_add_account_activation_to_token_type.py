"""add account activation to token type

Revision ID: 4c2b1a7e9d10
Revises: 98e1364a159c
Create Date: 2026-08-01 10:26:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "4c2b1a7e9d10"
down_revision: Union[str, Sequence[str], None] = "98e1364a159c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE tokentype ADD VALUE IF NOT EXISTS 'account_activation_token'")


def downgrade() -> None:
    """Downgrade schema."""
    # PostgreSQL does not support removing enum values directly.
    # If a rollback is required, a follow-up migration must recreate the enum.
    pass
