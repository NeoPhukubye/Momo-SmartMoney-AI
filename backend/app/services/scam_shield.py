from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.schemas.schemas import TransactionCreate
from app.models.models import User, Transaction, ScamReport, RiskLevel

# Known scam patterns
SCAM_KEYWORDS = [
    "prize", "winner", "claim", "urgent", "verify account",
    "sim swap", "confirm pin", "mtn agent", "reversal",
    "send back", "wrong transfer", "refund fee",
]

HIGH_RISK_AMOUNT_THRESHOLD = 5000  # ZAR


async def analyze_transaction_risk(
    txn: TransactionCreate, user: User, db: AsyncSession
) -> tuple[str, str | None]:
    reasons = []
    risk_score = 0

    # Check 1: Known scam phone numbers
    if txn.counterparty_phone:
        result = await db.execute(
            select(func.count(ScamReport.id))
            .where(ScamReport.suspect_phone == txn.counterparty_phone)
        )
        report_count = result.scalar() or 0
        if report_count >= 3:
            risk_score += 40
            reasons.append(f"This number has been reported {report_count} times for fraud")
        elif report_count >= 1:
            risk_score += 20
            reasons.append("This number has been reported before")

    # Check 2: Scam keywords in description
    description = (txn.description or "").lower()
    for keyword in SCAM_KEYWORDS:
        if keyword in description:
            risk_score += 30
            reasons.append(f"Message contains suspicious language: '{keyword}'")
            break

    # Check 3: Unusually large amount
    if txn.direction == "out" and txn.amount >= HIGH_RISK_AMOUNT_THRESHOLD:
        # Check average transaction for this user
        result = await db.execute(
            select(func.avg(Transaction.amount))
            .where(Transaction.user_id == user.id, Transaction.direction == "out")
        )
        avg_amount = result.scalar() or 0
        if avg_amount > 0 and txn.amount > avg_amount * 5:
            risk_score += 25
            reasons.append(f"Amount is {txn.amount/avg_amount:.0f}x your average transfer")

    # Check 4: Rapid transactions (velocity check)
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    result = await db.execute(
        select(func.count(Transaction.id))
        .where(
            Transaction.user_id == user.id,
            Transaction.direction == "out",
            Transaction.timestamp >= one_hour_ago,
        )
    )
    recent_count = result.scalar() or 0
    if recent_count >= 5:
        risk_score += 20
        reasons.append(f"You've made {recent_count} outgoing transfers in the last hour")

    # Check 5: New/unknown recipient with large amount
    if txn.counterparty_phone and txn.direction == "out" and txn.amount >= 1000:
        result = await db.execute(
            select(func.count(Transaction.id))
            .where(
                Transaction.user_id == user.id,
                Transaction.counterparty_phone == txn.counterparty_phone,
            )
        )
        past_txns = result.scalar() or 0
        if past_txns == 0:
            risk_score += 15
            reasons.append("First time sending to this number — and it's a large amount")

    # Determine risk level
    if risk_score >= 60:
        return RiskLevel.CRITICAL, "; ".join(reasons)
    elif risk_score >= 40:
        return RiskLevel.HIGH, "; ".join(reasons)
    elif risk_score >= 20:
        return RiskLevel.MEDIUM, "; ".join(reasons)
    else:
        return RiskLevel.LOW, None
