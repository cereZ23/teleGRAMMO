"""Add keyword alerts tables.

Revision ID: 003_keyword_alerts
Revises: 001
Create Date: 2024-12-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "003_keyword_alerts"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create keyword_alerts table
    op.create_table(
        "keyword_alerts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel_id", UUID(as_uuid=True), sa.ForeignKey("channels.id", ondelete="CASCADE"), nullable=True),
        sa.Column("keyword", sa.String(255), nullable=False),
        sa.Column("is_regex", sa.Boolean(), default=False, nullable=False),
        sa.Column("is_case_sensitive", sa.Boolean(), default=False, nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("notify_email", sa.Boolean(), default=False, nullable=False),
        sa.Column("notify_webhook", sa.String(500), nullable=True),
        sa.Column("match_count", sa.Integer(), default=0, nullable=False),
        sa.Column("last_match_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes for keyword_alerts
    op.create_index("idx_keyword_user", "keyword_alerts", ["user_id"])
    op.create_index("idx_keyword_active", "keyword_alerts", ["is_active"])

    # Create keyword_matches table
    op.create_table(
        "keyword_matches",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("keyword_alert_id", UUID(as_uuid=True), sa.ForeignKey("keyword_alerts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message_id", UUID(as_uuid=True), sa.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel_id", UUID(as_uuid=True), sa.ForeignKey("channels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("matched_text", sa.Text(), nullable=True),
        sa.Column("is_read", sa.Boolean(), default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # Create indexes for keyword_matches
    op.create_index("idx_match_alert", "keyword_matches", ["keyword_alert_id"])
    op.create_index("idx_match_message", "keyword_matches", ["message_id"])
    op.create_index("idx_match_created", "keyword_matches", ["created_at"])


def downgrade() -> None:
    # Drop keyword_matches indexes
    op.drop_index("idx_match_created")
    op.drop_index("idx_match_message")
    op.drop_index("idx_match_alert")

    # Drop keyword_matches table
    op.drop_table("keyword_matches")

    # Drop keyword_alerts indexes
    op.drop_index("idx_keyword_active")
    op.drop_index("idx_keyword_user")

    # Drop keyword_alerts table
    op.drop_table("keyword_alerts")
