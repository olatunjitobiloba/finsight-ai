"""Safetoken OTP routes using Interswitch Marketplace API."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services import generate_otp, verify_otp

router = APIRouter(prefix="/api/otp", tags=["otp"])


# Request Models
class GenerateOTPRequest(BaseModel):
    """Request to generate a new OTP."""
    token_id: str = Field(..., min_length=1, description="Token ID or account identifier")


class VerifyOTPRequest(BaseModel):
    """Request to verify an OTP code."""
    token_id: str = Field(..., min_length=1, description="Token ID for which OTP was generated")
    otp: str = Field(..., min_length=1, max_length=10, description="OTP code to verify")


# Routes
@router.post("/generate")
async def generate_otp_code(req: GenerateOTPRequest):
    """
    Generate a new Safetoken OTP for a given token ID.
    
    Args:
        token_id: The unique identifier (token ID) to generate OTP for
    
    Returns:
        OTP code and delivery information if successful.
    """
    try:
        result = generate_otp(req.token_id)
        
        if result.get("status") == "success":
            return {
                "status": "success",
                "message": "OTP generated and sent successfully",
                "data": result.get("data", {})
            }
        
        return {
            "status": "error",
            "message": result.get("message", "Failed to generate OTP"),
            "error_code": result.get("error_code"),
            "details": result.get("details")
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OTP generation failed: {str(e)}"
        )


@router.post("/verify")
async def verify_otp_code(req: VerifyOTPRequest):
    """
    Verify an OTP code for a given token ID.
    
    Args:
        token_id: The token ID for which OTP was generated
        otp: The OTP code to verify
    
    Returns:
        Verification result with status and any additional data.
    """
    try:
        result = verify_otp(req.token_id, req.otp)
        
        if result.get("status") == "success":
            return {
                "status": "success",
                "message": "OTP verified successfully",
                "verified": True,
                "data": result.get("data", {})
            }
        
        # Verification failed (wrong code, expired, etc)
        if result.get("status") == "failed":
            return {
                "status": "failed",
                "message": result.get("message", "OTP verification failed"),
                "verified": False,
                "error_code": result.get("error_code"),
                "details": result.get("details")
            }
        
        # Unexpected error
        return {
            "status": "error",
            "message": result.get("message", "Verification request failed"),
            "error_code": result.get("error_code"),
            "details": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OTP verification failed: {str(e)}"
        )
