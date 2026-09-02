"""MTN MoMo API Integration Service (Production MTN South Africa)."""
import uuid
import base64
import httpx
from fastapi import HTTPException
from app.config import get_settings

settings = get_settings()

BASE_URL = settings.momo_api_base_url
TARGET_ENV = settings.momo_target_environment or settings.momo_environment


def _format_msisdn(phone_number: str) -> str:
    msisdn = phone_number.replace("+", "").strip()
    if msisdn.startswith("0"):
        msisdn = "27" + msisdn[1:]
    return msisdn


class MoMoClient:
    def __init__(self):
        self.collection_key = settings.momo_collection_primary_key
        self.disbursement_key = settings.momo_disbursement_primary_key
        self.api_user = settings.momo_api_user
        self.api_key = settings.momo_api_key
        self.environment = TARGET_ENV
        self._token_cache: dict[str, str] = {}

    async def _get_token(self, product: str = "collection") -> str:
        """Step 1: Get OAuth token via Basic Auth."""
        if product in self._token_cache:
            return self._token_cache[product]

        sub_key = self.collection_key if product == "collection" else self.disbursement_key
        url = f"{BASE_URL}/token/"

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                headers={
                    "Ocp-Apim-Subscription-Key": sub_key,
                    "X-Target-Environment": self.environment,
                    "Authorization": f"Basic {base64.b64encode(f'{self.api_user}:{self.api_key}'.encode()).decode()}",
                },
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"MoMo Token Error: {response.text}",
                )
            token = response.json()["access_token"]
            self._token_cache[product] = token
            return token

    async def request_to_pay(
        self, amount: float, phone_number: str, currency: str = "ZAR",
        payer_message: str = "MoMo SmartMoney",
    ) -> dict:
        """Step 2: Initiate Request to Pay (expects 202 Accepted)."""
        token = await self._get_token("collection")
        reference_id = str(uuid.uuid4())
        msisdn = _format_msisdn(phone_number)

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Reference-Id": reference_id,
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.collection_key,
            "Content-Type": "application/json",
        }

        amount_str = str(int(amount) if float(amount).is_integer() else amount)
        payload = {
            "amount": amount_str,
            "currency": currency,
            "externalId": str(uuid.uuid4().int)[:8],
            "payer": {"partyIdType": "MSISDN", "partyId": msisdn},
            "payerMessage": payer_message,
            "payeeNote": payer_message,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{BASE_URL}/v1_0/requesttopay",
                json=payload,
                headers=headers,
            )
            if response.status_code != 202:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"MoMo RequestToPay Error: {response.text}",
                )
            return {"reference_id": reference_id, "status": "PENDING"}

    async def check_payment_status(self, reference_id: str) -> dict:
        """Step 3: Check transaction status."""
        token = await self._get_token("collection")
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.collection_key,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{BASE_URL}/v1_0/requesttopay/{reference_id}",
                headers=headers,
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"MoMo Status Error: {response.text}",
                )
            return response.json()

    async def transfer(
        self, amount: float, phone_number: str, currency: str = "ZAR", payee_note: str = ""
    ) -> dict:
        """Disbursement API: send money to a user."""
        token = await self._get_token("disbursement")
        reference_id = str(uuid.uuid4())
        msisdn = _format_msisdn(phone_number)

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Reference-Id": reference_id,
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.disbursement_key,
            "Content-Type": "application/json",
        }

        payload = {
            "amount": str(int(float(amount)) if float(amount).is_integer() else amount),
            "currency": currency,
            "externalId": reference_id,
            "payee": {"partyIdType": "MSISDN", "partyId": msisdn},
            "payerMessage": "MoMo SmartMoney AI",
            "payeeNote": payee_note or "SmartMoney transfer",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{BASE_URL.replace('/collection', '/disbursement')}/v1_0/transfer",
                json=payload,
                headers=headers,
            )
            return {
                "reference_id": reference_id,
                "status_code": response.status_code,
                "success": response.status_code == 202,
            }

    async def get_balance(self) -> dict:
        token = await self._get_token("collection")
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.collection_key,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{BASE_URL}/v1_0/account/balance",
                headers=headers,
            )
            if response.status_code == 200:
                return response.json()
            return {"availableBalance": "0", "currency": "ZAR"}

    async def validate_account(self, phone_number: str) -> bool:
        msisdn = _format_msisdn(phone_number)
        token = await self._get_token("collection")
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.collection_key,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{BASE_URL}/v1_0/accountholder/msisdn/{msisdn}/active",
                headers=headers,
            )
            return response.status_code == 200


# Singleton
momo_client = MoMoClient()
