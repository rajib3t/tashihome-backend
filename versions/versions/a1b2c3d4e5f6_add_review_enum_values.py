"""add review enum values

Revision ID: a1b2c3d4e5f6
Revises: 1d2e3f4a5b6c
Create Date: 2026-09-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '1d2e3f4a5b6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE reviewstatus ADD VALUE IF NOT EXISTS 'PENDING'")
    op.execute("ALTER TYPE reviewstatus ADD VALUE IF NOT EXISTS 'REJECTED'")
    op.execute("ALTER TYPE reviewstatus ADD VALUE IF NOT EXISTS 'pending'")
    op.execute("ALTER TYPE reviewstatus ADD VALUE IF NOT EXISTS 'rejected'")


def downgrade() -> None:
    pass
