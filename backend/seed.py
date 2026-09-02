"""Seed script to populate database with realistic demo data for hackathon presentation."""
import asyncio
from datetime import datetime, timedelta
import random
from passlib.context import CryptContext

from app.database import engine, async_session, Base
from app.models.models import (
    User, Transaction, Stokvel, StokvelMember, ScamReport,
    TransactionCategory, RiskLevel,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


DEMO_TRANSACTIONS = [
    # Income
    {"amount": 8500, "direction": "in", "category": TransactionCategory.DEPOSIT, "description": "Salary - Shoprite", "counterparty_name": "Shoprite Holdings"},
    {"amount": 1200, "direction": "in", "category": TransactionCategory.DEPOSIT, "description": "Side hustle payment", "counterparty_name": "Thabo M"},
    {"amount": 350, "direction": "in", "category": TransactionCategory.DEPOSIT, "description": "Refund - Takealot", "counterparty_name": "Takealot"},
    # Expenses
    {"amount": 2100, "direction": "out", "category": TransactionCategory.BILL_PAYMENT, "description": "Rent payment", "counterparty_name": "Landlord - Mrs Ndlovu"},
    {"amount": 850, "direction": "out", "category": TransactionCategory.BILL_PAYMENT, "description": "Electricity prepaid", "counterparty_name": "City Power"},
    {"amount": 499, "direction": "out", "category": TransactionCategory.BILL_PAYMENT, "description": "DStv Premium", "counterparty_name": "Multichoice"},
    {"amount": 120, "direction": "out", "category": TransactionCategory.AIRTIME, "description": "MTN data bundle 2GB", "counterparty_name": "MTN"},
    {"amount": 65, "direction": "out", "category": TransactionCategory.AIRTIME, "description": "Airtime recharge", "counterparty_name": "MTN"},
    {"amount": 450, "direction": "out", "category": TransactionCategory.MERCHANT, "description": "Groceries - Pick n Pay", "counterparty_name": "Pick n Pay Soweto"},
    {"amount": 280, "direction": "out", "category": TransactionCategory.MERCHANT, "description": "Groceries - Shoprite", "counterparty_name": "Shoprite"},
    {"amount": 150, "direction": "out", "category": TransactionCategory.MERCHANT, "description": "Fuel - Engen", "counterparty_name": "Engen Garage"},
    {"amount": 200, "direction": "out", "category": TransactionCategory.TRANSFER, "description": "Sent to Mom", "counterparty_name": "Mama", "counterparty_phone": "0731234567"},
    {"amount": 500, "direction": "out", "category": TransactionCategory.STOKVEL, "description": "Stokvel contribution", "counterparty_name": "Kasi Savings Club"},
    {"amount": 300, "direction": "out", "category": TransactionCategory.WITHDRAWAL, "description": "ATM withdrawal", "counterparty_name": "FNB ATM"},
    {"amount": 89, "direction": "out", "category": TransactionCategory.MERCHANT, "description": "Uber ride", "counterparty_name": "Uber SA"},
    # Flagged/risky transactions
    {"amount": 2500, "direction": "out", "category": TransactionCategory.TRANSFER, "description": "Prize claim fee - urgent", "counterparty_name": "Unknown", "counterparty_phone": "0609876543", "risk_level": RiskLevel.CRITICAL, "risk_reason": "Message contains suspicious language: 'prize'; First time sending to this number — and it's a large amount", "is_flagged": True},
    {"amount": 800, "direction": "out", "category": TransactionCategory.TRANSFER, "description": "Wrong transfer reversal", "counterparty_name": "Unknown Caller", "counterparty_phone": "0781112233", "risk_level": RiskLevel.HIGH, "risk_reason": "Message contains suspicious language: 'wrong transfer'; This number has been reported before", "is_flagged": True},
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # Create demo user
        user = User(
            phone_number="0712345678",
            name="Neo",
            pin_hash=pwd_context.hash("1234"),
            language="en",
        )
        db.add(user)
        await db.flush()

        # Create second user for stokvel demo
        user2 = User(
            phone_number="0723456789",
            name="Thandi Mokoena",
            pin_hash=pwd_context.hash("5678"),
            language="en",
        )
        db.add(user2)
        await db.flush()

        # Add transactions with varied dates
        now = datetime.utcnow()
        for i, txn_data in enumerate(DEMO_TRANSACTIONS):
            days_ago = random.randint(0, 28)
            hours_ago = random.randint(0, 23)
            txn = Transaction(
                user_id=user.id,
                amount=txn_data["amount"],
                currency="ZAR",
                direction=txn_data["direction"],
                category=txn_data["category"],
                description=txn_data["description"],
                counterparty_name=txn_data.get("counterparty_name"),
                counterparty_phone=txn_data.get("counterparty_phone"),
                risk_level=txn_data.get("risk_level", RiskLevel.LOW),
                risk_reason=txn_data.get("risk_reason"),
                is_flagged=txn_data.get("is_flagged", False),
                timestamp=now - timedelta(days=days_ago, hours=hours_ago),
            )
            db.add(txn)

        # Create stokvel
        stokvel = Stokvel(
            name="Kasi Savings Club",
            description="Monthly savings group - Soweto community members",
            contribution_amount=500,
            frequency="monthly",
            created_by=user.id,
            next_contribution_date=now + timedelta(days=15),
            next_payout_date=now + timedelta(days=45),
        )
        db.add(stokvel)
        await db.flush()

        # Add members
        member1 = StokvelMember(stokvel_id=stokvel.id, user_id=user.id, role="admin", total_contributed=2500)
        member2 = StokvelMember(stokvel_id=stokvel.id, user_id=user2.id, role="member", total_contributed=2000)
        db.add(member1)
        db.add(member2)

        # Add known scam numbers
        scam_numbers = [
            ("0609876543", "Fake prize scam - asks for claim fee"),
            ("0781112233", "Wrong transfer reversal scam"),
            ("0651234567", "Fake MTN agent - asks for PIN"),
        ]
        for phone, desc in scam_numbers:
            for _ in range(random.randint(3, 8)):
                report = ScamReport(
                    reporter_id=user.id,
                    suspect_phone=phone,
                    description=desc,
                )
                db.add(report)

        await db.commit()
        print("Database seeded successfully!")
        print(f"Demo user: phone=0712345678, pin=1234")
        print(f"Demo user 2: phone=0723456789, pin=5678")


if __name__ == "__main__":
    asyncio.run(seed())
