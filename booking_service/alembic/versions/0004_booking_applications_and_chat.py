"""add booking applications and chat

Revision ID: 0004_applications_chat
Revises: 0003_booking_walker_nullable
Create Date: 2026-04-04

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0004_applications_chat"
down_revision = "0003_booking_walker_nullable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    application_status = postgresql.ENUM(
        "PENDING",
        "WITHDRAWN",
        "ACCEPTED",
        "REJECTED",
        name="application_status",
    )
    application_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "booking_application",
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("walker_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("walker_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "PENDING",
                "WITHDRAWN",
                "ACCEPTED",
                "REJECTED",
                name="application_status",
                create_type=False,
            ),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("extra_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["booking_id"], ["booking.id"]),
        sa.ForeignKeyConstraint(["walker_id"], ["walker.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("booking_id", "walker_id", name="uq_booking_application_booking_walker"),
    )
    op.create_index("ix_booking_application_booking_id", "booking_application", ["booking_id"])
    op.create_index("ix_booking_application_walker_id", "booking_application", ["walker_id"])
    op.create_index("ix_booking_application_status", "booking_application", ["status"])

    op.create_table(
        "conversation",
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("walker_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("extra_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["booking_id"], ["booking.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("booking_id", name="uq_conversation_booking_id"),
    )
    op.create_index("ix_conversation_owner_id", "conversation", ["owner_id"])
    op.create_index("ix_conversation_walker_user_id", "conversation", ["walker_user_id"])

    op.create_table(
        "message",
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sender_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("extra_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversation.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_message_conversation_created", "message", ["conversation_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_message_conversation_created", table_name="message")
    op.drop_table("message")
    op.drop_index("ix_conversation_walker_user_id", table_name="conversation")
    op.drop_index("ix_conversation_owner_id", table_name="conversation")
    op.drop_table("conversation")
    op.drop_index("ix_booking_application_status", table_name="booking_application")
    op.drop_index("ix_booking_application_walker_id", table_name="booking_application")
    op.drop_index("ix_booking_application_booking_id", table_name="booking_application")
    op.drop_table("booking_application")
    sa.Enum(name="application_status").drop(op.get_bind(), checkfirst=True)
