"""Bank account verification routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.interswitch import get_bank_list, verify_bank_account

router = APIRouter(prefix="/api/bank-verify", tags=["bank-verify"])


class BankVerifyRequest(BaseModel):
    account_number: str
    bank_code: str


@router.get("/banks")
async def list_banks():
    """Get list of all Nigerian banks."""
    result = get_bank_list()
    if result.get("status") == "success":
        return {
            "status": "success",
            "data": result.get("banks", [])
        }
    return {
        "status": "error",
        "message": result.get("message", "Failed to fetch banks")
    }


@router.post("/verify")
async def verify_account(req: BankVerifyRequest):
    """Verify account number and get account name."""
    if not req.account_number or not req.bank_code:
        raise HTTPException(status_code=400, detail="account_number and bank_code required")
    
    result = verify_bank_account(req.account_number, req.bank_code)
    
    if result.get("status") == "success":
        return {
            "status": "success",
            "account_name": result.get("account_name", ""),
            "account_number": req.account_number,
            "bank_code": req.bank_code,
        }
    
    response = {
        "status": "error",
        "message": result.get("message", "Verification failed")
    }
    if result.get("provider_code"):
        response["provider_code"] = result.get("provider_code")
    if result.get("log_id"):
        response["log_id"] = result.get("log_id")
    return response
