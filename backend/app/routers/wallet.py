"""Wallet + scan + Google Wallet + P2P + payment-request endpoints.

The wallet is a virtual balance that lives next to the user's MoMo account.
Money can be moved in/out via the MTN MoMo Request-to-Pay flow, and between
SmartMoney users P2P. A QR scanner endpoint normalises whatever string the
user scans (MoMo, Stokvel invite, plain JSON, etc.) into a typed payload
the frontend can act on.
"""
from __future__ import annotations

import json
import re
import secrets
import string
import uuid
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import (
    PaymentRequest,
    PaymentRequestStatus,
    User,
    UserDirectory,
    Wallet,
    WalletTransaction,
    WalletTransactionType,
    WalletTransactionStatus,
)
from app.routers.auth import get_current_user
from app.schemas.schemas import (
    GoogleWalletEnrolRequest,
    GoogleWalletSaveResponse,
    PaymentRequestCreate,
    PaymentRequestResponse,
    ScanRequest,
    ScanResponse,
    WalletDepositRequest,
    WalletResponse,
    WalletSendRequest,
    WalletTransactionResponse,
    WalletWithdrawRequest,
)
from app.services.momo import (
    get_payment_status,
    initiate_request_to_pay,
)

router = APIRouter(prefix="/api/wallet", tags=["Wallet"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_or_create_wallet(user: User, db: AsyncSession) -> Wallet:
    result = await db.execute(select(Wallet).where(Wallet.user_id == user.id))
    wallet = result.scalar_one_or_none()
    if wallet:
        return wallet
    wallet = Wallet(user_id=user.id, balance=0.0, currency="ZAR", provider="momo")
    db.add(wallet)
    await db.commit()
    await db.refresh(wallet)
    return wallet


def _wallet_response(wallet: Wallet) -> WalletResponse:
    return WalletResponse(
        id=wallet.id,
        balance=wallet.balance,
        currency=wallet.currency,
        provider=wallet.provider,
        is_active=wallet.is_active,
        google_wallet_object_id=wallet.google_wallet_object_id,
        created_at=wallet.created_at,
        updated_at=wallet.updated_at,
    )


def _txn_response(txn: WalletTransaction) -> WalletTransactionResponse:
    return WalletTransactionResponse(
        id=txn.id,
        type=txn.type.value if hasattr(txn.type, "value") else str(txn.type),
        amount=txn.amount,
        currency=txn.currency,
        status=txn.status.value if hasattr(txn.status, "value") else str(txn.status),
        counterparty_phone=txn.counterparty_phone,
        counterparty_name=txn.counterparty_name,
        reference=txn.reference,
        note=txn.note,
        source=txn.source,
        created_at=txn.created_at,
    )


def _normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    digits = "".join(ch for ch in phone if ch.isdigit())
    if not digits:
        return None
    if digits.startswith("0"):
        digits = "27" + digits[1:]
    return digits


def _parse_scan(raw: str) -> ScanResponse:
    """Best-effort parse of a scanned QR string into a typed payload."""
    raw = (raw or "").strip()
    if not raw:
        return ScanResponse(kind="unknown", raw=raw)

    # 1) JSON payload
    if raw.startswith("{"):
        try:
            data = json.loads(raw)
            kind = data.get("kind") or data.get("type") or "unknown"
            return ScanResponse(
                kind=kind,
                amount=float(data["amount"]) if data.get("amount") is not None else None,
                phone=_normalize_phone(data.get("phone")),
                payee_name=data.get("payee_name") or data.get("name"),
                reference=data.get("reference") or data.get("ref") or data.get("id"),
                note=data.get("note"),
                raw=raw,
            )
        except (ValueError, KeyError, TypeError):
            pass

    # 1b) Plain payment-request id (e.g. "pr_abc123" pasted from a share link)
    if re.fullmatch(r"[A-Za-z0-9_\-]{6,64}", raw):
        return ScanResponse(kind="momo_pay", reference=raw, raw=raw)

    # 2) URL with query params (e.g. momo://pay?amount=10&phone=...&ref=...)
    parsed = urlparse(raw)
    if parsed.scheme in {"momo", "momosmartmoney", "smartmoney", "stokvel", "payment_request", "smartmoney-wallet"}:
        qs = parse_qs(parsed.query)
        if parsed.scheme == "stokvel":
            kind = "stokvel_invite"
        elif parsed.scheme in {"payment_request", "smartmoney-wallet"}:
            kind = "momo_pay"
        elif parsed.scheme in {"smartmoney", "momosmartmoney"}:
            kind = "momo_pay"
        else:
            kind = "momo_pay"
        amount = qs.get("amount", [None])[0]
        phone = _normalize_phone(qs.get("phone", [None])[0])
        return ScanResponse(
            kind=kind,
            amount=float(amount) if amount else None,
            phone=phone,
            payee_name=qs.get("payee", qs.get("name", [None]))[0],
            reference=qs.get("ref", qs.get("reference", [None]))[0] or parsed.path.lstrip("/") or None,
            note=qs.get("note", [None])[0],
            raw=raw,
        )

    # 3) Plain text — try to detect phone + amount
    phone_match = re.search(r"(\+?\d[\d\s\-]{7,}\d)", raw)
    amount_match = re.search(r"(?:R|ZAR|MT)\s*([0-9]+(?:\.[0-9]{1,2})?)", raw, re.IGNORECASE)
    if phone_match or amount_match:
        return ScanResponse(
            kind="momo_request",
            amount=float(amount_match.group(1)) if amount_match else None,
            phone=_normalize_phone(phone_match.group(1)) if phone_match else None,
            note=raw,
            raw=raw,
        )

    return ScanResponse(kind="unknown", raw=raw)


# ---------------------------------------------------------------------------
# Wallet endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=WalletResponse)
async def get_wallet(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    wallet = await _get_or_create_wallet(user, db)
    return _wallet_response(wallet)


@router.get("/transactions", response_model=list[WalletTransactionResponse])
async def list_transactions(
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    wallet = await _get_or_create_wallet(user, db)
    result = await db.execute(
        select(WalletTransaction)
        .where(WalletTransaction.wallet_id == wallet.id)
        .order_by(WalletTransaction.created_at.desc())
        .limit(max(1, min(limit, 100)))
    )
    return [_txn_response(t) for t in result.scalars().all()]


@router.post("/deposit", response_model=WalletTransactionResponse)
async def deposit(
    payload: WalletDepositRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    phone = _normalize_phone(payload.phone or user.phone_number)
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number is required for MoMo deposits")

    wallet = await _get_or_create_wallet(user, db)
    reference = await initiate_request_to_pay(
        amount=payload.amount, phone=phone, note=payload.note or "Wallet top-up"
    )
    txn = WalletTransaction(
        wallet_id=wallet.id,
        type=WalletTransactionType.DEPOSIT,
        amount=payload.amount,
        currency=wallet.currency,
        status=WalletTransactionStatus.PENDING,
        counterparty_phone=phone,
        note=payload.note,
        reference=reference,
        source="momo",
    )
    db.add(txn)
    await db.commit()
    await db.refresh(txn)
    return _txn_response(txn)


@router.post("/withdraw", response_model=WalletTransactionResponse)
async def withdraw(
    payload: WalletWithdrawRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    wallet = await _get_or_create_wallet(user, db)
    if wallet.balance < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient wallet balance")
    phone = _normalize_phone(payload.phone or user.phone_number)
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number is required for MoMo withdrawals")

    reference = await initiate_request_to_pay(
        amount=payload.amount, phone=phone, note=payload.note or "Wallet withdrawal"
    )
    txn = WalletTransaction(
        wallet_id=wallet.id,
        type=WalletTransactionType.WITHDRAWAL,
        amount=payload.amount,
        currency=wallet.currency,
        status=WalletTransactionStatus.PENDING,
        counterparty_phone=phone,
        note=payload.note,
        reference=reference,
        source="momo",
    )
    db.add(txn)
    wallet.balance -= payload.amount
    await db.commit()
    await db.refresh(txn)
    return _txn_response(txn)


@router.post("/transactions/{txn_id}/sync", response_model=WalletTransactionResponse)
async def sync_transaction(
    txn_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Poll MoMo and, if the payment is SUCCESSFUL, update the wallet balance."""
    result = await db.execute(
        select(WalletTransaction).where(WalletTransaction.id == txn_id)
    )
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    wallet = await _get_or_create_wallet(user, db)
    if wallet.id != txn.wallet_id:
        raise HTTPException(status_code=403, detail="Not your transaction")

    if txn.status == WalletTransactionStatus.SUCCESSFUL:
        return _txn_response(txn)
    if not txn.reference:
        raise HTTPException(status_code=400, detail="Transaction has no reference to poll")

    status_payload = await get_payment_status(txn.reference)
    status_str = (status_payload.get("status") or "").upper()
    if status_str == "SUCCESSFUL":
        txn.status = WalletTransactionStatus.SUCCESSFUL
        if txn.type == WalletTransactionType.DEPOSIT:
            wallet.balance += txn.amount
        await db.commit()
        await db.refresh(txn)
    elif status_str in {"FAILED", "REJECTED", "EXPIRED"}:
        txn.status = WalletTransactionStatus.FAILED
        if txn.type == WalletTransactionType.WITHDRAWAL:
            # refund the balance hold
            wallet.balance += txn.amount
        await db.commit()
        await db.refresh(txn)
    return _txn_response(txn)


# ---------------------------------------------------------------------------
# Scan endpoint
# ---------------------------------------------------------------------------

@router.post("/scan", response_model=ScanResponse)
async def scan(
    payload: ScanRequest,
    user: User = Depends(get_current_user),
):
    return _parse_scan(payload.raw)


# ---------------------------------------------------------------------------
# Google Wallet (save URL)
# ---------------------------------------------------------------------------

@router.post("/google-wallet/enrol", response_model=GoogleWalletSaveResponse)
async def enrol_google_wallet(
    payload: GoogleWalletEnrolRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a Google Wallet "save" URL for the user's SmartMoney MoMo card.

    In production this would mint a signed JWT against the Google Wallet API
    (issuer + class + object). Until real Google Wallet credentials are wired
    in, we generate a deterministic but unique object id and return a
    well-formed save URL that the frontend can deep-link to.
    """
    wallet = await _get_or_create_wallet(user, db)
    issuer_id = "33880000000223000001"  # placeholder issuer; replace with real id
    class_id = f"{issuer_id}.smartmoney_momo_class"
    object_id = f"{issuer_id}.{wallet.id.replace('-', '')[:18]}"
    wallet.google_wallet_object_id = object_id
    await db.commit()

    save_url = (
        f"https://pay.google.com/gp/v/save/"
        f"?token={class_id}.{object_id}"
    )
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    return GoogleWalletSaveResponse(
        save_url=save_url,
        class_id=class_id,
        object_id=object_id,
        expires_at=expires_at,
    )


# Convenience health route
@router.get("/ping")
async def ping():
    return {"ok": True, "service": "wallet", "ts": datetime.utcnow().isoformat()}


# ---------------------------------------------------------------------------
# P2P send / request
# ---------------------------------------------------------------------------

async def _ensure_directory(user: User, db: AsyncSession) -> None:
    phone = _normalize_phone(user.phone_number)
    if not phone:
        return
    result = await db.execute(select(UserDirectory).where(UserDirectory.phone_number == phone))
    entry = result.scalar_one_or_none()
    if entry is None:
        entry = UserDirectory(phone_number=phone, user_id=user.id, display_name=user.name)
        db.add(entry)
    else:
        entry.display_name = user.name
        entry.last_seen_at = datetime.utcnow()


def _short_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _payment_request_response(pr: PaymentRequest) -> PaymentRequestResponse:
    return PaymentRequestResponse(
        id=pr.id,
        amount=pr.amount,
        currency=pr.currency,
        payee_name=pr.payee_name,
        payee_phone=pr.payee_phone,
        note=pr.note,
        status=pr.status.value if hasattr(pr.status, "value") else str(pr.status),
        code=pr.code,
        qr_payload=pr.code,
        expires_at=pr.expires_at,
        created_at=pr.created_at,
    )


@router.post("/send", response_model=WalletTransactionResponse)
async def send_money(
    payload: WalletSendRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send money from the caller's wallet to another SmartMoney user (P2P).

    The recipient must already have a SmartMoney account. The transfer is
    internal: it moves funds between two SmartMoney wallets in one DB
    transaction. (For a real disbursement via MoMo, use POST /api/wallet/withdraw
    first, then the user's app initiates a deposit to the recipient.)
    """
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    recipient_phone = _normalize_phone(payload.recipient_phone)
    if not recipient_phone:
        raise HTTPException(status_code=400, detail="Recipient phone is required")

    # Find recipient by phone
    result = await db.execute(
        select(UserDirectory).where(UserDirectory.phone_number == recipient_phone)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(
            status_code=404,
            detail=(
                "Recipient is not a SmartMoney user yet. Ask them to register, "
                "or use Withdraw to send to their MoMo directly."
            ),
        )

    if entry.user_id == user.id:
        raise HTTPException(status_code=400, detail="You can't send to yourself")

    # Lock both wallets
    sender = await _get_or_create_wallet(user, db)
    if sender.balance < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient wallet balance")

    result = await db.execute(select(Wallet).where(Wallet.user_id == entry.user_id))
    recipient_wallet = result.scalar_one_or_none()
    if recipient_wallet is None:
        # Create a wallet for the recipient on the fly
        recipient_wallet = Wallet(user_id=entry.user_id, balance=0.0)
        db.add(recipient_wallet)
        await db.flush()

    ref = str(uuid.uuid4())
    sender.balance -= payload.amount
    recipient_wallet.balance += payload.amount

    out_txn = WalletTransaction(
        wallet_id=sender.id,
        type=WalletTransactionType.TRANSFER_OUT,
        amount=payload.amount,
        currency=sender.currency,
        status=WalletTransactionStatus.SUCCESSFUL,
        counterparty_phone=recipient_phone,
        counterparty_name=entry.display_name,
        note=payload.note,
        reference=ref,
        source="p2p",
    )
    in_txn = WalletTransaction(
        wallet_id=recipient_wallet.id,
        type=WalletTransactionType.TRANSFER_IN,
        amount=payload.amount,
        currency=recipient_wallet.currency,
        status=WalletTransactionStatus.SUCCESSFUL,
        counterparty_phone=_normalize_phone(user.phone_number),
        counterparty_name=user.name,
        note=payload.note,
        reference=ref,
        source="p2p",
    )
    db.add_all([out_txn, in_txn])
    await _ensure_directory(user, db)
    await db.commit()
    await db.refresh(out_txn)
    return _txn_response(out_txn)


@router.post("/request", response_model=PaymentRequestResponse)
async def create_payment_request(
    payload: PaymentRequestCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a 'pay me' QR code others can scan to send you money."""
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    code = _short_code(8)
    expires_at = (
        datetime.utcnow() + timedelta(minutes=payload.ttl_minutes or 60)
        if (payload.ttl_minutes or 0) > 0
        else None
    )
    pr = PaymentRequest(
        requester_id=user.id,
        amount=payload.amount,
        currency="ZAR",
        payee_name=payload.payee_name or user.name,
        payee_phone=_normalize_phone(payload.payee_phone or user.phone_number),
        note=payload.note,
        status=PaymentRequestStatus.OPEN,
        expires_at=expires_at,
        code=code,
    )
    db.add(pr)
    await _ensure_directory(user, db)
    await db.commit()
    await db.refresh(pr)
    return _payment_request_response(pr)


@router.get("/request/me", response_model=list[PaymentRequestResponse])
async def list_my_payment_requests(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PaymentRequest)
        .where(PaymentRequest.requester_id == user.id)
        .order_by(PaymentRequest.created_at.desc())
        .limit(50)
    )
    return [_payment_request_response(p) for p in result.scalars().all()]


@router.get("/request/{code}", response_model=PaymentRequestResponse)
async def get_payment_request(
    code: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PaymentRequest).where(PaymentRequest.code == code))
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Payment request not found")
    if pr.expires_at and pr.expires_at < datetime.utcnow() and pr.status == PaymentRequestStatus.OPEN:
        pr.status = PaymentRequestStatus.EXPIRED
        await db.commit()
    return _payment_request_response(pr)


@router.post("/request/{code}/pay", response_model=WalletTransactionResponse)
async def pay_payment_request(
    code: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pay an open payment-request by sending from caller's wallet to the requester."""
    result = await db.execute(select(PaymentRequest).where(PaymentRequest.code == code))
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Payment request not found")
    if pr.status != PaymentRequestStatus.OPEN:
        raise HTTPException(status_code=400, detail=f"Payment request is {pr.status}")
    if pr.expires_at and pr.expires_at < datetime.utcnow():
        pr.status = PaymentRequestStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=400, detail="Payment request has expired")
    if pr.requester_id == user.id:
        raise HTTPException(status_code=400, detail="You can't pay your own request")

    requester = await db.execute(select(User).where(User.id == pr.requester_id))
    requester_user = requester.scalar_one()

    sender = await _get_or_create_wallet(user, db)
    if sender.balance < pr.amount:
        raise HTTPException(
            status_code=400,
            detail="Insufficient wallet balance. Top up first or decline.",
        )

    requester_wallet_res = await db.execute(
        select(Wallet).where(Wallet.user_id == pr.requester_id)
    )
    requester_wallet = requester_wallet_res.scalar_one_or_none()
    if requester_wallet is None:
        requester_wallet = Wallet(user_id=pr.requester_id, balance=0.0)
        db.add(requester_wallet)
        await db.flush()

    ref = str(uuid.uuid4())
    sender.balance -= pr.amount
    requester_wallet.balance += pr.amount

    out_txn = WalletTransaction(
        wallet_id=sender.id,
        type=WalletTransactionType.TRANSFER_OUT,
        amount=pr.amount,
        currency=sender.currency,
        status=WalletTransactionStatus.SUCCESSFUL,
        counterparty_phone=_normalize_phone(requester_user.phone_number),
        counterparty_name=requester_user.name,
        note=pr.note or f"Payment for {pr.code}",
        reference=ref,
        source="request",
    )
    in_txn = WalletTransaction(
        wallet_id=requester_wallet.id,
        type=WalletTransactionType.TRANSFER_IN,
        amount=pr.amount,
        currency=requester_wallet.currency,
        status=WalletTransactionStatus.SUCCESSFUL,
        counterparty_phone=_normalize_phone(user.phone_number),
        counterparty_name=user.name,
        note=pr.note or f"Payment for {pr.code}",
        reference=ref,
        source="request",
    )
    pr.status = PaymentRequestStatus.PAID
    pr.paid_by_id = user.id
    db.add_all([out_txn, in_txn])
    await db.commit()
    await db.refresh(out_txn)
    return _txn_response(out_txn)