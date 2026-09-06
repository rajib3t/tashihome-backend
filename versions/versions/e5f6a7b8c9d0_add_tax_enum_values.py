"""add tax enum values

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-07 00:18:00.000000

"""
from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add uppercase enum values to taxstatus and taxtype for compatibility."""
    op.execute("ALTER TYPE taxstatus ADD VALUE IF NOT EXISTS 'ACTIVE'")
    op.execute("ALTER TYPE taxstatus ADD VALUE IF NOT EXISTS 'INACTIVE'")
    op.execute("ALTER TYPE taxstatus ADD VALUE IF NOT EXISTS 'active'")
    op.execute("ALTER TYPE taxstatus ADD VALUE IF NOT EXISTS 'inactive'")

    op.execute("ALTER TYPE taxtype ADD VALUE IF NOT EXISTS 'PERCENTAGE'")
    op.execute("ALTER TYPE taxtype ADD VALUE IF NOT EXISTS 'FIXED'")
    op.execute("ALTER TYPE taxtype ADD VALUE IF NOT EXISTS 'percentage'")
    op.execute("ALTER TYPE taxtype ADD VALUE IF NOT EXISTS 'fixed'")


def downgrade() -> None:
    pass

