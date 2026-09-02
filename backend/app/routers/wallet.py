"""Wallet + scan + Google Wallet endpoints.

The wallet is a virtual balance that lives next to the user's MoMo account.
Money can be moved in/out via the MTN MoMo Request-to-Pay flow. A QR
scanner endpoint normalises whatever string the user scans (MoMo, Stokvel
invite, plain JSON, etc.) into a typed payload the frontend can act on.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import (
    User,
    Wallet,
    WalletTransaction,
    WalletTransactionType,
    WalletTransactionStatus,
)
from app.routers.auth import get_current_user
from app.schemas.schemas import (
    GoogleWalletEnrolRequest,
    GoogleWalletSaveResponse,
    ScanRequest,
    ScanResponse,
    WalletDepositRequest,
    WalletResponse,
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
                reference=data.get("reference") or data.get("ref"),
                note=data.get("note"),
                raw=raw,
            )
        except (ValueError, KeyError, TypeError):
            pass

    # 2) URL with query params (e.g. momo://pay?amount=10&phone=...&ref=...)
    parsed = urlparse(raw)
    if parsed.scheme in {"momo", "momosmartmoney", "smartmoney", "stokvel"}:
        qs = parse_qs(parsed.query)
        kind = "momo_pay" if parsed.scheme == "momo" else parsed.scheme
        if parsed.scheme == "stokvel":
            kind = "stokvel_invite"
        amount = qs.get("amount", [None])[0]
        phone = _normalize_phone(qs.get("phone", [None])[0])
        return ScanResponse(
            kind=kind,
            amount=float(amount) if amount else None,
            phone=phone,
            payee_name=qs.get("payee", qs.get("name", [None]))[0],
            reference=qs.get("ref", qs.get("reference", [None]))[0],
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