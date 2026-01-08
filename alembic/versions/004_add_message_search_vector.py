"""Add full-text search vector and index on messages.

Revision ID: 004_full_text_search
Revises: 003_keyword_alerts
Create Date: 2026-01-08
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "004_full_text_search"
down_revision: Union[str, None] = "003_keyword_alerts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create generated tsvector column combining text fields
    op.execute(
        """
        ALTER TABLE messages
        ADD COLUMN IF NOT EXISTS search_vector tsvector
        GENERATED ALWAYS AS (
          to_tsvector(
            'simple',
            coalesce(message_text,'') || ' ' ||
            coalesce(username,'') || ' ' ||
            coalesce(first_name,'') || ' ' ||
            coalesce(last_name,'') || ' ' ||
            coalesce(post_author,'')
          )
        ) STORED
        """
    )

    # GIN index for fast full-text search
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_messages_search_vector
        ON messages USING GIN (search_vector)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_messages_search_vector")
    op.execute("ALTER TABLE messages DROP COLUMN IF EXISTS search_vector")

