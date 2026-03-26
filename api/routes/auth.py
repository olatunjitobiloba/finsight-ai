# api/routes/auth.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client
import os
import json
import base64

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL", "") or "https://sfmosgngefdnvmposqml.supabase.co"
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "") or os.getenv("SUPABASE_KEY", "")
RAW_PUBLIC_ANON_KEY = (
    os.getenv("SUPABASE_ANON_KEY", "")
    or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
)


def _is_anon_jwt(token: str) -> bool:
    """Return True only when token payload role is anon."""
    if not token or token.count(".") < 2:
        return False
    try:
        payload_part = token.split(".")[1]
        padding = "=" * (-len(payload_part) % 4)
        decoded = base64.urlsafe_b64decode((payload_part + padding).encode("utf-8"))
        payload = json.loads(decoded.decode("utf-8"))
        return str(payload.get("role", "")).lower() == "anon"
    except Exception:
        return False


SUPABASE_ANON_KEY = RAW_PUBLIC_ANON_KEY
if not SUPABASE_ANON_KEY:
    candidate = os.getenv("SUPABASE_KEY", "")
    if _is_anon_jwt(candidate):
        SUPABASE_ANON_KEY = candidate

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY) if (SUPABASE_URL and SUPABASE_SERVICE_KEY) else None


@router.get("/api/auth/public-config")
def auth_public_config():
    """
    Returns only browser-safe auth config values.
    This enables one-click Google sign-in from static frontend pages.
    """
    configured = bool(SUPABASE_URL and SUPABASE_ANON_KEY)
    return {
        "configured": configured,
        "supabase_url": SUPABASE_URL if configured else None,
        "supabase_anon_key": SUPABASE_ANON_KEY if configured else None,
    }

class GoogleAuthRequest(BaseModel):
    id_token: str  # from Google Sign-In on frontend

@router.post("/api/auth/google")
def google_auth(req: GoogleAuthRequest):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase backend client is not configured.")

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
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase backend client is not configured.")

    try:
        supabase.table("user_bank_profiles").upsert({
            "user_id":        req.user_id,
            "bank_name":      req.bank_name,
            "account_number": req.account_number,
        }).execute()
        return {"success": True, "message": "Bank account linked."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
