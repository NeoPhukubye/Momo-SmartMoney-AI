"""MTN South Africa MoMo Collection API Integration.

3-step lifecycle:
  1. get_access_token()         - OAuth token via Basic Auth
  2. initiate_request_to_pay()  - Request to Pay (202 Accepted)
  3. get_payment_status()       - Poll / Verify transaction status
"""
import os
import uuid
import base64
import httpx
from fastapi import HTTPException

MOMO_BASE_URL = os.getenv("MOMO_BASE_URL", "https://proxy.momoapi.mtn.com/collection")
MOMO_SUB_KEY = os.getenv("MOMO_COLLECTION_PRIMARY_KEY")
MOMO_API_USER = os.getenv("MOMO_API_USER")
MOMO_API_KEY = os.getenv("MOMO_API_KEY")
MOMO_TARGET_ENV = os.getenv("MOMO_TARGET_ENVIRONMENT", "mtnsouthafrica")


async def get_access_token() -> str:
    """Step 1: Generate Access Token using Basic Auth."""
    credentials = f"{MOMO_API_USER}:{MOMO_API_KEY}"
    encoded_creds = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Ocp-Apim-Subscription-Key": MOMO_SUB_KEY,
        "X-Target-Environment": MOMO_TARGET_ENV,
        "Authorization": f"Basic {encoded_creds}",
        "Content-Length": "0",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(f"{MOMO_BASE_URL}/token/", headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"Token Generation Error: {resp.text}")
        return resp.json()["access_token"]


async def initiate_request_to_pay(amount: float, phone: str, external_id: str = None, note: str = "MoMo Payment") -> str:
    """Step 2: Initiate Request to Pay (202 Accepted)."""
    token = await get_access_token()
    reference_id = str(uuid.uuid4())

    # Format phone to MSISDN without leading + (e.g., 27788033288)
    msisdn = phone.replace("+", "").strip()
    if msisdn.startswith("0"):
        msisdn = "27" + msisdn[1:]

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Reference-Id": reference_id,
        "X-Target-Environment": MOMO_TARGET_ENV,
        "Ocp-Apim-Subscription-Key": MOMO_SUB_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "amount": str(int(amount) if amount.is_integer() else amount),
        "currency": "ZAR",
        "externalId": external_id or str(uuid.uuid4().int)[:8],
        "payer": {
            "partyIdType": "MSISDN",
            "partyId": msisdn
        },
        "payerMessage": note,
        "payeeNote": note
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(f"{MOMO_BASE_URL}/v1_0/requesttopay", headers=headers, json=payload)
        if resp.status_code != 202:
            raise HTTPException(status_code=resp.status_code, detail=f"Payment Request Error: {resp.text}")
        return reference_id


async def get_payment_status(reference_id: str) -> dict:
    """Step 3: Poll / Verify Transaction Status."""
    token = await get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Target-Environment": MOMO_TARGET_ENV,
        "Ocp-Apim-Subscription-Key": MOMO_SUB_KEY,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{MOMO_BASE_URL}/v1_0/requesttopay/{reference_id}", headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"Status Check Error: {resp.text}")
        return resp.json()
