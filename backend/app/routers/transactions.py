from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.database import get_db
from app.models.models import User, Transaction
from app.schemas.schemas import TransactionCreate, TransactionResponse, SpendingSummary
from app.routers.auth import get_current_user
from app.services.scam_shield import analyze_transaction_risk
from app.services.categorizer import categorize_transaction

router = APIRouter()


@router.post("/", response_model=TransactionResponse)
async def create_transaction(
    txn_data: TransactionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    category = categorize_transaction(txn_data)
    risk_level, risk_reason = await analyze_transaction_risk(txn_data, user, db)

    txn = Transaction(
        user_id=user.id,
        amount=txn_data.amount,
        currency=txn_data.currency,
        counterparty_phone=txn_data.counterparty_phone,
        counterparty_name=txn_data.counterparty_name,
        category=category,
        description=txn_data.description,
        direction=txn_data.direction,
        momo_reference=txn_data.momo_reference,
        risk_level=risk_level,
        risk_reason=risk_reason,
        is_flagged=risk_level in ("high", "critical"),
    )
    db.add(txn)
    await db.commit()
    await db.refresh(txn)

    return txn


@router.get("/", response_model=list[TransactionResponse])
async def list_transactions(
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.timestamp.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


@router.get("/summary", response_model=SpendingSummary)
async def spending_summary(
    days: int = Query(default=30, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(Transaction).where(
            Transaction.user_id == user.id,
            Transaction.timestamp >= since,
        )
    )
    transactions = result.scalars().all()

    total_income = sum(t.amount for t in transactions if t.direction == "in")
    total_expenses = sum(t.amount for t in transactions if t.direction == "out")

    by_category: dict[str, float] = {}
    for t in transactions:
        if t.direction == "out":
            cat = t.category.value if t.category else "other"
            by_category[cat] = by_category.get(cat, 0) + t.amount

    return SpendingSummary(
        total_income=total_income,
        total_expenses=total_expenses,
        net=total_income - total_expenses,
        by_category=by_category,
        period=f"last_{days}_days",
    )


@router.get("/flagged", response_model=list[TransactionResponse])
async def flagged_transactions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user.id, Transaction.is_flagged == True)
        .order_by(Transaction.timestamp.desc())
    )
    return result.scalars().all()
