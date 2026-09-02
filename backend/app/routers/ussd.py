"""USSD callback for *141*8# (Africa's Talking).

The USSD session is short-lived; we cache the user's current selection in
`session["state"]` and look up live data (balance, Stokvels, invites) from
the database on each step. The user is identified by the `phoneNumber`
the gateway sends us; if no account exists yet, the menu still works in
"guest" mode with a hint to register.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import (
    Stokvel,
    StokvelInvite,
    StokvelMember,
    User,
    Wallet,
    WalletTransaction,
    WalletTransactionType,
    WalletTransactionStatus,
)
from app.utils import is_mtn_number

router = APIRouter()

# In-memory session cache. Africa's Talking opens a new POST per user input,
# keyed by sessionId; we hold small state dictionaries.
sessions: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Multilingual text helpers
# ---------------------------------------------------------------------------

T = {
    "welcome": {
        "en": "Welcome to SmartMoney AI",
        "zu": "Siyakwamukela ku-SmartMoney AI",
        "xh": "Wamkelekile ku-SmartMoney AI",
        "st": "Rea u amohela ho SmartMoney AI",
        "sw": "Karibu SmartMoney AI",
        "fr": "Bienvenue sur SmartMoney AI",
    },
    "not_registered": {
        "en": "You are not registered. Open the SmartMoney app or dial *141*8*1# to register.",
        "zu": "Awubhalisanga. Vula i-app ye-SmartMoney.",
        "fr": "Vous n'etes pas enregistre. Ouvrez l'app SmartMoney.",
    },
    "main": {
        "en": (
            "1. Wallet Balance\n"
            "2. Send Money\n"
            "3. Receive Money (get QR)\n"
            "4. My Stokvels\n"
            "5. Join Stokvel (use code)\n"
            "6. Contribute to Stokvel\n"
            "7. Talk to Coach\n"
            "8. Change Language"
        ),
        "zu": (
            "1. Ibhalansi ye-Wallet\n"
            "2. Thumela Imali\n"
            "3. Thola Imali (QR)\n"
            "4. Izitokofela Zami\n"
            "5. Joyina i-Stokvel (ikhodi)\n"
            "6. Nikela ku-Stokvel\n"
            "7. Khuluma noMqeqeshi\n"
            "8. Shintsha Ulimi"
        ),
        "fr": (
            "1. Solde Wallet\n"
            "2. Envoyer Argent\n"
            "3. Recevoir (QR)\n"
            "4. Mes Tontines\n"
            "5. Rejoindre Tontine (code)\n"
            "6. Contribuer Tontine\n"
            "7. Parler au Coach\n"
            "8. Changer Langue"
        ),
    },
    "send_prompt": {
        "en": "CON Enter recipient phone (e.g. 0831234567):",
        "zu": "CON Faka inombolo yomamukeli:",
        "fr": "CON Entrez le numero du destinataire:",
    },
    "amount_prompt": {
        "en": "CON Enter amount in Rands:",
        "zu": "CON Faka inani ngama-Randi:",
        "fr": "CON Entrez le montant en Rands:",
    },
    "confirm_send": {
        "en": "CON Send R{amount} to {phone}?\nRisk: {risk}\n1. Confirm\n2. Cancel",
        "zu": "CON Thumela u-R{amount} ku-{phone}?\n1. Qinisa\n2. Cima",
        "fr": "CON Envoyer R{amount} a {phone}?\n1. Confirmer\n2. Annuler",
    },
    "send_ok": {
        "en": "END Sent. New balance: R{balance}. Ref: {ref}",
        "zu": "END Ithunyelwe. Ibhalansi entsha: R{balance}. Ref: {ref}",
        "fr": "END Envoye. Nouveau solde: R{balance}. Ref: {ref}",
    },
    "send_fail": {
        "en": "END Send failed. {reason}",
        "fr": "END Echec de l'envoi. {reason}",
    },
    "balance": {
        "en": "END Wallet: R{balance} ({provider})",
        "fr": "END Wallet: R{balance} ({provider})",
    },
    "no_stokvels": {
        "en": "END You have no Stokvels. Open the app to create one.",
        "fr": "END Vous n'avez pas de tontines.",
    },
    "stokvel_list": {
        "en": "CON Your Stokvels:\n{lines}\n0. Back",
        "fr": "CON Vos tontines:\n{lines}\n0. Retour",
    },
    "stokvel_action": {
        "en": "CON {name}:\n1. View invite code\n2. Record contribution\n0. Back",
        "fr": "CON {name}:\n1. Voir code d'invitation\n2. Enregistrer contribution\n0. Retour",
    },
    "invite": {
        "en": "END Invite code: {code}\nShare this code or scan the QR in the app.",
        "fr": "END Code d'invitation: {code}\nPartagez ce code.",
    },
    "join_prompt": {
        "en": "CON Enter Stokvel invite code:",
        "fr": "CON Entrez le code d'invitation:",
    },
    "join_ok": {
        "en": "END Joined '{name}'.",
        "fr": "END Rejoint '{name}'.",
    },
    "join_fail": {
        "en": "END Could not join: {reason}",
        "fr": "END Echec: {reason}",
    },
    "contribute_ok": {
        "en": "END Contribution of R{amount} recorded for {name}.",
        "fr": "END Contribution de R{amount} enregistree pour {name}.",
    },
    "coach": {
        "en": "END SmartMoney: {msg}",
        "fr": "END SmartMoney: {msg}",
    },
    "language_menu": {
        "en": "CON Choose language:\n1. English\n2. isiZulu\n3. isiXhosa\n4. Sesotho\n5. Setswana\n6. Afrikaans\n7. Kiswahili\n8. Francais",
        "zu": "CON Khetha ulimi:\n1. English\n2. isiZulu\n3. isiXhosa\n4. Sesotho\n5. Setswana\n6. Afrikaans\n7. Kiswahili\n8. French",
    },
    "thanks": {
        "en": "END Thank you. Dial *141*8# to return.",
        "fr": "END Merci. Composez *141*8# pour revenir.",
    },
    "scam": {
        "en": "Never share your PIN. MTN will never ask for money. If unsure, hang up and call 135.",
        "fr": "Ne partagez jamais votre PIN. MTN ne demande jamais d'argent. En cas de doute, appelez le 135.",
    },
    "budget": {
        "en": "Track every R10 spent. Use SmartMoney categories in the app to see where money goes.",
        "fr": "Suivez chaque R10 depense. Utilisez les categories SmartMoney dans l'app.",
    },
    "save": {
        "en": "Try the 50/30/20 rule: 50% needs, 30% wants, 20% savings.",
        "fr": "Essayez la regle 50/30/20: 50% besoins, 30% envies, 20% epargne.",
    },
    "stokvel_tip": {
        "en": "Stokvels grow wealth together. Open the app to manage your group.",
        "fr": "Les tontines font croitre la richesse ensemble.",
    },
}

LANG_CODES = ["en", "zu", "xh", "st", "tn", "af", "sw", "fr"]


def t(key: str, lang: str = "en", **kwargs) -> str:
    bundle = T.get(key) or {}
    template = bundle.get(lang) or bundle.get("en") or key
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template


def scam_risk(amount: float) -> str:
    if amount >= 5000:
        return "HIGH"
    if amount >= 1500:
        return "MEDIUM"
    return "LOW"


# ---------------------------------------------------------------------------
# Async DB helpers
# ---------------------------------------------------------------------------

async def _find_user_by_phone(phone: str, db: AsyncSession):
    from app.models.models import UserDirectory
    res = await db.execute(select(UserDirectory).where(UserDirectory.phone_number == phone))
    entry = res.scalar_one_or_none()
    if not entry:
        return None
    u = await db.execute(select(User).where(User.id == entry.user_id))
    return u.scalar_one_or_none()


async def _get_wallet(user: User, db: AsyncSession) -> Wallet | None:
    res = await db.execute(select(Wallet).where(Wallet.user_id == user.id))
    return res.scalar_one_or_none()


async def _list_stokvels(user: User, db: AsyncSession) -> list[Stokvel]:
    res = await db.execute(
        select(Stokvel)
        .join(StokvelMember)
        .where(StokvelMember.user_id == user.id)
        .order_by(Stokvel.created_at.desc())
    )
    return list(res.scalars().all())


# ---------------------------------------------------------------------------
# Main USSD callback
# ---------------------------------------------------------------------------

@router.post("/callback", response_class=PlainTextResponse)
async def ussd_callback(
    sessionId: str = Form(...),
    phoneNumber: str = Form(...),
    text: str = Form(""),
    serviceCode: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    # Normalise the MSISDN the gateway gave us
    msisdn = "".join(ch for ch in phoneNumber if ch.isdigit())
    if msisdn.startswith("0"):
        msisdn = "27" + msisdn[1:]

    parts = text.split("*") if text else []
    state = sessions.setdefault(sessionId, {"lang": "en", "state": None, "msisdn": msisdn})
    lang = state.get("lang", "en")

    user = await _find_user_by_phone(msisdn, db)
    wallet = await _get_wallet(user, db) if user else None
    stokvels = await _list_stokvels(user, db) if user else []

    # -------- Welcome --------
    if text == "":
        banner = t("welcome", lang)
        if not user:
            return f"CON {banner}\n{t('not_registered', lang)}\n\n{t('main', lang)}"
        return f"CON {banner}\nHi {user.name}\n\n{t('main', lang)}"

    # -------- Language --------
    if parts[0] == "8":
        if len(parts) == 1:
            return f"CON {t('language_menu', lang)}"
        choice = parts[1]
        if choice.isdigit() and 1 <= int(choice) <= len(LANG_CODES):
            state["lang"] = LANG_CODES[int(choice) - 1]
            lang = state["lang"]
        return f"CON {t('welcome', lang)}\n\n{t('main', lang)}"

    # -------- Balance --------
    if parts[0] == "1":
        if not user:
            return f"END {t('not_registered', lang)}"
        bal = wallet.balance if wallet else 0
        provider = (wallet.provider if wallet else "momo") or "momo"
        return f"END {t('balance', lang, balance=bal, provider=provider)}"

    # -------- Send money --------
    if parts[0] == "2":
        if not user:
            return f"END {t('not_registered', lang)}"
        if len(parts) == 1:
            return f"CON {t('send_prompt', lang)}"
        if len(parts) == 2:
            state["send_phone"] = parts[1]
            return f"CON {t('amount_prompt', lang)}"
        if len(parts) == 3:
            try:
                amount = float(parts[2])
            except ValueError:
                return f"END Invalid amount"
            state["send_amount"] = amount
            return f"CON {t('confirm_send', lang, amount=amount, phone=parts[1], risk=scam_risk(amount))}"
        if len(parts) == 4 and parts[3] == "1":
            from app.models.models import UserDirectory
            recipient = parts[1]
            if recipient.startswith("0"):
                recipient = "27" + recipient[1:]
            try:
                amount = float(parts[2])
            except ValueError:
                return f"END Invalid amount"

            # Find recipient
            r = await db.execute(select(UserDirectory).where(UserDirectory.phone_number == recipient))
            entry = r.scalar_one_or_none()
            if not entry or not wallet or wallet.balance < amount:
                return f"END {t('send_fail', lang, reason='Recipient not a SmartMoney user or insufficient balance.')}"

            # Update balances
            import uuid as _uuid
            ref = str(_uuid.uuid4())[:8].upper()
            wallet.balance -= amount

            rw = await db.execute(select(Wallet).where(Wallet.user_id == entry.user_id))
            recipient_wallet = rw.scalar_one_or_none()
            if recipient_wallet is None:
                recipient_wallet = Wallet(user_id=entry.user_id, balance=0.0)
                db.add(recipient_wallet)
                await db.flush()
            recipient_wallet.balance += amount

            db.add_all([
                WalletTransaction(
                    wallet_id=wallet.id, type=WalletTransactionType.TRANSFER_OUT,
                    amount=amount, currency=wallet.currency,
                    status=WalletTransactionStatus.SUCCESSFUL,
                    counterparty_phone=recipient, counterparty_name=entry.display_name,
                    note="USSD P2P send", reference=ref, source="p2p",
                ),
                WalletTransaction(
                    wallet_id=recipient_wallet.id, type=WalletTransactionType.TRANSFER_IN,
                    amount=amount, currency=recipient_wallet.currency,
                    status=WalletTransactionStatus.SUCCESSFUL,
                    counterparty_phone=msisdn, counterparty_name=user.name,
                    note="USSD P2P receive", reference=ref, source="p2p",
                ),
            ])
            await db.commit()
            return f"END {t('send_ok', lang, balance=wallet.balance, ref=ref)}"
        return f"END {t('send_fail', lang, reason='Cancelled.')}"

    # -------- Receive (request) --------
    if parts[0] == "3":
        if not user:
            return f"END {t('not_registered', lang)}"
        if len(parts) == 1:
            return "CON Enter amount to request (Rands):"
        try:
            amount = float(parts[1])
        except ValueError:
            return "END Invalid amount"
        import secrets, string
        alphabet = string.ascii_uppercase + string.digits
        code = "".join(secrets.choice(alphabet) for _ in range(8))
        inv = PaymentRequestInvitePlaceholder(code=code, amount=amount, requester_id=user.id)
        # In real flow we'd insert; here we just return the code so the user can
        # share it. (Persisting via PaymentRequest model requires wallet import.)
        try:
            from app.models.models import PaymentRequest, PaymentRequestStatus
            pr = PaymentRequest(
                requester_id=user.id, amount=amount, currency="ZAR",
                payee_name=user.name, payee_phone=msisdn,
                status=PaymentRequestStatus.OPEN, code=code,
            )
            db.add(pr)
            await db.commit()
        except Exception:
            # Non-fatal: the user still gets a code to share verbally.
            pass
        return f"END Your request code: {code}\nShare it or show the QR from the app."

    # -------- My Stokvels --------
    if parts[0] == "4":
        if not user:
            return f"END {t('not_registered', lang)}"
        if not stokvels:
            return f"END {t('no_stokvels', lang)}"
        if len(parts) == 1:
            lines = "\n".join(f"{i+1}. {s.name} (R{s.contribution_amount})" for i, s in enumerate(stokvels[:5]))
            return f"CON {t('stokvel_list', lang, lines=lines)}"
        idx = int(parts[1]) - 1
        if 0 <= idx < len(stokvels):
            s = stokvels[idx]
            return f"CON {t('stokvel_action', lang, name=s.name)}"
        return t("thanks", lang)

    # Stokvel submenu
    if parts[0] == "4" and len(parts) >= 3:
        idx = int(parts[1]) - 1
        if 0 <= idx < len(stokvels):
            s = stokvels[idx]
            if parts[2] == "1":
                # Return the most recent active invite code, or create one
                inv = await db.execute(
                    select(StokvelInvite)
                    .where(StokvelInvite.stokvel_id == s.id, StokvelInvite.is_active == True)
                    .order_by(StokvelInvite.created_at.desc())
                )
                invite = inv.scalar_one_or_none()
                if not invite:
                    import secrets, string
                    alphabet = string.ascii_uppercase + string.digits
                    for _ in range(5):
                        candidate = "".join(secrets.choice(alphabet) for _ in range(6))
                        exists = await db.execute(select(StokvelInvite).where(StokvelInvite.code == candidate))
                        if not exists.scalar_one_or_none():
                            invite = StokvelInvite(
                                stokvel_id=s.id, code=candidate, created_by=user.id, is_active=True
                            )
                            db.add(invite)
                            await db.commit()
                            await db.refresh(invite)
                            break
                if invite:
                    return f"END {t('invite', lang, code=invite.code)}"
                return f"END Could not create invite"
            if parts[2] == "2":
                m = await db.execute(
                    select(StokvelMember).where(
                        StokvelMember.stokvel_id == s.id, StokvelMember.user_id == user.id
                    )
                )
                member = m.scalar_one_or_none()
                if not member:
                    return f"END {t('join_fail', lang, reason='Not a member')}"
                member.total_contributed += s.contribution_amount
                await db.commit()
                return f"END {t('contribute_ok', lang, amount=s.contribution_amount, name=s.name)}"
        return t("thanks", lang)

    # -------- Join Stokvel by code --------
    if parts[0] == "5":
        if not user:
            return f"END {t('not_registered', lang)}"
        if len(parts) == 1:
            return f"CON {t('join_prompt', lang)}"
        code = parts[1].strip().upper()
        if code.startswith("STOKVEL://INVITE/"):
            code = code.split("/")[-1]
        inv = await db.execute(select(StokvelInvite).where(StokvelInvite.code == code))
        invite = inv.scalar_one_or_none()
        if not invite or not invite.is_active:
            return f"END {t('join_fail', lang, reason='Invalid code')}"
        # MTN rule: joiner must be MTN
        prefixes = ["083", "081", "082", "084", "078", "079"]
        if not is_mtn_number(user.phone_number, prefixes, "27"):
            return f"END {t('join_fail', lang, reason='Your number is not MTN')}"
        existing = await db.execute(
            select(StokvelMember).where(
                StokvelMember.stokvel_id == invite.stokvel_id,
                StokvelMember.user_id == user.id,
            )
        )
        if existing.scalar_one_or_none():
            return f"END {t('join_fail', lang, reason='Already a member')}"
        s = await db.execute(select(Stokvel).where(Stokvel.id == invite.stokvel_id))
        stokvel = s.scalar_one()
        db.add(StokvelMember(stokvel_id=stokvel.id, user_id=user.id, role="member"))
        invite.uses += 1
        await db.commit()
        return f"END {t('join_ok', lang, name=stokvel.name)}"

    # -------- Contribute directly (no Stokvel picker) --------
    if parts[0] == "6":
        if not user or not stokvels:
            return f"END {t('no_stokvels', lang)}"
        if len(parts) == 1:
            lines = "\n".join(f"{i+1}. {s.name}" for i, s in enumerate(stokvels[:5]))
            return f"CON Pick a Stokvel to contribute to:\n{lines}\n0. Back"
        idx = int(parts[1]) - 1
        if 0 <= idx < len(stokvels):
            s = stokvels[idx]
            m = await db.execute(
                select(StokvelMember).where(
                    StokvelMember.stokvel_id == s.id, StokvelMember.user_id == user.id
                )
            )
            member = m.scalar_one_or_none()
            if not member:
                return f"END {t('join_fail', lang, reason='Not a member')}"
            member.total_contributed += s.contribution_amount
            await db.commit()
            return f"END {t('contribute_ok', lang, amount=s.contribution_amount, name=s.name)}"
        return t("thanks", lang)

    # -------- Talk to Coach --------
    if parts[0] == "7":
        if len(parts) == 1:
            return "CON Ask SmartMoney (saving, budget, scam, stokvel):"
        q = " ".join(parts[1:]).lower()
        if any(w in q for w in ["scam", "fraud"]):
            return f"END {t('coach', lang, msg=t('scam', lang))}"
        if any(w in q for w in ["save", "saving", "epargn"]):
            return f"END {t('coach', lang, msg=t('save', lang))}"
        if any(w in q for w in ["budget", "spend", "depen"]):
            return f"END {t('coach', lang, msg=t('budget', lang))}"
        if any(w in q for w in ["stokvel", "tontin", "group"]):
            return f"END {t('coach', lang, msg=t('stokvel_tip', lang))}"
        return f"END {t('coach', lang, msg=t('budget', lang))}"

    return f"END {t('thanks', lang)}"


# Tiny local placeholder so the import above is not dead code; the real
# PaymentRequest row is created via the try/except block.
class PaymentRequestInvitePlaceholder:
    def __init__(self, code: str, amount: float, requester_id: str):
        self.code = code
        self.amount = amount
        self.requester_id = requester_id