# api/routes/auth.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client
import os

router  = APIRouter()
supabase = create_client(
    os.getenv("SUPABASE_URL",""),
    os.getenv("SUPABASE_KEY","")
)

class GoogleAuthRequest(BaseModel):
    id_token: str  # from Google Sign-In on frontend

@router.post("/api/auth/google")
def google_auth(req: GoogleAuthRequest):
    try:
        result = supabase.auth.sign_in_with_id_token({
            "provider": "google",
            "token":    req.id_token
        })
        return {
            "user_id":      result.user.id,
            "email":        result.user.email,
            "access_token": result.session.access_token
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

class BankSetupRequest(BaseModel):
    user_id:        str
    bank_name:      str
    account_number: str
    bvn_last4:      str  # partial BVN for verification only

@router.post("/api/auth/bank-setup")
def bank_setup(req: BankSetupRequest):
    """
    Store user's bank details for Interswitch actions.
    We store account number — NOT BVN, NOT password.
    """
    try:
        supabase.table("user_bank_profiles").upsert({
            "user_id":        req.user_id,
            "bank_name":      req.bank_name,
            "account_number": req.account_number,
        }).execute()
        return {"success": True, "message": "Bank account linked."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
