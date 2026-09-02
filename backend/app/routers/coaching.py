from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import User
from app.schemas.schemas import CoachingQuery, CoachingResponse
from app.routers.auth import get_current_user
from app.services.ai_coach import get_coaching_response

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/chat", response_model=CoachingResponse)
@limiter.limit("20/minute")
async def coaching_chat(
    request: Request,
    query: CoachingQuery,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    response = await get_coaching_response(query.message, user, db, context=query.context)
    return response


@router.get("/tips")
async def daily_tips(user: User = Depends(get_current_user)):
    tips = [
        "Set up a weekly savings goal — even R10/week adds up to R520/year!",
        "Check your spending categories to find where you can cut back.",
        "Never share your MoMo PIN with anyone — not even someone claiming to be from MTN.",
        "Join a stokvel to reach savings goals faster with your community.",
        "Review flagged transactions weekly to stay safe from fraud.",
        "The 50/30/20 rule: 50% needs, 30% wants, 20% savings — adjust for your situation.",
        "Set money aside BEFORE spending — pay yourself first, even if it's just R20.",
        "Track every transaction for a week to spot money leaks you didn't know about.",
    ]
    return {"tips": tips, "user_name": user.name}
