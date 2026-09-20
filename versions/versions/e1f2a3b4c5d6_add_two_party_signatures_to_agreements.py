"""add two party signatures and partially_signed status to vendor_agreements

Revision ID: e1f2a3b4c5d6
Revises: d5e6f7a8b9c0
Create Date: 2026-09-17 00:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, Sequence[str], None] = 'd5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add 'partially_signed' to agreementstatus enum if not present
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'agreementstatus') THEN
                ALTER TYPE agreementstatus ADD VALUE IF NOT EXISTS 'partially_signed';
            END IF;
        END$$;
        """
    )

    # 2. Add bilateral / first-party execution columns to vendor_agreements
    op.add_column('vendor_agreements', sa.Column('first_party_signer_name', sa.String(length=255), nullable=True))
    op.add_column('vendor_agreements', sa.Column('first_party_signer_role', sa.String(length=100), nullable=True))
    op.add_column('vendor_agreements', sa.Column('first_party_signature_type', sa.String(length=50), nullable=True))
    op.add_column('vendor_agreements', sa.Column('first_party_signature_data', sa.Text(), nullable=True))
    op.add_column('vendor_agreements', sa.Column('first_party_signed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('vendor_agreements', sa.Column('first_party_signer_ip', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('vendor_agreements', 'first_party_signer_ip')
    op.drop_column('vendor_agreements', 'first_party_signed_at')
    op.drop_column('vendor_agreements', 'first_party_signature_data')
    op.drop_column('vendor_agreements', 'first_party_signature_type')
    op.drop_column('vendor_agreements', 'first_party_signer_role')
    op.drop_column('vendor_agreements', 'first_party_signer_name')

