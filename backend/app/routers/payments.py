from fastapi import APIRouter
from pydantic import BaseModel
from app.services.momo import initiate_request_to_pay, get_payment_status

router = APIRouter(prefix="/api/payments", tags=["MoMo Payments"])


class PayRequest(BaseModel):
    amount: float
    phone: str
    note: str = "MoMo SmartMoney Deposit"


@router.post("/collect")
async def collect_funds(data: PayRequest):
    ref_id = await initiate_request_to_pay(amount=data.amount, phone=data.phone, note=data.note)
    return {"status": "INITIATED", "reference_id": ref_id}


@router.get("/status/{reference_id}")
async def check_status(reference_id: str):
    return await get_payment_status(reference_id)
