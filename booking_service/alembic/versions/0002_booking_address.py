"""add booking address fields

Revision ID: 0002_booking_address
Revises: 0001_init
Create Date: 2026-03-25

"""

from alembic import op
import sqlalchemy as sa


revision = "0002_booking_address"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("booking", sa.Column("address_country", sa.String(length=128), nullable=True))
    op.add_column("booking", sa.Column("address_city", sa.String(length=128), nullable=True))
    op.add_column("booking", sa.Column("address_street", sa.String(length=256), nullable=True))
    op.add_column("booking", sa.Column("address_house", sa.String(length=64), nullable=True))
    op.add_column("booking", sa.Column("address_apartment", sa.String(length=64), nullable=True))
    op.add_column("booking", sa.Column("meeting_latitude", sa.Float(), nullable=True))
    op.add_column("booking", sa.Column("meeting_longitude", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("booking", "meeting_longitude")
    op.drop_column("booking", "meeting_latitude")
    op.drop_column("booking", "address_apartment")
    op.drop_column("booking", "address_house")
    op.drop_column("booking", "address_street")
    op.drop_column("booking", "address_city")
    op.drop_column("booking", "address_country")

