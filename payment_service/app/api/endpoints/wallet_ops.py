from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id, require_walker_role
from app.db.session import get_db
from app.db_crud.wallet_crud import crud_wallet, crud_withdrawal
from app.models.wallet import LedgerEntryKind, Wallet, WalletLedger, WithdrawalRequest, WithdrawalStatus
from app.schemas.wallet import (
    WalletRead,
    WalletTopUpBody,
    WithdrawalCreate,
    WithdrawalRead,
)

router = APIRouter(prefix="/wallets", tags=["wallets"])
withdrawals_router = APIRouter(prefix="/withdrawals", tags=["withdrawals"])


@router.get("/me", response_model=WalletRead)
async def get_my_wallet(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> WalletRead:
    w = await crud_wallet.ensure_wallet(db, user_id)
    await db.commit()
    return WalletRead(user_id=w.user_id, balance=float(w.balance), currency=w.currency)


@router.post("/topup", response_model=WalletRead)
async def topup_wallet(
    body: WalletTopUpBody,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> WalletRead:
    result = await db.execute(
        select(Wallet).where(Wallet.user_id == user_id).with_for_update()
    )
    w = result.scalar_one_or_none()
    if not w:
        w = Wallet(user_id=user_id, balance=Decimal("0.00"))
        db.add(w)
        await db.flush()
        result = await db.execute(
            select(Wallet).where(Wallet.user_id == user_id).with_for_update()
        )
        w = result.scalar_one()
    w.balance = w.balance + body.amount
    db.add(
        WalletLedger(
            user_id=user_id,
            kind=LedgerEntryKind.TOPUP,
            amount=body.amount,
            booking_id=None,
            withdrawal_id=None,
        )
    )
    await db.commit()
    await db.refresh(w)
    return WalletRead(user_id=w.user_id, balance=float(w.balance), currency=w.currency)


@withdrawals_router.post("/", response_model=WithdrawalRead, status_code=status.HTTP_201_CREATED)
async def create_withdrawal(
    body: WithdrawalCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_walker_role),
) -> WithdrawalRead:
    result = await db.execute(
        select(Wallet).where(Wallet.user_id == user_id).with_for_update()
    )
    w = result.scalar_one_or_none()
    if not w:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="wallet_empty",
        )
    if w.balance < body.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="insufficient_balance",
        )
    w.balance = w.balance - body.amount
    req = WithdrawalRequest(
        user_id=user_id,
        amount=body.amount,
        status=WithdrawalStatus.PENDING_MODERATION,
        moderator_note=None,
    )
    db.add(req)
    await db.flush()
    await db.refresh(req)
    db.add(
        WalletLedger(
            user_id=user_id,
            kind=LedgerEntryKind.WITHDRAWAL_RESERVE,
            amount=body.amount,
            booking_id=None,
            withdrawal_id=req.id,
        )
    )
    await db.commit()
    await db.refresh(req)
    return WithdrawalRead(
        id=req.id,
        user_id=req.user_id,
        amount=float(req.amount),
        status=req.status,
        moderator_note=req.moderator_note,
        created_at=req.created_at,
    )


@withdrawals_router.get("/me", response_model=list[WithdrawalRead])
async def list_my_withdrawals(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_walker_role),
    limit: int = 50,
    offset: int = 0,
) -> list[WithdrawalRead]:
    rows = await crud_withdrawal.list_for_user(db, user_id, limit=limit, offset=offset)
    return [
        WithdrawalRead(
            id=r.id,
            user_id=r.user_id,
            amount=float(r.amount),
            status=r.status,
            moderator_note=r.moderator_note,
            created_at=r.created_at,
        )
        for r in rows
    ]
