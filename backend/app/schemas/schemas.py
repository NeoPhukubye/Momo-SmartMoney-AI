from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    phone_number: str
    name: str
    pin: str
    language: str = "en"


class UserLogin(BaseModel):
    phone_number: str
    pin: str


class UserResponse(BaseModel):
    id: str
    phone_number: str
    name: str
    language: str
    created_at: datetime
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    auth_provider: Optional[str] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TransactionCreate(BaseModel):
    amount: float
    currency: str = "ZAR"
    counterparty_phone: Optional[str] = None
    counterparty_name: Optional[str] = None
    description: Optional[str] = None
    direction: str
    momo_reference: Optional[str] = None


class TransactionResponse(BaseModel):
    id: str
    amount: float
    currency: str
    counterparty_phone: Optional[str]
    counterparty_name: Optional[str]
    category: str
    description: Optional[str]
    direction: str
    timestamp: datetime
    risk_level: str
    risk_reason: Optional[str]
    is_flagged: bool

    class Config:
        from_attributes = True


class StokvelCreate(BaseModel):
    name: str
    description: Optional[str] = None
    contribution_amount: float
    frequency: str = "monthly"


class StokvelResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    contribution_amount: float
    frequency: str
    next_contribution_date: Optional[datetime]
    next_payout_date: Optional[datetime]
    member_count: int = 0
    mtn_member_count: int = 0
    has_mtn_member: bool = False
    is_active: bool

    class Config:
        from_attributes = True


class GoogleAuthRequest(BaseModel):
    """Credential returned by Google Identity Services on the client."""
    credential: str  # the ID token (JWT)
    phone_number: Optional[str] = None  # required for new MTN-gated users
    name: Optional[str] = None


class WalletSendRequest(BaseModel):
    amount: float
    recipient_phone: str
    note: Optional[str] = "SmartMoney P2P transfer"


class PaymentRequestCreate(BaseModel):
    amount: float
    note: Optional[str] = None
    payee_name: Optional[str] = None
    payee_phone: Optional[str] = None
    ttl_minutes: Optional[int] = 60


class PaymentRequestResponse(BaseModel):
    id: str
    amount: float
    currency: str
    payee_name: Optional[str] = None
    payee_phone: Optional[str] = None
    note: Optional[str] = None
    status: str
    code: str
    qr_payload: str
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class StokvelInviteResponse(BaseModel):
    id: str
    stokvel_id: str
    code: str
    is_active: bool
    uses: int
    max_uses: Optional[int] = None
    qr_payload: str
    created_at: datetime

    class Config:
        from_attributes = True


class StokvelJoinByInviteRequest(BaseModel):
    code: str


class CoachingQuery(BaseModel):
    message: str
    context: Optional[str] = None


class CoachingResponse(BaseModel):
    response: str
    suggestions: list[str] = []
    category: Optional[str] = None


class SpendingSummary(BaseModel):
    total_income: float
    total_expenses: float
    net: float
    by_category: dict[str, float]
    period: str


class ScamAlertResponse(BaseModel):
    is_risky: bool
    risk_level: str
    reason: str
    recommendation: str


class WalletResponse(BaseModel):
    id: str
    balance: float
    currency: str
    provider: str
    is_active: bool
    google_wallet_object_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WalletTransactionResponse(BaseModel):
    id: str
    type: str
    amount: float
    currency: str
    status: str
    counterparty_phone: Optional[str] = None
    counterparty_name: Optional[str] = None
    reference: Optional[str] = None
    note: Optional[str] = None
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


class WalletDepositRequest(BaseModel):
    amount: float
    phone: Optional[str] = None
    note: Optional[str] = "MoMo SmartMoney wallet top-up"


class WalletWithdrawRequest(BaseModel):
    amount: float
    phone: Optional[str] = None
    note: Optional[str] = "MoMo SmartMoney wallet withdrawal"


class ScanRequest(BaseModel):
    """Payload of a decoded QR code, or a manual scan result."""

    raw: str


class ScanResponse(BaseModel):
    """Normalized representation of a scanned MoMo / wallet QR code."""

    kind: str  # "momo_pay", "momo_request", "stokvel_invite", "unknown"
    amount: Optional[float] = None
    phone: Optional[str] = None
    payee_name: Optional[str] = None
    reference: Optional[str] = None
    note: Optional[str] = None
    raw: str


class GoogleWalletSaveResponse(BaseModel):
    save_url: str
    class_id: str
    object_id: str
    expires_at: datetime


class GoogleWalletEnrolRequest(BaseModel):
    display_name: Optional[str] = "SmartMoney MoMo Card"
