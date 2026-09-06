"""add taxes table

Revision ID: d4e5f6a7b8c9
Revises: c2d3e4f5a6b7
Create Date: 2026-09-06 23:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create ENUM types safely if PostgreSQL
    tax_status_enum = postgresql.ENUM('ACTIVE', 'INACTIVE', 'active', 'inactive', name='taxstatus', create_type=False)
    tax_type_enum = postgresql.ENUM('PERCENTAGE', 'FIXED', 'percentage', 'fixed', name='taxtype', create_type=False)
    
    bind = op.get_bind()
    tax_status_enum.create(bind, checkfirst=True)
    tax_type_enum.create(bind, checkfirst=True)

    op.execute("ALTER TYPE taxstatus ADD VALUE IF NOT EXISTS 'ACTIVE'")
    op.execute("ALTER TYPE taxstatus ADD VALUE IF NOT EXISTS 'INACTIVE'")
    op.execute("ALTER TYPE taxstatus ADD VALUE IF NOT EXISTS 'active'")
    op.execute("ALTER TYPE taxstatus ADD VALUE IF NOT EXISTS 'inactive'")

    op.execute("ALTER TYPE taxtype ADD VALUE IF NOT EXISTS 'PERCENTAGE'")
    op.execute("ALTER TYPE taxtype ADD VALUE IF NOT EXISTS 'FIXED'")
    op.execute("ALTER TYPE taxtype ADD VALUE IF NOT EXISTS 'percentage'")
    op.execute("ALTER TYPE taxtype ADD VALUE IF NOT EXISTS 'fixed'")

    # 2. Create taxes table
    op.create_table(
        'taxes',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('rate', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),
        sa.Column('tax_type', tax_type_enum, nullable=False, server_default='percentage'),
        sa.Column('is_inclusive', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('gst_number', sa.String(length=50), nullable=True),
        sa.Column('legal_name', sa.String(length=255), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('hsn_sac_code', sa.String(length=50), nullable=True),
        sa.Column('cgst_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('sgst_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('igst_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', tax_status_enum, nullable=False, server_default='active'),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_taxes_public_id'), 'taxes', ['public_id'], unique=True)
    op.create_index(op.f('ix_taxes_code'), 'taxes', ['code'], unique=True)
    op.create_index(op.f('ix_taxes_status'), 'taxes', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_taxes_status'), table_name='taxes')
    op.drop_index(op.f('ix_taxes_code'), table_name='taxes')
    op.drop_index(op.f('ix_taxes_public_id'), table_name='taxes')
    op.drop_table('taxes')

    bind = op.get_bind()
    tax_status_enum = postgresql.ENUM('active', 'inactive', name='taxstatus', create_type=False)
    tax_type_enum = postgresql.ENUM('percentage', 'fixed', name='taxtype', create_type=False)
    tax_status_enum.drop(bind, checkfirst=True)
    tax_type_enum.drop(bind, checkfirst=True)

