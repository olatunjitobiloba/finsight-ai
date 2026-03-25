"""Execution routes for Interswitch-backed financial actions."""

import os
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.interswitch import get_billers, get_payment_items, pay_bill

router = APIRouter(prefix="/api/execute", tags=["execute"])


class ExecutePaymentRequest(BaseModel):
    customer_id: str = Field(..., min_length=3)
    amount: float = Field(..., gt=0)
    payment_code: Optional[str] = None
    reference: Optional[str] = None


def _is_sandbox_pending(message: str) -> bool:
    text = (message or "").lower()
    return any(token in text for token in ["access denied", "permission", "entitle", "unauthorized"])


@router.post("/pay")
async def execute_fix_payment(request: ExecutePaymentRequest):
    """Execute a bill payment for an action with sandbox-pending fallback."""
    payment_code = (request.payment_code or os.getenv("INTERSWITCH_DEFAULT_PAYMENT_CODE", "")).strip()

    if not payment_code:
        return {
            "success": False,
            "status": "sandbox_pending",
            "message": "Sandbox pending: payment code is not available yet. Add entitlement and fetch paymentCode from /vas/billers/payment-item.",
        }

    result = pay_bill(
        customer_id=request.customer_id.strip(),
        payment_code=payment_code,
        amount_naira=float(request.amount),
        reference=request.reference,
    )

    if result.get("status") == "success":
        return {
            "success": True,
            "status": "success",
            "message": result.get("description", "Payment successful"),
            "reference": result.get("reference"),
            "amount": result.get("amount"),
            "provider": result.get("provider", "Interswitch"),
            "response_code": result.get("response_code"),
            "raw": result.get("raw", {}),
        }

    message = result.get("message", "Payment failed")
    if _is_sandbox_pending(message):
        return {
            "success": False,
            "status": "sandbox_pending",
            "message": "Sandbox pending: your app is not yet entitled for Marketplace Routing endpoints.",
            "provider_message": message,
            "reference": result.get("reference"),
        }

    return {
        "success": False,
        "status": "failed",
        "message": message,
        "reference": result.get("reference"),
    }


@router.get("/billers")
async def execute_billers():
    """Expose billers list for the execution flow."""
    result = get_billers()
    if result.get("status") == "success":
        return {"success": True, "data": result.get("data", [])}

    message = result.get("message", "Failed to fetch billers")
    if _is_sandbox_pending(message):
        return {
            "success": False,
            "status": "sandbox_pending",
            "message": "Sandbox pending: billers endpoint is not yet enabled for this app.",
            "provider_message": message,
        }

    return {"success": False, "status": "failed", "message": message}


@router.get("/payment-items")
async def execute_payment_items(biller_id: int):
    """Expose payment items list for a selected biller."""
    result = get_payment_items(biller_id)
    if result.get("status") == "success":
        return {"success": True, "data": result.get("data", [])}

    message = result.get("message", "Failed to fetch payment items")
    if _is_sandbox_pending(message):
        return {
            "success": False,
            "status": "sandbox_pending",
            "message": "Sandbox pending: payment-item endpoint is not yet enabled for this app.",
            "provider_message": message,
        }

    return {"success": False, "status": "failed", "message": message}
