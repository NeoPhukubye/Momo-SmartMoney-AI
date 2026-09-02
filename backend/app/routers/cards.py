from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/api/cards", tags=["Cards & Digital Wallets"])


class ProvisionRequest(BaseModel):
    card_id: str
    target_wallet: str
    device_id: str


class TapAuthorizeRequest(BaseModel):
    user_id: str
    merchant_name: str
    merchant_id: str
    amount: float
    channel: str = "APPLE_PAY_NFC"


class ApplePaySessionRequest(BaseModel):
    validationURL: str


apple_pay_router = APIRouter(prefix="/api/apple-pay", tags=["Apple Pay Web"])


@apple_pay_router.post("/validate-session")
async def validate_apple_pay_session(payload: ApplePaySessionRequest):
    return {
        "merchantSessionIdentifier": f"ms_{uuid.uuid4().hex}",
        "nonce": uuid.uuid4().hex,
        "merchantIdentifier": "merchant.com.momo.smartmoney",
        "domainName": "smartmoney-app.onrender.com",
        "displayName": "MoMo SmartMoney AI",
        "signature": "simulated_apple_pay_merchant_session_signature",
        "operationalAnalyticsIdentifier": f"oa_{uuid.uuid4().hex[:10]}",
        "retries": 0,
        "timestamp": 0,
    }


@router.post("/wallet/provision")
async def provision_to_wallet(payload: ProvisionRequest):
    if payload.target_wallet not in ("APPLE_PAY", "GOOGLE_PAY"):
        raise HTTPException(status_code=400, detail="Unsupported digital wallet")

    if payload.target_wallet == "APPLE_PAY":
        return {
            "status": "READY_FOR_WALLET",
            "targetWallet": "APPLE_PAY",
            "cardId": payload.card_id,
            "tokenRequestorId": "40000000001",
            "activationData": "dGVzdF9hY3RpdmF0aW9uX2Jsb2I=",
            "encryptedPassData": {
                "version": "EV_ECC_V2",
                "ephemeralPublicKey": "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...",
                "data": "k83hjs82hd8sjd092jssdf...",
            },
        }

    return {
        "status": "READY_FOR_WALLET",
        "targetWallet": "GOOGLE_PAY",
        "cardId": payload.card_id,
        "tokenRequestorId": "40000000002",
        "opaquePaymentCard": f"mdes_jwe_token_{uuid.uuid4().hex[:12]}",
        "tsp": "MASTERCARD_MDES",
    }


@router.post("/tap/authorize")
async def authorize_nfc_tap(payload: TapAuthorizeRequest):
    flagged_merchants = ["FAKE_AGENT_789", "SUSPICIOUS_TERMINAL_01"]

    if payload.merchant_id in flagged_merchants or payload.amount > 5000:
        return {
            "decision": "DECLINED",
            "flagged": True,
            "risk_score": 88,
            "reason": "Scam Shield: High-risk merchant velocity detected on POS terminal.",
        }

    return {
        "decision": "APPROVED",
        "flagged": False,
        "auth_code": f"APPR-{uuid.uuid4().hex[:6].upper()}",
        "channel": payload.channel,
        "amount_deducted": payload.amount,
        "currency": "ZAR",
    }
