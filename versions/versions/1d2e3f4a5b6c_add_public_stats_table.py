"""add public stats table

Revision ID: 1d2e3f4a5b6c
Revises: 1c1eb3bb7ae2
Create Date: 2026-09-02 23:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1d2e3f4a5b6c'
down_revision: Union[str, Sequence[str], None] = '1c1eb3bb7ae2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'public_stats',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('total_homes', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_destinations', sa.Integer(), server_default='0', nullable=False),
        sa.Column('verified_percent', sa.Integer(), server_default='100', nullable=False),
        sa.Column('average_rating', sa.Float(), server_default='4.9', nullable=False),
        sa.Column('total_reviews', sa.Integer(), server_default='0', nullable=False),
        sa.Column('stats', sa.JSON(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_public_stats_key'), 'public_stats', ['key'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_public_stats_key'), table_name='public_stats')
    op.drop_table('public_stats')

