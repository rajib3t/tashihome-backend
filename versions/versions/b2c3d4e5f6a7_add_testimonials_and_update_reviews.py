"""add testimonials table and update review status default

Revision ID: b2c3d4e5f6a7
Revises: a2b3c4d5e6f7
Create Date: 2026-09-03 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create testimonials table
    op.create_table(
        'testimonials',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('public_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('user_role', sa.String(length=50), server_default='user', nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('designation', sa.String(length=255), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('rating', sa.SmallInteger(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column(
            'status',
            sa.Enum('PENDING', 'APPROVED', 'REJECTED', 'HIDDEN', 'pending', 'approved', 'rejected', 'hidden', name='testimonialstatus'),
            server_default='PENDING',
            nullable=False,
        ),
        sa.Column('is_featured', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('rating IS NULL OR (rating >= 1 AND rating <= 5)', name='chk_testimonials_rating'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_testimonials_public_id'), 'testimonials', ['public_id'], unique=True)
    op.create_index(op.f('ix_testimonials_user_id'), 'testimonials', ['user_id'], unique=False)
    op.create_index(op.f('ix_testimonials_user_role'), 'testimonials', ['user_role'], unique=False)
    op.create_index(op.f('ix_testimonials_status'), 'testimonials', ['status'], unique=False)
    op.create_index(op.f('ix_testimonials_is_featured'), 'testimonials', ['is_featured'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_testimonials_is_featured'), table_name='testimonials')
    op.drop_index(op.f('ix_testimonials_status'), table_name='testimonials')
    op.drop_index(op.f('ix_testimonials_user_role'), table_name='testimonials')
    op.drop_index(op.f('ix_testimonials_user_id'), table_name='testimonials')
    op.drop_index(op.f('ix_testimonials_public_id'), table_name='testimonials')
    op.drop_table('testimonials')
    op.execute("DROP TYPE IF EXISTS testimonialstatus")
