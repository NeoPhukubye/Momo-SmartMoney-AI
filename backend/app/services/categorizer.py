from app.schemas.schemas import TransactionCreate
from app.models.models import TransactionCategory


def categorize_transaction(txn: TransactionCreate) -> TransactionCategory:
    description = (txn.description or "").lower()
    counterparty = (txn.counterparty_name or "").lower()

    if any(kw in description for kw in ["airtime", "data", "bundle", "recharge"]):
        return TransactionCategory.AIRTIME
    if any(kw in description for kw in ["electricity", "water", "dstv", "bill", "rent"]):
        return TransactionCategory.BILL_PAYMENT
    if any(kw in description for kw in ["shop", "store", "pay", "merchant", "till"]):
        return TransactionCategory.MERCHANT
    if any(kw in description for kw in ["save", "savings", "goal"]):
        return TransactionCategory.SAVINGS
    if any(kw in description for kw in ["stokvel", "group", "contribution"]):
        return TransactionCategory.STOKVEL
    if any(kw in description for kw in ["withdraw", "atm", "cash out"]):
        return TransactionCategory.WITHDRAWAL
    if txn.direction == "in":
        return TransactionCategory.DEPOSIT
    if txn.direction == "out" and txn.counterparty_phone:
        return TransactionCategory.TRANSFER

    return TransactionCategory.OTHER
