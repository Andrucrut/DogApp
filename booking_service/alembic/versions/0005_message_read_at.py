"""add message.read_at

Revision ID: 0005_message_read_at
Revises: 0004_applications_chat
Create Date: 2026-04-04

"""

from alembic import op
import sqlalchemy as sa


revision = "0005_message_read_at"
down_revision = "0004_applications_chat"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("message", sa.Column("read_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_message_conversation_id_id", "message", ["conversation_id", "id"])


def downgrade() -> None:
    op.drop_index("ix_message_conversation_id_id", table_name="message")
    op.drop_column("message", "read_at")
