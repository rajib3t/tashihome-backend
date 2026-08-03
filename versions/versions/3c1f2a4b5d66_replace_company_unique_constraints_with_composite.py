"""replace company unique constraints with composite user_id and name

Revision ID: 3c1f2a4b5d66
Revises: 2f7c9d8e1a44
Create Date: 2026-08-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c1f2a4b5d66'
down_revision: Union[str, Sequence[str], None] = '2f7c9d8e1a44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('uq_companies_name', 'companies', type_='unique')
    op.drop_constraint('uq_companies_user_id', 'companies', type_='unique')
    op.create_unique_constraint('uq_companies_user_id_name', 'companies', ['user_id', 'name'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_companies_user_id_name', 'companies', type_='unique')
    op.create_unique_constraint('uq_companies_user_id', 'companies', ['user_id'])
    op.create_unique_constraint('uq_companies_name', 'companies', ['name'])
