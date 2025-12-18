"""add_schedule_fields_to_user_channel

Revision ID: b770522e31d8
Revises: 001
Create Date: 2025-12-18 09:45:31.749787

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b770522e31d8'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add schedule_enabled with server_default first, then remove default
    op.add_column('user_channels', sa.Column('schedule_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('user_channels', sa.Column('schedule_interval_hours', sa.Integer(), nullable=True))
    op.add_column('user_channels', sa.Column('last_scheduled_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('user_channels', sa.Column('next_scheduled_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f('ix_user_channels_next_scheduled_at'), 'user_channels', ['next_scheduled_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_channels_next_scheduled_at'), table_name='user_channels')
    op.drop_column('user_channels', 'next_scheduled_at')
    op.drop_column('user_channels', 'last_scheduled_at')
    op.drop_column('user_channels', 'schedule_interval_hours')
    op.drop_column('user_channels', 'schedule_enabled')
