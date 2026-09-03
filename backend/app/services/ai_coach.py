import os
import json
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from google import genai
from google.genai import types

from app.models.models import User, Transaction, ChatMessage, Wallet, StokvelMember
from app.schemas.schemas import CoachingResponse
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SYSTEM_INSTRUCTION = """You are MoMo SmartMoney AI Coach, a deeply analytical personal financial advisor for MTN MoMo users in South Africa.

Your personality:
- Warm, encouraging, and street-smart about money.
- Speak simply, like a wise friend — never condescending.
- Use Rands (R) for currency.
- Keep responses SHORT (2-3 sentences max if possible) and highly actionable.
- Celebrate small wins ("R50 saved is R50 earned!").
- Use common South African English expressions naturally (howzit, eish, sharp, lekker).

Your expertise:
- Analyzing spending patterns and giving specific, data-backed advice.
- Personalized budgeting using the 50/30/20 rule adapted for SA informal economy.
- Warning about mobile money scams (fake agents, SIM swaps, "send back" scams, advance fee fraud).
- Encouraging saving — even R5/day matters.
- Supporting stokvel (group savings) participation and management.
- Understanding township economics and informal traders.

CRITICAL RULES FOR ANALYTICAL REASONING:
1. NEVER give boilerplate or generic advice like "Save 20%" or "Create a budget" without direct calculations based on the user's live data.
2. ALWAYS cite the user's exact balance, specific recent transactions, and calculate percentage breakdowns from the provided financial context.
3. Compare categories with mathematical calculations (e.g., "You spent R420 on Fast Food out of R1,200 total expenses—that is 35% of your outflow").
4. Point out risks, anomalies, or upcoming Stokvel obligations using the real data provided.
5. Provide localized, culturally aware advice in South African English or the requested language.
6. Keep answers concise, actionable, and mathematically grounded.
7. Never reveal you are an AI — you are "SmartMoney", their financial coach.
8. If you see overspending, address it gently with practical tips.
9. Always end with ONE clear action the user can take TODAY.
10. If asked about something outside finance, redirect warmly.
11. Never recommend specific financial products or investments.
"""

_client = None


def _get_genai_client():
    global _client
    if _client is None and settings.gemini_api_key:
        try:
            _client = genai.Client(api_key=settings.gemini_api_key)
        except Exception as e:
            logger.error(f"Failed to initialize google-genai Client: {e}")
    return _client


async def get_coaching_response(
    message: str, user: User, db: AsyncSession, context: str | None = None
) -> CoachingResponse:
    # 1. Fetch wallet and balance
    wallet_result = await db.execute(
        select(Wallet).where(Wallet.user_id == user.id)
    )
    wallet = wallet_result.scalar_one_or_none()
    balance = wallet.balance if wallet else 0.0
    currency = wallet.currency if wallet else "ZAR"

    # 2. Fetch last 30 days of transactions for income/expense calculations
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    tx_result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user.id, Transaction.timestamp >= thirty_days_ago)
        .order_by(Transaction.timestamp.desc())
        .limit(20)
    )
    recent_transactions = tx_result.scalars().all()

    total_in = sum(t.amount for t in recent_transactions if t.direction == "in")
    total_out = sum(t.amount for t in recent_transactions if t.direction == "out")

    # Build spending breakdown
    categories = {}
    for t in recent_transactions:
        if t.direction == "out":
            cat = t.category.value if t.category else "other"
            categories[cat] = categories.get(cat, 0) + t.amount

    top_categories_sorted = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
    top_categories_list = [{"category": k.title(), "amount": float(v)} for k, v in top_categories_sorted]

    recent_tx_list = []
    for t in recent_transactions:
        recent_tx_list.append({
            "date": str(t.timestamp.date()) if t.timestamp else "N/A",
            "merchant": t.counterparty_name or t.description or "Unknown",
            "amount": -float(t.amount) if t.direction == "out" else float(t.amount),
            "category": t.category.value if t.category else "other"
        })

    # 3. Fetch Stokvel obligations
    stokvel_result = await db.execute(
        select(StokvelMember)
        .where(StokvelMember.user_id == user.id)
        .options(selectinload(StokvelMember.stokvel))
    )
    memberships = stokvel_result.scalars().all()
    stokvel_obligations = []
    for m in memberships:
        if m.stokvel and m.stokvel.is_active:
            stokvel_obligations.append({
                "name": m.stokvel.name,
                "due_amount": float(m.stokvel.contribution_amount),
                "due_date": str(m.stokvel.next_contribution_date.date()) if m.stokvel.next_contribution_date else "N/A"
            })

    # 4. Assemble financial context
    financial_context = {
        "balance": float(balance),
        "currency": currency,
        "monthly_income": float(total_in),
        "monthly_expenses": float(total_out),
        "top_categories": top_categories_list,
        "recent_transactions": recent_tx_list,
        "stokvel_obligations": stokvel_obligations
    }

    # Detect spending trends for some fallback context or extra information
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_week = [t for t in recent_transactions if t.timestamp >= seven_days_ago]
    week_spending = sum(t.amount for t in recent_week if t.direction == "out")
    daily_avg = week_spending / 7 if recent_week else 0

    user_context = f"""USER FINANCIAL SNAPSHOT (LIVE DATA):
{json.dumps(financial_context, indent=2)}

- Name: {user.name}
- Savings rate: {((total_in - total_out) / total_in * 100) if total_in > 0 else 0:.0f}%
- This week's daily average spend: R{daily_avg:.0f}
- Flags: {sum(1 for t in recent_transactions if t.is_flagged)}"""

    if context:
        user_context += f"\n- Additional context: {context}"

    # Load conversation history for multi-turn context
    chat_history = await _get_chat_history(user.id, db)

    # Try Gemini Client
    client = _get_genai_client()
    if client:
        try:
            response_text = await _call_gemini_client(client, message, user_context, chat_history, language=user.language or "en")
            if response_text:
                # Save to chat history
                await _save_chat_message(user.id, "user", message, db)
                await _save_chat_message(user.id, "assistant", response_text, db)
                await db.commit()

                return CoachingResponse(
                    response=response_text,
                    suggestions=_generate_suggestions(message, total_in, total_out),
                    category=_detect_category(message),
                )
        except Exception as e:
            logger.warning(f"Gemini SDK Client error: {e}")

    # Fallback response
    return _fallback_response(message, total_in, total_out, user.name)


async def _get_chat_history(user_id: str, db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == user_id)
        .order_by(desc(ChatMessage.created_at))
        .limit(10)
    )
    messages = result.scalars().all()
    # Return in chronological order
    return [{"role": m.role, "content": m.content} for m in reversed(messages)]


async def _save_chat_message(user_id: str, role: str, content: str, db: AsyncSession):
    msg = ChatMessage(user_id=user_id, role=role, content=content)
    db.add(msg)


async def _call_gemini_client(client, message: str, user_context: str, history: list[dict], language: str = "en") -> str | None:
    import asyncio

    history_text = ""
    if history:
        history_text = "\n\nRECENT CONVERSATION:\n"
        for h in history[-6:]:  # Last 3 exchanges
            prefix = "User" if h["role"] == "user" else "You"
            history_text += f"{prefix}: {h['content']}\n"

    prompt = f"""{user_context}{history_text}

TARGET RESPONSE LANGUAGE: {language}

USER QUESTION:
"{message}"

Analyze the numbers above. Identify real patterns, compute relevant percentages, and answer the user's question directly using their actual transaction and balance data.
"""

    loop = asyncio.get_event_loop()
    # Call client.models.generate_content in an executor because the google-genai library is synchronous
    response = await loop.run_in_executor(
        None,
        lambda: client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.3,
                max_output_tokens=300,
            )
        )
    )

    if response and response.text:
        return response.text.strip()
    return None


def _detect_category(message: str) -> str | None:
    msg_lower = message.lower()
    if any(w in msg_lower for w in ["save", "savings", "goal", "invest"]):
        return "savings"
    if any(w in msg_lower for w in ["spend", "budget", "money", "expensive", "cost"]):
        return "spending"
    if any(w in msg_lower for w in ["scam", "fraud", "suspicious", "fake", "stolen"]):
        return "security"
    if any(w in msg_lower for w in ["stokvel", "group", "club", "contribute"]):
        return "stokvel"
    return None


def _generate_suggestions(message: str, income: float, expenses: float) -> list[str]:
    msg_lower = message.lower()
    if any(w in msg_lower for w in ["save", "savings", "goal"]):
        return ["Set a savings goal", "View my progress", "Join a stokvel"]
    if any(w in msg_lower for w in ["spend", "budget", "money", "expensive"]):
        return ["Show spending breakdown", "Set a budget", "Where can I cut back?"]
    if any(w in msg_lower for w in ["scam", "fraud", "suspicious", "fake"]):
        return ["View flagged transactions", "Report a scam", "Safety tips"]
    if any(w in msg_lower for w in ["stokvel", "group", "club"]):
        return ["My stokvels", "Create a stokvel", "Contribution history"]
    if any(w in msg_lower for w in ["hello", "hi", "hey", "howzit"]):
        return ["How am I doing?", "Help me save", "Any scam alerts?"]
    # Context-aware suggestions
    if income > 0 and expenses > income * 0.8:
        return ["Where am I overspending?", "Help me cut back", "Emergency fund tips"]
    return ["Check my spending", "Help me save", "Is this a scam?"]


def _fallback_response(message: str, income: float, expenses: float, name: str) -> CoachingResponse:
    msg_lower = message.lower()

    if any(w in msg_lower for w in ["hello", "hi", "hey", "howzit", "sawubona"]):
        return CoachingResponse(
            response=f"Howzit {name}! I'm SmartMoney, your financial coach. I can help with your spending, savings goals, stokvel tracking, or keeping you safe from scams. What's on your mind?",
            suggestions=["Show my spending", "Help me save", "Stokvel info"],
        )

    if any(w in msg_lower for w in ["spend", "spending", "budget"]):
        net = income - expenses
        status = "You're in the green" if net > 0 else "Things are tight"
        return CoachingResponse(
            response=f"{status} this month — R{income:.0f} in, R{expenses:.0f} out. Net: R{net:.0f}. Want me to break down where your money's going?",
            suggestions=["Spending breakdown", "Set a budget", "Cut expenses"],
            category="spending",
        )

    if any(w in msg_lower for w in ["save", "savings"]):
        suggested = income * 0.1
        return CoachingResponse(
            response=f"Smart move thinking about savings! With your income of R{income:.0f}, try saving 10% — that's R{suggested:.0f}/month. Even R20/day adds up to R600/month. Start small, stay consistent.",
            suggestions=["Set savings goal", "Start with R50/week", "Join stokvel"],
            category="savings",
        )

    if any(w in msg_lower for w in ["scam", "fraud", "suspicious"]):
        return CoachingResponse(
            response="Stay sharp! Common scams: 'wrong transfer' (they ask you to send back), fake MTN agents asking for PINs, and prize messages. Rule: if YOU didn't start it, don't send money.",
            suggestions=["View flagged numbers", "Report a scam", "More safety tips"],
            category="security",
        )

    if any(w in msg_lower for w in ["stokvel", "group", "club"]):
        return CoachingResponse(
            response=f"Stokvels are powerful, {name}! A group of 10 people saving R200/month means someone gets R2,000 every month. I can help you track contributions and predict payouts.",
            suggestions=["My stokvels", "Create new stokvel", "How stokvels work"],
            category="stokvel",
        )

    return CoachingResponse(
        response=f"I'm here to help, {name}! I can coach you on spending, saving, stokvels, or scam protection. Just ask me anything about your money.",
        suggestions=["My spending summary", "Help me save", "Is this a scam?"],
    )
