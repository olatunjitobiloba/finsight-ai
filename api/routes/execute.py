"""Execution routes for Interswitch-backed financial actions."""

import os
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.interswitch import (
    BASE_URL,
    QUICKTELLER_URL,
    QUICKTELLER_V2_URL,
    TERMINAL_ID,
    TOKEN_URL,
    VERIFY_BASE_URL,
    get_billers,
    get_default_payment_code,
    get_payment_items,
    pay_bill,
    validate_customer,
)

router = APIRouter(prefix="/api/execute", tags=["execute"])


class ExecutePaymentRequest(BaseModel):
    customer_id: str = Field(..., min_length=3)
    amount: float = Field(..., gt=0)
    payment_code: Optional[str] = None
    reference: Optional[str] = None


class ValidateCustomerRequest(BaseModel):
    customer_id: str = Field(..., min_length=3)
    payment_code: str = Field(..., min_length=3)


def _is_sandbox_pending(message: str) -> bool:
    text = (message or "").lower()
    return any(token in text for token in [
        "access denied",
        "permission",
        "entitle",
        "unauthorized",
        "forbidden",
        "bad credentials",
        "invalid client",
        "terminal",
        "merchant",
    ])


def _host_of(url: str) -> str:
    return urlparse(str(url or "")).netloc


@router.post("/pay")
async def execute_fix_payment(request: ExecutePaymentRequest):
    """Execute a bill payment for an action with sandbox-pending fallback."""
    payment_code = (request.payment_code or get_default_payment_code() or os.getenv("INTERSWITCH_DEFAULT_PAYMENT_CODE", "")).strip()

    if not payment_code:
        return {
            "success": False,
            "status": "sandbox_pending",
            "message": "Sandbox pending: payment code is not available yet. Fetch paymentCode from /api/execute/payment-items after selecting a biller.",
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


@router.post("/validate")
async def execute_validate_customer(request: ValidateCustomerRequest):
    """Validate a customer id and payment code before payment advice."""
    result = validate_customer(
        customer_id=request.customer_id.strip(),
        payment_code=request.payment_code.strip(),
    )

    if result.get("status") == "success":
        return {
            "success": True,
            "status": "success",
            "customer_name": result.get("customer_name", ""),
            "amount": result.get("amount", 0),
            "amount_type": result.get("amount_type", ""),
            "response_code": result.get("response_code", ""),
            "raw": result.get("raw", {}),
        }

    message = result.get("message", "Validation failed")
    if _is_sandbox_pending(message):
        return {
            "success": False,
            "status": "sandbox_pending",
            "message": "Sandbox pending: customer validation endpoint is not yet enabled for this app.",
            "provider_message": message,
        }

    return {
        "success": False,
        "status": "failed",
        "message": message,
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

    response = {
        "success": False,
        "status": "failed",
        "message": message,
    }
    for key in [
        "request_id",
        "target_path",
        "error_type",
        "phase",
        "url_host",
        "status_code",
        "attempts",
        "retryable",
    ]:
        if key in result:
            response[key] = result.get(key)
    return response


@router.get("/env-check")
async def execute_env_check():
    """Safe env diagnostics for Interswitch integration troubleshooting."""
    client_id = (os.getenv("INTERSWITCH_CLIENT_ID") or os.getenv("INTERSWITCH_API_CLIENT_ID") or "").strip()
    client_secret = (
        os.getenv("INTERSWITCH_CLIENT_SECRET")
        or os.getenv("INTERSWITCH_SECRET_KEY")
        or os.getenv("INTERSWITCH_SECRET")
        or os.getenv("INTERSWITCH_API_SECRET")
        or ""
    ).strip()

    return {
        "success": True,
        "status": "ok",
        "env": {
            "token_url_host": _host_of(TOKEN_URL),
            "quickteller_v1_host": _host_of(QUICKTELLER_URL),
            "quickteller_v2_host": _host_of(QUICKTELLER_V2_URL),
            "verify_host": _host_of(VERIFY_BASE_URL),
            "base_url_host": _host_of(BASE_URL),
            "terminal_id": TERMINAL_ID,
            "client_id_present": bool(client_id),
            "client_secret_present": bool(client_secret),
            "default_payment_code_present": bool((get_default_payment_code() or "").strip()),
        },
    }


@router.get("/status")
async def execute_status():
    """Quick diagnostic endpoint for Interswitch credential/setup readiness."""
    client_id = (os.getenv("INTERSWITCH_CLIENT_ID") or "").strip()
    client_secret = (
        os.getenv("INTERSWITCH_CLIENT_SECRET")
        or os.getenv("INTERSWITCH_SECRET_KEY")
        or os.getenv("INTERSWITCH_SECRET")
        or ""
    ).strip()
    terminal_id = (os.getenv("INTERSWITCH_TERMINAL_ID") or "3DMO0001").strip()
    payment_code = (get_default_payment_code() or "").strip()

    checks = {
        "client_id_present": bool(client_id),
        "client_secret_present": bool(client_secret),
        "terminal_id_present": bool(terminal_id),
        "default_payment_code_present": bool(payment_code),
    }

    if not checks["client_id_present"] or not checks["client_secret_present"]:
        return {
            "success": False,
            "status": "misconfigured",
            "message": "Interswitch credentials are missing. Set INTERSWITCH_CLIENT_ID and INTERSWITCH_CLIENT_SECRET.",
            "checks": checks,
        }

    try:
        result = get_billers()
    except Exception as exc:
        return {
            "success": False,
            "status": "failed",
            "message": str(exc),
            "checks": checks,
        }

    if result.get("status") == "success":
        return {
            "success": True,
            "status": "ok",
            "message": "Interswitch credentials and billers endpoint are reachable.",
            "checks": checks,
            "sample_billers_count": len(result.get("data", [])),
        }

    message = result.get("message", "Unknown error")
    pending = _is_sandbox_pending(message)
    return {
        "success": False,
        "status": "sandbox_pending" if pending else "failed",
        "message": message,
        "checks": checks,
    }
