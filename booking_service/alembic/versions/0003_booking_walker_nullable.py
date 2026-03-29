"""booking.walker_id nullable for open requests

Revision ID: 0003_booking_walker_nullable
Revises: 0002_booking_address
Create Date: 2026-03-28

"""

from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_booking_walker_nullable"
down_revision = "0002_booking_address"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "booking",
        "walker_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "booking",
        "walker_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
