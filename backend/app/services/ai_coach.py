from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timedelta
import google.generativeai as genai
import logging
import json

from app.models.models import User, Transaction, ChatMessage
from app.schemas.schemas import CoachingResponse
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SYSTEM_PROMPT = """You are SmartMoney AI, a friendly and accessible financial coach for MoMo mobile money users in South Africa.

Your personality:
- Warm, encouraging, and street-smart about money
- You speak simply, like a wise friend — never condescending
- You use Rands (R) for currency
- You keep responses SHORT (2-3 sentences max) and actionable
- You celebrate small wins ("R50 saved is R50 earned!")
- You use common South African English expressions naturally (howzit, eish, sharp, lekker)

Your expertise:
- Analyzing spending patterns and giving specific, data-backed advice
- Personalized budgeting using the 50/30/20 rule adapted for SA informal economy
- Warning about mobile money scams (fake agents, SIM swaps, "send back" scams, advance fee fraud)
- Encouraging saving — even R5/day matters
- Supporting stokvel (group savings) participation and management
- Understanding township economics and informal traders

Rules:
- Never reveal you are an AI — you are "SmartMoney", their financial coach
- If you see overspending, address it gently with practical tips
- Always end with ONE clear action the user can take TODAY
- Reference their actual transaction data when giving advice
- If asked about something outside finance, redirect warmly
- Never recommend specific financial products or investments
- Be aware of South African public holidays, pay cycles (25th of month), and grant payment dates"""


# Gemini model singleton with connection pooling
_gemini_model = None


def _get_gemini_model():
    global _gemini_model
    if _gemini_model is None and settings.gemini_api_key:
        genai.configure(api_key=settings.gemini_api_key)
        _gemini_model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            system_instruction=SYSTEM_PROMPT,
            generation_config=genai.GenerationConfig(
                max_output_tokens=300,
                temperature=0.7,
                top_p=0.9,
                top_k=40,
            ),
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_ONLY_HIGH",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_ONLY_HIGH",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_ONLY_HIGH",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_ONLY_HIGH",
            },
        )
    return _gemini_model


async def get_coaching_response(
    message: str, user: User, db: AsyncSession, context: str | None = None
) -> CoachingResponse:
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user.id, Transaction.timestamp >= thirty_days_ago)
        .order_by(Transaction.timestamp.desc())
        .limit(20)
    )
    recent_transactions = result.scalars().all()

    total_in = sum(t.amount for t in recent_transactions if t.direction == "in")
    total_out = sum(t.amount for t in recent_transactions if t.direction == "out")

    # Build spending breakdown
    categories = {}
    for t in recent_transactions:
        if t.direction == "out":
            cat = t.category.value if t.category else "other"
            categories[cat] = categories.get(cat, 0) + t.amount

    top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
    cat_str = ", ".join(f"{k}: R{v:.0f}" for k, v in top_categories) if top_categories else "No spending data yet"

    # Detect spending trends
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_week = [t for t in recent_transactions if t.timestamp >= seven_days_ago]
    week_spending = sum(t.amount for t in recent_week if t.direction == "out")
    daily_avg = week_spending / 7 if recent_week else 0

    user_context = f"""USER FINANCIAL SNAPSHOT:
- Name: {user.name}
- Last 30 days: Income R{total_in:.0f}, Spent R{total_out:.0f}, Net R{total_in - total_out:.0f}
- Savings rate: {((total_in - total_out) / total_in * 100) if total_in > 0 else 0:.0f}%
- Top spending: {cat_str}
- This week's daily average spend: R{daily_avg:.0f}
- Transactions this month: {len(recent_transactions)}
- Flagged transactions: {sum(1 for t in recent_transactions if t.is_flagged)}"""

    if context:
        user_context += f"\n- Additional context: {context}"

    # Load conversation history for multi-turn context
    chat_history = await _get_chat_history(user.id, db)

    # Try Gemini
    model = _get_gemini_model()
    if model:
        try:
            response = await _call_gemini(model, message, user_context, chat_history)
            if response:
                # Save to chat history
                await _save_chat_message(user.id, "user", message, db)
                await _save_chat_message(user.id, "assistant", response, db)
                await db.commit()

                return CoachingResponse(
                    response=response,
                    suggestions=_generate_suggestions(message, total_in, total_out),
                    category=_detect_category(message),
                )
        except Exception as e:
            logger.warning(f"Gemini API error: {e}")

    # Fallback
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


async def _call_gemini(model, message: str, user_context: str, history: list[dict]) -> str | None:
    import asyncio

    # Build conversation with history for context
    history_text = ""
    if history:
        history_text = "\n\nRECENT CONVERSATION:\n"
        for h in history[-6:]:  # Last 3 exchanges
            prefix = "User" if h["role"] == "user" else "You"
            history_text += f"{prefix}: {h['content']}\n"

    prompt = f"{user_context}{history_text}\n\nUser says now: {message}"

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: model.generate_content(prompt))

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
