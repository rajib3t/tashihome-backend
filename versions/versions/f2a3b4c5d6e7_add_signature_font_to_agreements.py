"""add signature_font and first_party_signature_font to vendor_agreements

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-09-21 00:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2a3b4c5d6e7'
down_revision: Union[str, Sequence[str], None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('vendor_agreements', sa.Column('signature_font', sa.String(length=100), nullable=True))
    op.add_column('vendor_agreements', sa.Column('first_party_signature_font', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('vendor_agreements', 'first_party_signature_font')
    op.drop_column('vendor_agreements', 'signature_font')
