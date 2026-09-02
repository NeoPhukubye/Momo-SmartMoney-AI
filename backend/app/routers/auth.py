import secrets
from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.models import User
from app.schemas.schemas import (
    GoogleAuthRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.utils import is_mtn_number

router = APIRouter()
settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        phone_number=user.phone_number,
        name=user.name,
        language=user.language,
        created_at=user.created_at,
        email=user.email,
        avatar_url=user.avatar_url,
        auth_provider=user.auth_provider,
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.phone_number == user_data.phone_number))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Phone number already registered")

    user = User(
        phone_number=user_data.phone_number,
        name=user_data.name,
        pin_hash=pwd_context.hash(user_data.pin),
        language=user_data.language,
        auth_provider="pin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token, user=_user_response(user))


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.phone_number == credentials.phone_number))
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(credentials.pin, user.pin_hash):
        raise HTTPException(status_code=401, detail="Invalid phone number or PIN")

    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token, user=_user_response(user))


# ---------------------------------------------------------------------------
# Google OAuth (Identity Services)
# ---------------------------------------------------------------------------

_GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
_GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


def _allowed_audiences() -> set[str]:
    return {cid.strip() for cid in (settings.google_client_ids or "").split(",") if cid.strip()}


async def _verify_google_id_token(token: str) -> dict:
    """Verify a Google ID token's signature, audience, issuer, and expiry.

    Returns the decoded claims on success. Raises HTTPException otherwise.
    """
    audiences = _allowed_audiences()
    if not audiences:
        raise HTTPException(
            status_code=500,
            detail="Google sign-in is not configured on the server (GOOGLE_CLIENT_IDS is empty).",
        )

    # Fetch Google's public keys (cached only for the lifetime of this request).
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            jwks_resp = await client.get(_GOOGLE_CERTS_URL)
            jwks_resp.raise_for_status()
            jwks = jwks_resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not fetch Google JWKS: {exc}")

    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail="Google ID token key not found")

        claims = jwt.decode(
            token,
            key,
            algorithms=[unverified_header.get("alg", "RS256")],
            audience=list(audiences),
            issuers=list(_GOOGLE_ISSUERS),
            options={"verify_aud": True, "verify_iss": True, "verify_exp": True},
        )
    except JWTError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid Google ID token: {exc}")

    return claims


def _placeholder_msisdn() -> str:
    """Random SA-shaped placeholder for Google-only users who haven't added a phone yet."""
    return f"+27g{secrets.token_hex(6)}"


@router.post("/google", response_model=TokenResponse)
async def google_auth(payload: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """Verify a Google ID token and find-or-create the corresponding user."""
    if not payload.credential:
        raise HTTPException(status_code=400, detail="Missing Google credential")

    claims = await _verify_google_id_token(payload.credential)
    google_sub = claims.get("sub")
    email = claims.get("email")
    email_verified = bool(claims.get("email_verified"))
    name = claims.get("name") or payload.name or (email.split("@")[0] if email else "Google user")
    picture = claims.get("picture")

    if not google_sub:
        raise HTTPException(status_code=400, detail="Google token missing sub claim")

    # 1) Existing Google-linked user
    result = await db.execute(select(User).where(User.google_sub == google_sub))
    user = result.scalar_one_or_none()

    # 2) Otherwise, if we have a verified email, try to link to an existing user
    if user is None and email and email_verified:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

    if user is None:
        # Brand-new user. They MUST supply an MTN phone number so the Stokvel MTN
        # rule is satisfied; otherwise we reject the registration.
        phone = (payload.phone_number or "").strip()
        if not phone:
            raise HTTPException(
                status_code=400,
                detail="New Google sign-ins must include a phone_number to satisfy the MTN rule.",
            )
        prefixes = [p for p in settings.mtn_prefixes.split(",") if p]
        if not is_mtn_number(phone, prefixes, settings.mtn_default_country_code):
            raise HTTPException(
                status_code=400,
                detail="At least one member must have an MTN mobile number. The provided phone is not MTN.",
            )

        # Make sure the phone isn't already taken
        result = await db.execute(select(User).where(User.phone_number == phone))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Phone number already registered")

        # Google users don't have a PIN yet; generate a random unusable hash so the
        # NOT NULL constraint is satisfied. They can set a PIN later from their
        # profile (out of scope for this change).
        user = User(
            phone_number=phone,
            name=name,
            pin_hash=pwd_context.hash(secrets.token_urlsafe(16)),
            email=email,
            google_sub=google_sub,
            avatar_url=picture,
            auth_provider="google",
        )
        db.add(user)
    else:
        # Backfill identity fields on subsequent sign-ins
        if not user.google_sub:
            user.google_sub = google_sub
        if not user.email and email:
            user.email = email
        if picture and not user.avatar_url:
            user.avatar_url = picture
        if user.auth_provider == "pin":
            user.auth_provider = "both"
        elif not user.auth_provider:
            user.auth_provider = "google"

    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token, user=_user_response(user))