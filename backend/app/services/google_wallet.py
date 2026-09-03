"""Google Wallet "Add to Google Wallet" save links.

A save link is NOT a URL you can assemble from ids. It is
`https://pay.google.com/gp/v/save/<JWT>` where <JWT> is a **path segment**
holding a JSON Web Token signed with a Google Cloud service account key.
Anything else - a `?token=` query parameter, or ids concatenated together -
gets a 404 from pay.google.com, because there is no signature for Google to
verify and nothing identifying you as the issuer.

The JWT carries the pass itself. We inline both `genericClasses` and
`genericObjects` in the payload, so Google creates the class on first save and
we never need a separate REST call against the Wallet API.

Setup required before this works:
  1. Google Pay & Wallet Console -> get your **issuer ID** (a ~20-digit number).
  2. Google Cloud -> enable the Google Wallet API, create a **service account**,
     download its JSON key.
  3. In the Wallet Console, authorise that service account email as an issuer user.
  4. Set GOOGLE_WALLET_ISSUER_ID and GOOGLE_WALLET_SERVICE_ACCOUNT_JSON.

Docs: https://developers.google.com/wallet/generic/web
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

SAVE_URL_PREFIX = "https://pay.google.com/gp/v/save/"

# Google truncates long links in some browsers; the documented safe ceiling for
# an encoded JWT is 1800 characters. Keep the pass lean and check before
# handing the URL out, rather than shipping a link that silently fails.
MAX_JWT_LENGTH = 1800


class GoogleWalletNotConfigured(RuntimeError):
    """Raised when issuer id or service-account credentials are missing."""


def _load_service_account(raw: str) -> dict[str, Any]:
    """Accept the service-account key as raw JSON or as a path to a file.

    Render environment variables hold the JSON directly; local development is
    easier with a file path. Supporting both avoids a deploy-only failure mode.
    """
    raw = raw.strip()
    if raw.startswith("{"):
        return json.loads(raw)
    with open(raw, "r", encoding="utf-8") as fh:
        return json.load(fh)


def build_generic_class(issuer_id: str, class_suffix: str) -> dict[str, Any]:
    """A minimal class.

    Deliberately just the id. A `classTemplateInfo` override pushed the encoded
    JWT to ~1840 characters, past the 1800-char ceiling Google documents for
    save links - and an over-long link fails by being silently truncated, which
    is the worst kind of bug to chase. Google lays out `textModulesData`
    sensibly by default, so the override bought nothing worth that risk.

    If you later want a custom card layout, create the class once via the Wallet
    REST API and keep referencing it by `classId` here - the template then lives
    server-side at Google and costs the JWT nothing.
    """
    return {"id": f"{issuer_id}.{class_suffix}"}


def build_generic_object(
    *,
    issuer_id: str,
    class_suffix: str,
    object_suffix: str,
    holder_name: str,
    phone_number: str,
    balance: float,
    currency: str,
    card_title: str,
) -> dict[str, Any]:
    return {
        "id": f"{issuer_id}.{object_suffix}",
        "classId": f"{issuer_id}.{class_suffix}",
        "state": "ACTIVE",
        "cardTitle": {
            "defaultValue": {"language": "en-US", "value": card_title}
        },
        "header": {
            "defaultValue": {"language": "en-US", "value": holder_name}
        },
        "hexBackgroundColor": "#FFCC00",
        "textModulesData": [
            {
                "id": "balance",
                "header": "Balance",
                "body": f"{currency} {balance:,.2f}",
            },
            {
                "id": "phone",
                "header": "MoMo number",
                "body": phone_number,
            },
        ],
        # The barcode is what a POS or agent actually scans. Encoding the
        # phone number keeps it meaningful offline, which matters for the
        # USSD-first users this card is aimed at.
        "barcode": {
            "type": "QR_CODE",
            "value": phone_number,
            "alternateText": phone_number,
        },
    }


def create_save_url(
    *,
    issuer_id: str,
    service_account_json: str,
    origins: list[str],
    class_suffix: str,
    object_suffix: str,
    holder_name: str,
    phone_number: str,
    balance: float,
    currency: str,
    card_title: str,
) -> str:
    """Return a signed "Add to Google Wallet" URL.

    Raises GoogleWalletNotConfigured when credentials are absent, so the caller
    can answer with a clear 503 instead of handing the browser a dead link.
    """
    if not issuer_id or not service_account_json:
        raise GoogleWalletNotConfigured(
            "GOOGLE_WALLET_ISSUER_ID and GOOGLE_WALLET_SERVICE_ACCOUNT_JSON "
            "must be set to issue Google Wallet passes."
        )

    # Imported lazily so the rest of the wallet API keeps working on a
    # deployment that never installed the Google auth libraries.
    from google.auth import crypt, jwt as google_jwt

    key = _load_service_account(service_account_json)
    signer = crypt.RSASigner.from_service_account_info(key)

    claims = {
        "iss": key["client_email"],
        "aud": "google",
        "typ": "savetowallet",
        "origins": origins,
        "payload": {
            "genericClasses": [build_generic_class(issuer_id, class_suffix)],
            "genericObjects": [
                build_generic_object(
                    issuer_id=issuer_id,
                    class_suffix=class_suffix,
                    object_suffix=object_suffix,
                    holder_name=holder_name,
                    phone_number=phone_number,
                    balance=balance,
                    currency=currency,
                    card_title=card_title,
                )
            ],
        },
    }

    token = google_jwt.encode(signer, claims).decode("utf-8")

    if len(token) > MAX_JWT_LENGTH:
        logger.warning(
            "Google Wallet JWT is %d chars, above the %d-char safe limit; "
            "the save link may be truncated by the browser.",
            len(token),
            MAX_JWT_LENGTH,
        )

    return SAVE_URL_PREFIX + token
