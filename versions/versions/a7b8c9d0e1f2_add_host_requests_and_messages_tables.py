"""add host_requests and host_request_messages tables

Revision ID: a7b8c9d0e1f2
Revises: f4b2c1d3e5a7
Create Date: 2026-08-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, Sequence[str], None] = 'f4b2c1d3e5a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create host_requests table
    op.create_table(
        'host_requests',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('property_name', sa.String(length=255), nullable=True),
        sa.Column('property_type', sa.String(length=50), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('expected_rooms', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column(
            'status',
            sa.Enum('PENDING', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'CONVERTED', name='hostrequeststatus'),
            nullable=False,
            server_default='PENDING',
        ),
        sa.Column('reviewed_by', sa.BigInteger(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('converted_user_id', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['converted_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_host_requests_public_id'), 'host_requests', ['public_id'], unique=True)
    op.create_index(op.f('ix_host_requests_email'), 'host_requests', ['email'], unique=False)
    op.create_index(op.f('ix_host_requests_phone'), 'host_requests', ['phone'], unique=False)
    op.create_index(op.f('ix_host_requests_status'), 'host_requests', ['status'], unique=False)
    op.create_index(op.f('ix_host_requests_user_id'), 'host_requests', ['user_id'], unique=False)

    # Create host_request_messages table
    op.create_table(
        'host_request_messages',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('host_request_id', sa.BigInteger(), nullable=False),
        sa.Column('sender_id', sa.BigInteger(), nullable=True),
        sa.Column('sender_name', sa.String(length=255), nullable=False),
        sa.Column('sender_role', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_internal', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['host_request_id'], ['host_requests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_host_request_messages_public_id'), 'host_request_messages', ['public_id'], unique=True)
    op.create_index(op.f('ix_host_request_messages_host_request_id'), 'host_request_messages', ['host_request_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_host_request_messages_host_request_id'), table_name='host_request_messages')
    op.drop_index(op.f('ix_host_request_messages_public_id'), table_name='host_request_messages')
    op.drop_table('host_request_messages')

    op.drop_index(op.f('ix_host_requests_user_id'), table_name='host_requests')
    op.drop_index(op.f('ix_host_requests_status'), table_name='host_requests')
    op.drop_index(op.f('ix_host_requests_phone'), table_name='host_requests')
    op.drop_index(op.f('ix_host_requests_email'), table_name='host_requests')
    op.drop_index(op.f('ix_host_requests_public_id'), table_name='host_requests')
    op.drop_table('host_requests')
    op.execute("DROP TYPE IF EXISTS hostrequeststatus")

