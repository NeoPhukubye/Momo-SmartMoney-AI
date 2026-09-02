from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.config import get_settings
from app.database import get_db
from app.models.models import User, Stokvel, StokvelMember
from app.schemas.schemas import StokvelCreate, StokvelResponse
from app.routers.auth import get_current_user
from app.utils import is_mtn_number

router = APIRouter()

settings = get_settings()


def _stokvel_response(stokvel: Stokvel, member_count: int, mtn_member_count: int) -> StokvelResponse:
    return StokvelResponse(
        id=stokvel.id,
        name=stokvel.name,
        description=stokvel.description,
        contribution_amount=stokvel.contribution_amount,
        frequency=stokvel.frequency,
        next_contribution_date=stokvel.next_contribution_date,
        next_payout_date=stokvel.next_payout_date,
        member_count=member_count,
        mtn_member_count=mtn_member_count,
        has_mtn_member=mtn_member_count > 0,
        is_active=stokvel.is_active,
    )


@router.post("/", response_model=StokvelResponse)
async def create_stokvel(
    data: StokvelCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Rule: at least one member must be an MTN subscriber.
    # The creator is the only member at creation, so their phone must be MTN.
    prefixes = [p for p in settings.mtn_prefixes.split(",") if p]
    if not is_mtn_number(user.phone_number, prefixes, settings.mtn_default_country_code):
        raise HTTPException(
            status_code=400,
            detail=(
                "At least one member must have an MTN mobile number. "
                "Your registered number does not appear to be an MTN number."
            ),
        )

    stokvel = Stokvel(
        name=data.name,
        description=data.description,
        contribution_amount=data.contribution_amount,
        frequency=data.frequency,
        created_by=user.id,
    )
    db.add(stokvel)
    await db.flush()

    # Every member has equal authority. The creator is recorded as a regular
    # "member" rather than a privileged "admin" so all members share the same
    # role from the very first join.
    member = StokvelMember(
        stokvel_id=stokvel.id,
        user_id=user.id,
        role="member",
    )
    db.add(member)
    await db.commit()
    await db.refresh(stokvel)

    return _stokvel_response(stokvel, member_count=1, mtn_member_count=1)


@router.get("/", response_model=list[StokvelResponse])
async def list_stokvels(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Stokvel)
        .join(StokvelMember)
        .where(StokvelMember.user_id == user.id)
    )
    stokvels = result.scalars().all()

    prefixes = [p for p in settings.mtn_prefixes.split(",") if p]
    default_cc = settings.mtn_default_country_code

    responses = []
    for s in stokvels:
        member_result = await db.execute(
            select(StokvelMember).where(StokvelMember.stokvel_id == s.id)
        )
        memberships = member_result.scalars().all()
        mtn_count = 0
        for m in memberships:
            member_user_result = await db.execute(
                select(User).where(User.id == m.user_id)
            )
            member_user = member_user_result.scalar_one_or_none()
            if member_user and is_mtn_number(member_user.phone_number, prefixes, default_cc):
                mtn_count += 1
        responses.append(_stokvel_response(s, member_count=len(memberships), mtn_member_count=mtn_count))
    return responses


@router.post("/{stokvel_id}/join")
async def join_stokvel(
    stokvel_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Stokvel).where(Stokvel.id == stokvel_id))
    stokvel = result.scalar_one_or_none()
    if not stokvel:
        raise HTTPException(status_code=404, detail="Stokvel not found")

    existing = await db.execute(
        select(StokvelMember).where(
            StokvelMember.stokvel_id == stokvel_id,
            StokvelMember.user_id == user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already a member")

    # New members join with the same authority as everyone else.
    member = StokvelMember(stokvel_id=stokvel_id, user_id=user.id, role="member")
    db.add(member)
    await db.commit()
    return {"message": f"Joined stokvel '{stokvel.name}' successfully"}


@router.post("/{stokvel_id}/contribute")
async def record_contribution(
    stokvel_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StokvelMember).where(
            StokvelMember.stokvel_id == stokvel_id,
            StokvelMember.user_id == user.id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Not a member of this stokvel")

    stokvel_result = await db.execute(select(Stokvel).where(Stokvel.id == stokvel_id))
    stokvel = stokvel_result.scalar_one()

    member.total_contributed += stokvel.contribution_amount
    await db.commit()
    return {
        "message": f"Contribution of {stokvel.contribution_amount} recorded",
        "total_contributed": member.total_contributed,
    }