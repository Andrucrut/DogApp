"""add AWAITING_OWNER_PAYMENT to booking_status

Revision ID: 0006_awaiting_owner_payment
Revises: 0005_message_read_at
Create Date: 2026-04-07

"""

from alembic import op

revision = "0006_awaiting_owner_payment"
down_revision = "0005_message_read_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE booking_status ADD VALUE IF NOT EXISTS 'AWAITING_OWNER_PAYMENT'")


def downgrade() -> None:
    pass
