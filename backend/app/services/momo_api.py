"""MTN MoMo API Integration Service (Sandbox + Production)"""
import uuid
import httpx
from app.config import get_settings

settings = get_settings()

BASE_URL = settings.momo_api_base_url


class MoMoClient:
    def __init__(self):
        self.collection_key = settings.momo_collection_primary_key
        self.disbursement_key = settings.momo_disbursement_primary_key
        self.api_user = settings.momo_api_user
        self.api_key = settings.momo_api_key
        self.environment = settings.momo_environment
        self._token_cache: dict[str, str] = {}

    async def _get_token(self, product: str = "collection") -> str:
        """Get OAuth token for MoMo API."""
        if product in self._token_cache:
            return self._token_cache[product]

        sub_key = self.collection_key if product == "collection" else self.disbursement_key
        url = f"{BASE_URL}/{product}/token/"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                auth=(self.api_user, self.api_key),
                headers={"Ocp-Apim-Subscription-Key": sub_key},
            )
            response.raise_for_status()
            token = response.json()["access_token"]
            self._token_cache[product] = token
            return token

    async def request_to_pay(
        self, amount: float, phone_number: str, currency: str = "ZAR", payer_message: str = ""
    ) -> dict:
        """Request payment from a user (Collection API)."""
        token = await self._get_token("collection")
        reference_id = str(uuid.uuid4())

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Reference-Id": reference_id,
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.collection_key,
            "Content-Type": "application/json",
        }

        payload = {
            "amount": str(amount),
            "currency": currency,
            "externalId": reference_id,
            "payer": {"partyIdType": "MSISDN", "partyId": phone_number},
            "payerMessage": payer_message or "SmartMoney payment",
            "payeeNote": "MoMo SmartMoney AI",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/collection/v1_0/requesttopay",
                json=payload,
                headers=headers,
            )
            return {
                "reference_id": reference_id,
                "status_code": response.status_code,
                "success": response.status_code == 202,
            }

    async def check_payment_status(self, reference_id: str) -> dict:
        """Check status of a payment request."""
        token = await self._get_token("collection")

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.collection_key,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/collection/v1_0/requesttopay/{reference_id}",
                headers=headers,
            )
            if response.status_code == 200:
                return response.json()
            return {"status": "FAILED", "reason": f"HTTP {response.status_code}"}

    async def transfer(
        self, amount: float, phone_number: str, currency: str = "ZAR", payee_note: str = ""
    ) -> dict:
        """Send money to a user (Disbursement API)."""
        token = await self._get_token("disbursement")
        reference_id = str(uuid.uuid4())

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Reference-Id": reference_id,
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.disbursement_key,
            "Content-Type": "application/json",
        }

        payload = {
            "amount": str(amount),
            "currency": currency,
            "externalId": reference_id,
            "payee": {"partyIdType": "MSISDN", "partyId": phone_number},
            "payerMessage": "MoMo SmartMoney AI",
            "payeeNote": payee_note or "SmartMoney transfer",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/disbursement/v1_0/transfer",
                json=payload,
                headers=headers,
            )
            return {
                "reference_id": reference_id,
                "status_code": response.status_code,
                "success": response.status_code == 202,
            }

    async def get_balance(self) -> dict:
        """Get account balance."""
        token = await self._get_token("collection")
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.collection_key,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/collection/v1_0/account/balance",
                headers=headers,
            )
            if response.status_code == 200:
                return response.json()
            return {"availableBalance": "0", "currency": "ZAR"}

    async def validate_account(self, phone_number: str) -> bool:
        """Check if a phone number is registered on MoMo."""
        token = await self._get_token("collection")
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.collection_key,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/collection/v1_0/accountholder/msisdn/{phone_number}/active",
                headers=headers,
            )
            return response.status_code == 200


# Singleton
momo_client = MoMoClient()
