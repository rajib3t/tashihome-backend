"""add staff and agent to user roles

Revision ID: b1c2d3e4f5a6
Revises: a7b8c9d0e1f2
Create Date: 2026-08-31 21:18:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'staff'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'agent'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'STAFF'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'AGENT'")


def downgrade() -> None:
    """Downgrade schema."""
    # PostgreSQL does not support removing enum values directly.
    # If a rollback is required, a follow-up migration must recreate the enum.
    pass

