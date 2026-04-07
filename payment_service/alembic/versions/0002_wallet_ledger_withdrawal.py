"""wallet ledger withdrawal settlement

Revision ID: 0002_wallet
Revises: 0001_init
Create Date: 2026-04-07

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID

revision = "0002_wallet"
down_revision = "0001_init"
branch_labels = None
depends_on = None

# create_type=False: типы создаём явно в upgrade() (иначе create_table снова вызывает CREATE TYPE).
ledger_kind = ENUM(
    "TOPUP",
    "OWNER_BOOKING_DEBIT",
    "WALKER_BOOKING_CREDIT",
    "WITHDRAWAL_RESERVE",
    "WITHDRAWAL_REJECT_REFUND",
    name="ledger_entry_kind",
    create_type=False,
)

withdrawal_status = ENUM(
    "PENDING_MODERATION",
    "IN_PROGRESS",
    "COMPLETED",
    "REJECTED",
    name="withdrawal_status",
    create_type=False,
)


def upgrade() -> None:
    ledger_kind.create(op.get_bind(), checkfirst=True)
    withdrawal_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "wallet",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extra_fields", JSONB(), nullable=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("balance", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("currency", sa.String(8), nullable=False, server_default="RUB"),
        sa.UniqueConstraint("user_id", name="uq_wallet_user_id"),
    )
    op.create_index("ix_wallet_user_id", "wallet", ["user_id"])

    op.create_table(
        "wallet_ledger",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extra_fields", JSONB(), nullable=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("kind", ledger_kind, nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("booking_id", UUID(as_uuid=True), nullable=True),
        sa.Column("withdrawal_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_wallet_ledger_user_id", "wallet_ledger", ["user_id"])
    op.create_index("ix_wallet_ledger_booking_id", "wallet_ledger", ["booking_id"])

    op.create_table(
        "booking_wallet_settlement",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extra_fields", JSONB(), nullable=True),
        sa.Column("booking_id", UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", UUID(as_uuid=True), nullable=False),
        sa.Column("walker_user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="RUB"),
        sa.UniqueConstraint("booking_id", name="uq_booking_wallet_settlement_booking_id"),
    )

    op.create_table(
        "withdrawal_request",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extra_fields", JSONB(), nullable=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column(
            "status",
            withdrawal_status,
            nullable=False,
            server_default=sa.text("'PENDING_MODERATION'::withdrawal_status"),
        ),
        sa.Column("moderator_note", sa.Text(), nullable=True),
    )
    op.create_index("ix_withdrawal_request_user_id", "withdrawal_request", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_withdrawal_request_user_id", table_name="withdrawal_request")
    op.drop_table("withdrawal_request")
    op.drop_table("booking_wallet_settlement")
    op.drop_index("ix_wallet_ledger_booking_id", table_name="wallet_ledger")
    op.drop_index("ix_wallet_ledger_user_id", table_name="wallet_ledger")
    op.drop_table("wallet_ledger")
    op.drop_index("ix_wallet_user_id", table_name="wallet")
    op.drop_table("wallet")
    withdrawal_status.drop(op.get_bind(), checkfirst=True)
    ledger_kind.drop(op.get_bind(), checkfirst=True)
