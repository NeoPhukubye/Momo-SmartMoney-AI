from sqlalchemy import Column, String, Float, DateTime, Boolean, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    pin_hash = Column(String, nullable=False)
    language = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    transactions = relationship("Transaction", back_populates="user")
    stokvel_memberships = relationship("StokvelMember", back_populates="user")


class TransactionCategory(str, enum.Enum):
    AIRTIME = "airtime"
    TRANSFER = "transfer"
    BILL_PAYMENT = "bill_payment"
    MERCHANT = "merchant"
    SAVINGS = "savings"
    STOKVEL = "stokvel"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    OTHER = "other"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="ZAR")
    counterparty_phone = Column(String)
    counterparty_name = Column(String)
    category = Column(SQLEnum(TransactionCategory), default=TransactionCategory.OTHER)
    description = Column(String)
    direction = Column(String, nullable=False)  # "in" or "out"
    timestamp = Column(DateTime, default=datetime.utcnow)
    momo_reference = Column(String, unique=True)

    # Scam Shield fields
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.LOW)
    risk_reason = Column(String)
    is_flagged = Column(Boolean, default=False)

    user = relationship("User", back_populates="transactions")


class Stokvel(Base):
    __tablename__ = "stokvels"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(String)
    contribution_amount = Column(Float, nullable=False)
    frequency = Column(String, default="monthly")  # weekly, monthly, biweekly
    payout_order = Column(String)  # JSON list of member IDs
    next_contribution_date = Column(DateTime)
    next_payout_date = Column(DateTime)
    created_by = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    members = relationship("StokvelMember", back_populates="stokvel")


class StokvelMember(Base):
    __tablename__ = "stokvel_members"

    id = Column(String, primary_key=True, default=generate_uuid)
    stokvel_id = Column(String, ForeignKey("stokvels.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    role = Column(String, default="member")  # admin, member
    joined_at = Column(DateTime, default=datetime.utcnow)
    total_contributed = Column(Float, default=0.0)
    is_current = Column(Boolean, default=True)  # current in payout rotation

    stokvel = relationship("Stokvel", back_populates="members")
    user = relationship("User", back_populates="stokvel_memberships")


class ScamReport(Base):
    __tablename__ = "scam_reports"

    id = Column(String, primary_key=True, default=generate_uuid)
    reporter_id = Column(String, ForeignKey("users.id"))
    suspect_phone = Column(String, nullable=False)
    description = Column(String)
    transaction_id = Column(String, ForeignKey("transactions.id"))
    reported_at = Column(DateTime, default=datetime.utcnow)
    times_reported = Column(Integer, default=1)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User")


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    balance = Column(Float, default=0.0)
    currency = Column(String, default="ZAR")
    provider = Column(String, default="momo")  # momo, google, mixed
    google_wallet_object_id = Column(String)  # set after Google Wallet save
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    transactions = relationship("WalletTransaction", back_populates="wallet", cascade="all, delete-orphan")


class WalletTransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    STOKVEL_CONTRIBUTION = "stokvel_contribution"
    FEE = "fee"


class WalletTransactionStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESSFUL = "successful"
    FAILED = "failed"


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id = Column(String, primary_key=True, default=generate_uuid)
    wallet_id = Column(String, ForeignKey("wallets.id"), nullable=False, index=True)
    type = Column(SQLEnum(WalletTransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="ZAR")
    status = Column(SQLEnum(WalletTransactionStatus), default=WalletTransactionStatus.PENDING)
    counterparty_phone = Column(String)
    counterparty_name = Column(String)
    reference = Column(String)  # MoMo reference id, stokvel id, scan token, etc.
    note = Column(String)
    source = Column(String, default="momo")  # momo, scan, google, manual
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    wallet = relationship("Wallet", back_populates="transactions")
