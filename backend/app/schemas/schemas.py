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
