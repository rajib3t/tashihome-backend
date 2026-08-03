"""add unique constraint to companies user_id and name

Revision ID: 2f7c9d8e1a44
Revises: b98bb49acd63
Create Date: 2026-08-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f7c9d8e1a44'
down_revision: Union[str, Sequence[str], None] = 'b98bb49acd63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint('uq_companies_user_id', 'companies', ['user_id'])
    op.create_unique_constraint('uq_companies_name', 'companies', ['name'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_companies_name', 'companies', type_='unique')
    op.drop_constraint('uq_companies_user_id', 'companies', type_='unique')
