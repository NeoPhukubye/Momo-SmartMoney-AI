from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.config import get_settings
from app.database import get_db
from app.models.models import (
    Stokvel,
    StokvelInvite,
    StokvelMember,
    User,
    UserDirectory,
)
from app.schemas.schemas import (
    StokvelCreate,
    StokvelInviteResponse,
    StokvelJoinByInviteRequest,
    StokvelResponse,
)
from app.routers.auth import get_current_user
from app.utils import is_mtn_number

router = APIRouter()

settings = get_settings()


def _short_code(length: int = 6) -> str:
    import secrets
    import string
    alphabet = string.ascii_uppercase + string.digits
    # Avoid ambiguous chars
    alphabet = alphabet.replace("O", "").replace("0", "").replace("I", "").replace("1", "")
    return "".join(secrets.choice(alphabet) for _ in range(length))


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
    # MoMo Stokvels work best when at least one member is on MTN (so payouts
    # can flow through MoMo), but we no longer block creation on this — a
    # group can be created now and an MTN member linked before the first
    # payout cycle.
    prefixes = [p for p in settings.mtn_prefixes.split(",") if p]
    creator_is_mtn = is_mtn_number(user.phone_number, prefixes, settings.mtn_default_country_code)

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

    return _stokvel_response(
        stokvel,
        member_count=1,
        mtn_member_count=1 if creator_is_mtn else 0,
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


# ---------------------------------------------------------------------------
# Stokvel invite QR generator
# ---------------------------------------------------------------------------

def _invite_response(inv: StokvelInvite, stokvel_id: str) -> StokvelInviteResponse:
    payload = f"stokvel://invite/{inv.code}"
    return StokvelInviteResponse(
        id=inv.id,
        stokvel_id=stokvel_id,
        code=inv.code,
        is_active=inv.is_active,
        uses=inv.uses,
        max_uses=inv.max_uses,
        qr_payload=payload,
        created_at=inv.created_at,
    )


@router.post("/{stokvel_id}/invite", response_model=StokvelInviteResponse)
async def create_invite(
    stokvel_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a shareable invite code + QR payload for a Stokvel.

    Any current member can create an invite. The QR contains
    `stokvel://invite/<CODE>` so the scan endpoint on the receiver's side
    routes them into the join flow.
    """
    s = await db.execute(select(Stokvel).where(Stokvel.id == stokvel_id))
    stokvel = s.scalar_one_or_none()
    if not stokvel:
        raise HTTPException(status_code=404, detail="Stokvel not found")

    # Must already be a member to invite
    m = await db.execute(
        select(StokvelMember).where(
            StokvelMember.stokvel_id == stokvel_id,
            StokvelMember.user_id == user.id,
        )
    )
    if not m.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Only members can invite others")

    # Generate a unique code
    for _ in range(10):
        code = _short_code(6)
        existing = await db.execute(select(StokvelInvite).where(StokvelInvite.code == code))
        if not existing.scalar_one_or_none():
            break
    else:
        raise HTTPException(status_code=500, detail="Could not allocate invite code, retry")

    invite = StokvelInvite(
        stokvel_id=stokvel_id,
        code=code,
        created_by=user.id,
        is_active=True,
    )
    db.add(invite)
    # Also register this user in the directory so other members can P2P them.
    from app.utils import _normalize_phone  # local import to avoid touching utils
    phone = _normalize_phone(user.phone_number)
    if phone:
        existing = await db.execute(select(UserDirectory).where(UserDirectory.phone_number == phone))
        if not existing.scalar_one_or_none():
            db.add(UserDirectory(phone_number=phone, user_id=user.id, display_name=user.name))
    await db.commit()
    await db.refresh(invite)
    return _invite_response(invite, stokvel_id)


@router.get("/{stokvel_id}/invites", response_model=list[StokvelInviteResponse])
async def list_invites(
    stokvel_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    s = await db.execute(select(Stokvel).where(Stokvel.id == stokvel_id))
    if not s.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Stokvel not found")
    result = await db.execute(
        select(StokvelInvite)
        .where(StokvelInvite.stokvel_id == stokvel_id)
        .order_by(StokvelInvite.created_at.desc())
    )
    return [_invite_response(inv, stokvel_id) for inv in result.scalars().all()]


@router.post("/join-by-invite", response_model=StokvelResponse)
async def join_by_invite(
    payload: StokvelJoinByInviteRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Join a Stokvel by entering the invite code (also wired to QR scans)."""
    code = (payload.code or "").strip().upper()
    if code.startswith("STOKVEL://INVITE/"):
        code = code.split("/")[-1]
    if not code:
        raise HTTPException(status_code=400, detail="Invite code is required")

    inv_res = await db.execute(select(StokvelInvite).where(StokvelInvite.code == code))
    invite = inv_res.scalar_one_or_none()
    if not invite or not invite.is_active:
        raise HTTPException(status_code=404, detail="Invite not found or inactive")
    if invite.max_uses is not None and invite.uses >= invite.max_uses:
        raise HTTPException(status_code=400, detail="Invite has reached its use limit")

    s = await db.execute(select(Stokvel).where(Stokvel.id == invite.stokvel_id))
    stokvel = s.scalar_one_or_none()
    if not stokvel or not stokvel.is_active:
        raise HTTPException(status_code=404, detail="Stokvel not found or inactive")

    existing = await db.execute(
        select(StokvelMember).where(
            StokvelMember.stokvel_id == invite.stokvel_id,
            StokvelMember.user_id == user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already a member of this stokvel")

    member = StokvelMember(
        stokvel_id=invite.stokvel_id, user_id=user.id, role="member"
    )
    invite.uses += 1
    db.add(member)
    await db.commit()

    return _stokvel_response(stokvel, member_count=1, mtn_member_count=1)