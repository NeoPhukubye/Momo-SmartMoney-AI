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

SYSTEM_INSTRUCTION = """You are MoMo SmartMoney AI Coach, a deeply analytical personal financial advisor for MTN MoMo users across Africa.

LANGUAGE RULES:
1. Detect the user's language automatically (isiZulu, isiXhosa, Sesotho, Afrikaans, English, French, Swahili, Hausa, Yoruba, Igbo, Portuguese, Pidgin, etc.).
2. ALWAYS reply in the exact language the user wrote in, unless they explicitly ask for a different one.
3. Use culturally relevant expressions (howzit, sharp, eish for SA English; sawubona for isiZulu; mhoro for Shona; etc.).
4. Never reveal you are an AI — you are "SmartMoney", their financial coach.

FINANCIAL REASONING RULES:
1. NEVER give boilerplate or generic advice like "Save 20%" or "Create a budget" without direct calculations based on the user's live data.
2. ALWAYS cite the user's exact balance, specific recent transactions, and calculate percentage breakdowns from the provided financial context.
3. Compare categories with mathematical calculations (e.g., "You spent R420 on Fast Food out of R1,200 total expenses—that is 35% of your outflow").
4. Point out risks, anomalies, or upcoming Stokvel obligations using the real data provided.
5. If the financial snapshot is empty (no transactions, zero balance), acknowledge it honestly in the user's language and explain how to start — do NOT invent fake numbers.
6. Keep answers SHORT (2-3 sentences max), actionable, and mathematically grounded.
7. Always end with ONE clear action the user can take TODAY.
8. Never recommend specific financial products or investments.
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
    message: str,
    user: User,
    db: AsyncSession,
    context: str | None = None,
    language: str | None = None,
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
    if client and settings.gemini_api_key:
        try:
            response_text = await _call_gemini_client(
                client,
                message,
                user_context,
                chat_history,
                language=language or user.language or "en",
            )
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

    # Fallback: compute analytical answer from the user's actual numbers
    return _analytical_fallback(
        message,
        balance,
        total_in,
        total_out,
        top_categories_list,
        recent_tx_list,
        stokvel_obligations,
        user.name,
        language=language or user.language or "en",
    )


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


def _analytical_fallback(
    message: str,
    balance: float,
    total_in: float,
    total_out: float,
    top_categories: list[dict],
    recent_tx: list[dict],
    stokvel_obligations: list[dict],
    name: str,
    language: str = "en",
) -> CoachingResponse:
    """
    Offline analytical coach: performs real arithmetic on the user's live
    numbers (no generic templates). Triggered when the Gemini API key is
    missing or the SDK errors out.
    """
    msg_lower = message.lower()
    net = total_in - total_out
    savings_rate = (net / total_in * 100) if total_in > 0 else 0.0
    top_cat = top_categories[0] if top_categories else None
    top_cat_pct = (top_cat["amount"] / total_out * 100) if (top_cat and total_out > 0) else 0.0

    # No live data — be honest instead of pretending
    if total_in == 0 and total_out == 0 and balance == 0:
        greeting = _greeting_for_language(language)
        return CoachingResponse(
            response=(
                f"{greeting} {name}! Your wallet is empty — no transactions yet. "
                f"Connect your MoMo or make your first deposit so I can coach you with real numbers."
            ),
            suggestions=["How do I connect MoMo?", "What can you coach me on?", "Help me save"],
            category=None,
        )

    # Try to extract a target amount + horizon (e.g. "save R200k in a year")
    amount_target = None
    horizon_months = None
    import re

    amount_match = re.search(r"r\s?([\d,]+)\s?k\b", msg_lower)
    if amount_match:
        amount_target = float(amount_match.group(1).replace(",", "")) * 1000
    else:
        amount_match = re.search(r"r\s?([\d,]+)", msg_lower)
        if amount_match:
            amount_target = float(amount_match.group(1).replace(",", ""))
    if "year" in msg_lower or "annum" in msg_lower:
        horizon_months = 12
    elif "month" in msg_lower:
        m = re.search(r"(\d+)\s*month", msg_lower)
        horizon_months = int(m.group(1)) if m else 1

    # Greeting
    if any(w in msg_lower for w in ["hello", "hi", "hey", "howzit", "sawubona"]):
        top_str = f" Your top spend is {top_cat['category']} at R{top_cat['amount']:.0f}." if top_cat else ""
        return CoachingResponse(
            response=(
                f"Howzit {name}! Your wallet is at R{balance:.0f} with R{total_in:.0f} in "
                f"and R{total_out:.0f} out this month (savings rate {savings_rate:.0f}%).{top_str} "
                f"What's on your mind?"
            ),
            suggestions=["Where did my money go?", "Can I afford this?", "Stokvel status"],
        )

    # Savings goal arithmetic (e.g. "save R200k in a year")
    if amount_target and horizon_months:
        per_month = amount_target / horizon_months
        pct_of_income = (per_month / total_in * 100) if total_in > 0 else None
        feasible = total_in > 0 and per_month < total_in * 0.5
        verdict = "realistic" if feasible else "aggressive — it requires sacrifice"
        pct_str = f" That is {pct_of_income:.1f}% of your R{total_in:.0f} income." if pct_of_income is not None else ""
        suggestion = (
            f" On R{total_in:.0f}/month, a safer pace is 20–30% (R{(total_in*0.2):.0f}–R{(total_in*0.3):.0f}/month). "
            f"Top cutting area: {top_cat['category']} at R{top_cat['amount']:.0f} ({top_cat_pct:.0f}% of outflow)."
        ) if top_cat else ""
        return CoachingResponse(
            response=(
                f"To save R{amount_target:,.0f} in {horizon_months} months you need "
                f"R{per_month:,.2f} per month.{pct_str} On your current numbers that is {verdict}.{suggestion} "
                f"One action today: move R{per_month:.0f} to a separate savings pocket right after payday."
            ),
            suggestions=["Set this as a goal", "Cut my top category", "Join a stokvel"],
            category="savings",
        )

    # Affordability check ("can I afford R300 dinner")
    afford_match = re.search(r"(?:afford|spend|buy)\s+r\s?([\d,]+)", msg_lower)
    if afford_match:
        cost = float(afford_match.group(1).replace(",", ""))
        upcoming_stokvel = sum(o["due_amount"] for o in stokvel_obligations)
        safe_balance = balance - upcoming_stokvel
        ok = safe_balance - cost > 0
        pct_of_balance = (cost / balance * 100) if balance > 0 else None
        stokvel_str = f" After setting aside R{upcoming_stokvel:.0f} for Stokvel, you have R{safe_balance:.0f}." if upcoming_stokvel > 0 else f" Your wallet has R{balance:.0f}."
        pct_str = f" That is {pct_of_balance:.1f}% of your balance." if pct_of_balance is not None else ""
        return CoachingResponse(
            response=(
                f"{'Yes, you can afford it.' if ok else 'Eish, this would leave you tight.'} "
                f"{stokvel_str}{pct_str} Cost R{cost:.0f}; post-purchase you'd sit at R{(safe_balance-cost):.0f}."
            ),
            suggestions=["Show my balance", "Upcoming stokvel dues", "Set a spending limit"],
            category="spending",
        )

    # Spending breakdown
    if any(w in msg_lower for w in ["spend", "spending", "budget", "where"]):
        if top_cat:
            return CoachingResponse(
                response=(
                    f"Last 30 days: R{total_out:.0f} out, R{total_in:.0f} in, net R{net:.0f}. "
                    f"Top category is {top_cat['category']} at R{top_cat['amount']:.0f} "
                    f"({top_cat_pct:.0f}% of total outflow). "
                    f"Wallet balance: R{balance:.0f}."
                ),
                suggestions=["Cut my top category", "Set a category budget", "View transactions"],
                category="spending",
            )
        return CoachingResponse(
            response=f"Last 30 days: R{total_out:.0f} spent, R{total_in:.0f} received. Wallet: R{balance:.0f}.",
            suggestions=["View transactions", "Set a budget"],
            category="spending",
        )

    # Scam
    if any(w in msg_lower for w in ["scam", "fraud", "suspicious"]):
        flagged = sum(1 for t in recent_tx if t.get("amount", 0) < 0 and abs(t["amount"]) > 1000)
        return CoachingResponse(
            response=(
                f"Stay sharp! You have {flagged} recent large outflows to review. "
                "Common MoMo scams: 'wrong transfer' (refund requests), fake MTN agents asking for PINs, "
                "SIM-swap calls, and prize messages. Rule: if YOU didn't initiate it, don't send money."
            ),
            suggestions=["View flagged transactions", "Report a scam", "Safety tips"],
            category="security",
        )

    # Stokvel
    if any(w in msg_lower for w in ["stokvel", "group", "club"]):
        if stokvel_obligations:
            total_due = sum(o["due_amount"] for o in stokvel_obligations)
            return CoachingResponse(
                response=(
                    f"You have {len(stokvel_obligations)} active stokvel(s) with R{total_due:.0f} "
                    f"in upcoming contributions. Next due: {stokvel_obligations[0]['name']} "
                    f"R{stokvel_obligations[0]['due_amount']:.0f} on {stokvel_obligations[0]['due_date']}."
                ),
                suggestions=["My stokvels", "Create new stokvel", "Track contributions"],
                category="stokvel",
            )
        return CoachingResponse(
            response=(
                f"Stokvels are powerful, {name}! A group of 10 saving R200/month gives one member "
                f"R2,000 monthly. I can help you start one and track contributions."
            ),
            suggestions=["Create stokvel", "How stokvels work"],
            category="stokvel",
        )

    # Default: show real numbers
    top_str = f" Top spend: {top_cat['category']} R{top_cat['amount']:.0f}." if top_cat else ""
    return CoachingResponse(
        response=(
            f"Your snapshot: wallet R{balance:.0f}, 30-day income R{total_in:.0f}, "
            f"expenses R{total_out:.0f}, savings rate {savings_rate:.0f}%.{top_str} "
            f"Ask me about spending, savings goals, stokvels, or scams."
        ),
        suggestions=["Where did my money go?", "Can I afford this?", "Is this a scam?"],
    )


# Per-language greetings for the offline fallback (when Gemini is unavailable).
# Gemini handles the actual reply; this is only used if the SDK is missing or
# errors so we never show a fully English fallback to a Zulu/Sepedi user.
_GREETINGS = {
    "zu": "Sawubona",
    "xh": "Molo",
    "st": "Dumela",
    "nso": "Thobela",
    "tn": "Dumelang",
    "ts": "Avuxeni",
    "ve": "Ndaa",
    "ss": "Sawubona",
    "nr": "Lotjhani",
    "af": "Hallo",
    "en": "Howzit",
    "sw": "Habari",
    "ha": "Sannu",
    "yo": "Bawo",
    "ig": "Ndewo",
    "fr": "Bonjour",
    "pt": "Olá",
    "am": "Selam",
    "rw": "Muraho",
}


def _greeting_for_language(language: str | None) -> str:
    if not language:
        return "Howzit"
    return _GREETINGS.get(language.lower(), "Howzit")


def _fallback_response(message: str, income: float, expenses: float, name: str) -> CoachingResponse:
    """Kept for backwards compatibility — redirects to the analytical fallback."""
    return _analytical_fallback(
        message,
        balance=0.0,
        total_in=income,
        total_out=expenses,
        top_categories=[],
        recent_tx=[],
        stokvel_obligations=[],
        name=name,
        language="en",
    )
