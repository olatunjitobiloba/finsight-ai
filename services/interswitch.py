"""Interswitch Marketplace Routing integration for FinSight AI."""

import base64
import os
import time
import uuid
from typing import Optional

import httpx

TOKEN_URL = "https://qa.interswitchng.com/passport/oauth/token"
BASE_URL = "https://api-marketplace-routing.k8.isw.la/marketplace-routing/api/v1"

_token_cache = {"token": None, "expires_at": 0}


def get_access_token() -> str:
    """Get and cache OAuth2 Bearer token for Interswitch APIs."""
    client_id = os.getenv("INTERSWITCH_CLIENT_ID", "")
    client_secret = os.getenv("INTERSWITCH_CLIENT_SECRET", "")

    if _token_cache["token"] and time.time() < _token_cache["expires_at"] - 60:
        return _token_cache["token"]

    if not client_id or not client_secret:
        raise ValueError(
            "INTERSWITCH_CLIENT_ID and INTERSWITCH_CLIENT_SECRET "
            "must be set as environment variables."
        )

    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    try:
        response = httpx.post(
            TOKEN_URL,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "client_credentials",
                "scope": "profile",
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        _token_cache["token"] = data["access_token"]
        _token_cache["expires_at"] = time.time() + data.get("expires_in", 3600)

        return _token_cache["token"]
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Interswitch auth failed: {e.response.text}") from e
    except Exception as e:
        raise RuntimeError(f"Interswitch auth error: {str(e)}") from e


def _auth_headers() -> dict:
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json",
    }


def _generate_reference(prefix: str = "FS") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12].upper()}"


def get_billers() -> dict:
    """Fetch all supported billers for VAS payments."""
    try:
        response = httpx.get(
            f"{BASE_URL}/vas/billers",
            headers=_auth_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return {"status": "success", "data": response.json().get("data", [])}
    except httpx.HTTPStatusError as e:
        return {"status": "error", "message": e.response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_payment_items(biller_id: int) -> dict:
    """Fetch biller payment items and payment codes."""
    try:
        response = httpx.get(
            f"{BASE_URL}/vas/billers/payment-item",
            headers=_auth_headers(),
            params={"biller-id": biller_id},
            timeout=15,
        )
        response.raise_for_status()
        return {"status": "success", "data": response.json().get("data", [])}
    except httpx.HTTPStatusError as e:
        return {"status": "error", "message": e.response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def validate_customer(customer_id: str, payment_code: str) -> dict:
    """Validate customer details before VAS payment."""
    try:
        response = httpx.post(
            f"{BASE_URL}/vas/validate-customer",
            headers=_auth_headers(),
            json=[
                {
                    "customerId": customer_id,
                    "paymentCode": payment_code,
                }
            ],
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("success"):
            customer_data = data.get("data", [{}])[0]
            return {
                "status": "success",
                "customer_name": customer_data.get("FullName", ""),
                "amount": customer_data.get("Amount", 0),
                "amount_type": customer_data.get("AmountTypeDescription", ""),
                "surcharge": customer_data.get("Surcharge", 0),
                "raw": customer_data,
            }
        return {"status": "error", "message": data.get("message", "Validation failed")}
    except httpx.HTTPStatusError as e:
        return {"status": "error", "message": e.response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def pay_bill(
    customer_id: str,
    payment_code: str,
    amount_naira: float,
    reference: Optional[str] = None,
) -> dict:
    """Execute VAS payment via Interswitch Marketplace Routing."""
    ref = reference or _generate_reference("FS")

    try:
        response = httpx.post(
            f"{BASE_URL}/vas/pay",
            headers=_auth_headers(),
            json={
                "customerId": customer_id,
                "amount": amount_naira,
                "reference": ref,
                "paymentCode": payment_code,
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("success"):
            result = data.get("data", {})
            return {
                "status": "success",
                "reference": result.get("TransactionRef", ref),
                "amount": amount_naira,
                "response_code": result.get("ResponseCode", ""),
                "description": result.get("ResponseDescription", "Payment successful"),
                "grouping": result.get("ResponseCodeGrouping", ""),
                "provider": "Interswitch",
                "raw": result,
            }

        return {
            "status": "error",
            "message": data.get("message", "Payment failed"),
            "reference": ref,
        }
    except httpx.HTTPStatusError as e:
        return {
            "status": "error",
            "message": f"Payment failed: {e.response.text}",
            "reference": ref,
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "reference": ref}


def check_transaction(request_reference: str) -> dict:
    """Check transaction status by reference."""
    try:
        response = httpx.get(
            f"{BASE_URL}/vas/transactions",
            headers=_auth_headers(),
            params={"request-reference": request_reference},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("success"):
            result = data.get("data", {})
            return {
                "status": "success",
                "tx_ref": result.get("TransactionRef", ""),
                "tx_status": result.get("Status", ""),
                "amount": result.get("Amount", 0),
                "service": result.get("ServiceName", ""),
                "paid_on": result.get("PaymentDate", ""),
                "raw": result,
            }

        return {"status": "error", "message": data.get("message", "Query failed")}
    except httpx.HTTPStatusError as e:
        return {"status": "error", "message": e.response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_bank_list() -> dict:
    """Fetch list of banks and corresponding bank codes."""
    try:
        response = httpx.get(
            f"{BASE_URL}/verify/identity/account-number/bank-list",
            headers=_auth_headers(),
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        return {"status": "success", "banks": data.get("data", [])}
    except httpx.HTTPStatusError as e:
        return {"status": "error", "message": e.response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def verify_bank_account(account_number: str, bank_code: str) -> dict:
    """Resolve account name from account number and bank code."""
    try:
        response = httpx.post(
            f"{BASE_URL}/verify/identity/account-number/resolve",
            headers=_auth_headers(),
            json={
                "accountNumber": account_number,
                "bankCode": bank_code,
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("success"):
            result = data.get("data", {})
            return {
                "status": "success",
                "account_name": result.get("bankDetails", {}).get("accountName", ""),
                "account_no": account_number,
                "bank_code": bank_code,
                "raw": result,
            }

        return {"status": "error", "message": data.get("message", "Verification failed")}
    except httpx.HTTPStatusError as e:
        return {"status": "error", "message": e.response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def generate_otp(token_id: str) -> dict:
    """Generate Safetoken OTP for transaction confirmation."""
    try:
        response = httpx.post(
            f"{BASE_URL}/soft-token/generate",
            headers=_auth_headers(),
            json={"tokenId": token_id},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("success"):
            result = data.get("data", {})
            return {
                "status": "success",
                "otp": result.get("otp", ""),
                "expiry": result.get("expiry", ""),
                "correlation_id": result.get("correlationId", ""),
                "token_id": token_id,
            }

        return {"status": "error", "message": data.get("message", "OTP generation failed")}
    except httpx.HTTPStatusError as e:
        return {"status": "error", "message": e.response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def verify_otp(token_id: str, otp: str) -> dict:
    """Verify Safetoken OTP and return authentication token when valid."""
    try:
        response = httpx.post(
            f"{BASE_URL}/soft-token/verify",
            headers=_auth_headers(),
            json={
                "tokenId": token_id,
                "otp": otp,
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("success"):
            result = data.get("data", {})
            verified = result.get("transactionStatus", "N") == "Y"
            return {
                "status": "success" if verified else "failed",
                "verified": verified,
                "auth_token": result.get("authenticationToken", ""),
                "raw": result,
            }

        return {"status": "error", "message": data.get("message", "OTP verification failed")}
    except httpx.HTTPStatusError as e:
        return {"status": "error", "message": e.response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_biller_info(biller_code: str) -> dict:
    """
    Backward-compatible helper.
    Prefer get_billers() and get_payment_items() with biller-id.
    """
    billers = get_billers()
    if billers.get("status") != "success":
        return billers

    match = None
    needle = (biller_code or "").strip().lower()
    for biller in billers.get("data", []):
        name = str(biller.get("name") or biller.get("billerName") or "").lower()
        code = str(biller.get("code") or biller.get("billerCode") or "").lower()
        if needle and (needle == code or needle in name):
            match = biller
            break

    if not match:
        return {
            "status": "error",
            "message": "Biller not found. Use get_billers() to inspect available billers.",
        }
    return {"status": "success", "data": match}


def get_data_bundles(network: str) -> list:
    """
    Backward-compatible bundle lookup for legacy callers.
    Uses billers/payment-items where possible, otherwise returns static fallback bundles.
    """
    network_name = (network or "").strip().lower()
    billers = get_billers()
    if billers.get("status") == "success":
        for biller in billers.get("data", []):
            name = str(biller.get("name") or biller.get("billerName") or "").lower()
            if network_name and network_name in name:
                biller_id = biller.get("id") or biller.get("billerId")
                if biller_id is not None:
                    items = get_payment_items(int(biller_id))
                    if items.get("status") == "success":
                        return items.get("data", [])
    return _fallback_bundles(network)


def _fallback_bundles(network: str) -> list:
    bundles = {
        "mtn": [
            {"code": "MTN1GB", "name": "1GB - 30 days", "price": 300},
            {"code": "MTN2GB", "name": "2GB - 30 days", "price": 500},
        ],
        "airtel": [
            {"code": "AIR1GB", "name": "1.5GB - 30 days", "price": 300},
            {"code": "AIR3GB", "name": "3GB - 30 days", "price": 500},
        ],
        "glo": [
            {"code": "GLO2GB", "name": "2.5GB - 30 days", "price": 300},
            {"code": "GLO5GB", "name": "5GB - 30 days", "price": 500},
        ],
        "9mobile": [
            {"code": "9M1GB", "name": "1GB - 30 days", "price": 300},
            {"code": "9M2GB", "name": "2GB - 30 days", "price": 500},
        ],
    }
    return bundles.get((network or "").strip().lower(), [])


def bank_transfer(
    destination_account: str,
    destination_bank_code: str,
    amount_naira: float,
    narration: str,
    user_id: str,
) -> dict:
    """
    Backward-compatible placeholder for legacy integration.
    Marketplace Routing endpoints in this module focus on VAS and verification.
    """
    _ = (destination_account, destination_bank_code, amount_naira, narration, user_id)
    return {
        "status": "error",
        "message": "bank_transfer is not configured for Marketplace Routing in this build.",
    }


def simulate_saving(amount: float, plan_type: str, user_profile: Optional[dict] = None) -> dict:
    """
    Build a simple savings plan preview.
    This is intentionally provider-agnostic and does not execute a payment.
    """
    if amount <= 0:
        return {
            "success": False,
            "error": "Amount must be greater than zero",
        }

    frequencies = {
        "weekly": 4,
        "monthly": 1,
        "quarterly": 1 / 3,
        "custom": 1,
    }
    factor = frequencies.get((plan_type or "").lower(), 1)
    monthly_equivalent = round(amount * factor, 2)

    return {
        "success": True,
        "message": "Savings plan prepared",
        "plan": {
            "amount": round(amount, 2),
            "plan_type": (plan_type or "monthly").lower(),
            "estimated_monthly_contribution": monthly_equivalent,
        },
        "user_profile": user_profile or {},
        "provider": "Interswitch",
        "mode": "simulation",
    }


def simulate_savings(transactions: list, user_profile: Optional[dict] = None) -> dict:
    """
    Analyze spend vs income and suggest a savings target.
    """
    income = 0.0
    spend = 0.0

    for txn in transactions or []:
        amount = float(txn.get("amount", 0) or 0)
        tx_type = str(txn.get("type", "")).lower()
        if tx_type == "credit":
            income += amount
        elif tx_type == "debit":
            spend += amount

    net = income - spend
    suggested = round(max(0.0, income * 0.2), 2)

    return {
        "summary": {
            "income": round(income, 2),
            "spending": round(spend, 2),
            "net": round(net, 2),
        },
        "recommendation": {
            "target_savings": suggested,
            "rule": "20_percent_of_income",
        },
        "user_profile": user_profile or {},
        "provider": "Interswitch",
        "mode": "simulation",
    }


def simulate_bill_optimization(transactions: list) -> dict:
    """
    Group recurring bill-like categories and return optimization hints.
    """
    tracked_categories = {"electricity", "data", "airtime", "internet", "tv", "rent"}
    totals = {}

    for txn in transactions or []:
        category = str(txn.get("category", "")).strip().lower()
        if not category and txn.get("description"):
            category = str(txn.get("description", "")).strip().lower()

        if category in tracked_categories:
            totals[category] = totals.get(category, 0.0) + float(txn.get("amount", 0) or 0)

    suggestions = []
    for category, total in sorted(totals.items(), key=lambda item: item[1], reverse=True):
        suggestions.append({
            "category": category,
            "current_spend": round(total, 2),
            "suggested_cap": round(total * 0.9, 2),
            "estimated_monthly_saving": round(total * 0.1, 2),
        })

    return {
        "tracked_totals": {k: round(v, 2) for k, v in totals.items()},
        "suggestions": suggestions,
        "provider": "Interswitch",
        "mode": "simulation",
    }
