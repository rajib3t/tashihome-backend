"""add vendor_agreements table

Revision ID: d5e6f7a8b9c0
Revises: c3d4e5f6a7b8
Create Date: 2026-09-16 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'agreementtype') THEN
                CREATE TYPE agreementtype AS ENUM ('host_onboarding', 'commission_agreement', 'supplemental');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'agreementstatus') THEN
                CREATE TYPE agreementstatus AS ENUM ('draft', 'sent', 'viewed', 'signed', 'declined', 'expired', 'cancelled');
            END IF;
        END$$;
        """
    )

    agreement_type_enum = postgresql.ENUM(
        'host_onboarding',
        'commission_agreement',
        'supplemental',
        name='agreementtype',
        create_type=False,
    )

    agreement_status_enum = postgresql.ENUM(
        'draft',
        'sent',
        'viewed',
        'signed',
        'declined',
        'expired',
        'cancelled',
        name='agreementstatus',
        create_type=False,
    )

    op.create_table(
        'vendor_agreements',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        sa.Column('vendor_id', sa.BigInteger(), nullable=False),
        sa.Column('host_request_id', sa.BigInteger(), nullable=True),
        sa.Column('agreement_type', agreement_type_enum, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False, server_default='1.0'),
        sa.Column('status', agreement_status_enum, nullable=False, server_default='sent'),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('commission_percentage', sa.Numeric(precision=5, scale=2), nullable=False, server_default='10.00'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('viewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('signed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('signer_name', sa.String(length=255), nullable=True),
        sa.Column('signer_email', sa.String(length=255), nullable=True),
        sa.Column('signer_phone', sa.String(length=50), nullable=True),
        sa.Column('signature_type', sa.String(length=50), nullable=True),
        sa.Column('signature_data', sa.Text(), nullable=True),
        sa.Column('signer_ip', sa.String(length=100), nullable=True),
        sa.Column('signer_user_agent', sa.String(length=500), nullable=True),
        sa.Column('document_hash', sa.String(length=64), nullable=True),
        sa.Column('pdf_file_url', sa.String(length=500), nullable=True),
        sa.Column('terms_snapshot', sa.Text(), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['vendor_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['host_request_id'], ['host_requests.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index(op.f('ix_vendor_agreements_public_id'), 'vendor_agreements', ['public_id'], unique=True)
    op.create_index(op.f('ix_vendor_agreements_vendor_id'), 'vendor_agreements', ['vendor_id'], unique=False)
    op.create_index(op.f('ix_vendor_agreements_host_request_id'), 'vendor_agreements', ['host_request_id'], unique=False)
    op.create_index(op.f('ix_vendor_agreements_token'), 'vendor_agreements', ['token'], unique=True)
    op.create_index(op.f('ix_vendor_agreements_status'), 'vendor_agreements', ['status'], unique=False)
    op.create_index(op.f('ix_vendor_agreements_agreement_type'), 'vendor_agreements', ['agreement_type'], unique=False)
    op.create_index(op.f('ix_vendor_agreements_created_by'), 'vendor_agreements', ['created_by'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_vendor_agreements_created_by'), table_name='vendor_agreements')
    op.drop_index(op.f('ix_vendor_agreements_agreement_type'), table_name='vendor_agreements')
    op.drop_index(op.f('ix_vendor_agreements_status'), table_name='vendor_agreements')
    op.drop_index(op.f('ix_vendor_agreements_token'), table_name='vendor_agreements')
    op.drop_index(op.f('ix_vendor_agreements_host_request_id'), table_name='vendor_agreements')
    op.drop_index(op.f('ix_vendor_agreements_vendor_id'), table_name='vendor_agreements')
    op.drop_index(op.f('ix_vendor_agreements_public_id'), table_name='vendor_agreements')
    op.drop_table('vendor_agreements')

    op.execute('DROP TYPE IF EXISTS agreementstatus')
    op.execute('DROP TYPE IF EXISTS agreementtype')

