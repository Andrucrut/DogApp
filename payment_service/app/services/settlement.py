from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import (
    BookingWalletSettlement,
    LedgerEntryKind,
    Wallet,
    WalletLedger,
)
from app.services.booking_client import fetch_payment_context


async def _get_wallet_for_update(db: AsyncSession, user_id: UUID) -> Wallet:
    result = await db.execute(
        select(Wallet).where(Wallet.user_id == user_id).with_for_update()
    )
    w = result.scalar_one_or_none()
    if w:
        return w
    w = Wallet(user_id=user_id, balance=Decimal("0.00"))
    db.add(w)
    await db.flush()
    result = await db.execute(
        select(Wallet).where(Wallet.user_id == user_id).with_for_update()
    )
    return result.scalar_one()


async def settle_booking_wallet(db: AsyncSession, booking_id: UUID) -> tuple[bool, str | None, dict]:
    """
    Idempotent settlement: debits owner, credits walker.
    Returns (ok, error_code, meta). error_code None on success.
    """
    ctx = await fetch_payment_context(booking_id)
    if not ctx:
        return False, "booking_unavailable", {}
    if ctx.status != "AWAITING_OWNER_PAYMENT":
        return False, "invalid_booking_status", {"status": ctx.status}
    if not ctx.walker_user_id:
        return False, "no_walker", {}
    price = ctx.price
    if price <= 0:
        return False, "invalid_price", {}

    owner_id = ctx.owner_id
    walker_uid = ctx.walker_user_id

    uids_sorted = sorted([owner_id, walker_uid], key=lambda u: str(u))
    await _get_wallet_for_update(db, uids_sorted[0])
    await _get_wallet_for_update(db, uids_sorted[1])

    existing = await db.execute(
        select(BookingWalletSettlement).where(BookingWalletSettlement.booking_id == booking_id)
    )
    if existing.scalar_one_or_none():
        await db.commit()
        return True, None, {"already_settled": True}

    owner_w = (
        await db.execute(select(Wallet).where(Wallet.user_id == owner_id))
    ).scalar_one()
    walker_w = (
        await db.execute(select(Wallet).where(Wallet.user_id == walker_uid))
    ).scalar_one()

    if owner_w.balance < price:
        await db.rollback()
        return False, "insufficient_balance", {}

    owner_w.balance = owner_w.balance - price
    walker_w.balance = walker_w.balance + price

    db.add(
        BookingWalletSettlement(
            booking_id=booking_id,
            owner_id=owner_id,
            walker_user_id=walker_uid,
            amount=price,
            currency=ctx.currency,
        )
    )
    db.add(
        WalletLedger(
            user_id=owner_id,
            kind=LedgerEntryKind.OWNER_BOOKING_DEBIT,
            amount=price,
            booking_id=booking_id,
            withdrawal_id=None,
        )
    )
    db.add(
        WalletLedger(
            user_id=walker_uid,
            kind=LedgerEntryKind.WALKER_BOOKING_CREDIT,
            amount=price,
            booking_id=booking_id,
            withdrawal_id=None,
        )
    )
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return True, None, {"already_settled": True}

    return True, None, {"already_settled": False}
