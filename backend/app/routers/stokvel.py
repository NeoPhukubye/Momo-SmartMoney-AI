from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.database import get_db
from app.models.models import User, Stokvel, StokvelMember
from app.schemas.schemas import StokvelCreate, StokvelResponse
from app.routers.auth import get_current_user

router = APIRouter()


@router.post("/", response_model=StokvelResponse)
async def create_stokvel(
    data: StokvelCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stokvel = Stokvel(
        name=data.name,
        description=data.description,
        contribution_amount=data.contribution_amount,
        frequency=data.frequency,
        created_by=user.id,
    )
    db.add(stokvel)
    await db.flush()

    member = StokvelMember(
        stokvel_id=stokvel.id,
        user_id=user.id,
        role="admin",
    )
    db.add(member)
    await db.commit()
    await db.refresh(stokvel)

    return StokvelResponse(
        id=stokvel.id,
        name=stokvel.name,
        description=stokvel.description,
        contribution_amount=stokvel.contribution_amount,
        frequency=stokvel.frequency,
        next_contribution_date=stokvel.next_contribution_date,
        next_payout_date=stokvel.next_payout_date,
        member_count=1,
        is_active=stokvel.is_active,
    )


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
    responses = []
    for s in stokvels:
        member_result = await db.execute(
            select(StokvelMember).where(StokvelMember.stokvel_id == s.id)
        )
        count = len(member_result.scalars().all())
        responses.append(StokvelResponse(
            id=s.id,
            name=s.name,
            description=s.description,
            contribution_amount=s.contribution_amount,
            frequency=s.frequency,
            next_contribution_date=s.next_contribution_date,
            next_payout_date=s.next_payout_date,
            member_count=count,
            is_active=s.is_active,
        ))
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

    member = StokvelMember(stokvel_id=stokvel_id, user_id=user.id)
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
