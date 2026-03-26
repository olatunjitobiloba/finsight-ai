"""Interswitch Marketplace Routing integration for FinSight AI."""

import base64
import hashlib
import hmac
import logging
import os
import time
import uuid
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

TOKEN_URL = os.getenv("INTERSWITCH_TOKEN_URL", "https://qa.interswitchng.com/passport/oauth/token")
QUICKTELLER_URL = os.getenv("INTERSWITCH_QT_BASE_URL", "https://qa.interswitchng.com/quicktellerservice/api/v5")
QUICKTELLER_V2_URL = os.getenv("INTERSWITCH_QT_V2_BASE_URL", "https://sandbox.interswitchng.com/api/v2/quickteller")
VERIFY_BASE_URL = os.getenv(
    "INTERSWITCH_VERIFY_BASE_URL",
    "https://api-marketplace-routing.k8.isw.la/marketplace-routing/api/v1",
)
BASE_URL = os.getenv("INTERSWITCH_BASE_URL", VERIFY_BASE_URL)
TERMINAL_ID = os.getenv("INTERSWITCH_TERMINAL_ID", "3DMO0001")

_token_cache = {
    "token": None,
    "expires_at": 0,
    "profile_token": None,
    "profile_expires_at": 0,
}


def _request_with_retry(
    method: str,
    url: str,
    *,
    headers: Optional[dict] = None,
    params: Optional[dict] = None,
    json: Optional[dict] = None,
    data: Optional[dict] = None,
    timeout: float = 10.0,
    max_attempts: int = 2,
    retry_delay_seconds: float = 1.0,
) -> dict:
    """Perform an HTTP request with retry on transport-level disconnects."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    path = parsed.path or "/"
    request_id = str(uuid.uuid4())[:8]

    transport_exceptions = (
        httpx.RemoteProtocolError,
        httpx.ConnectError,
        httpx.ReadError,
        httpx.WriteError,
        httpx.ReadTimeout,
        httpx.WriteTimeout,
        httpx.PoolTimeout,
    )

    for attempt in range(1, max_attempts + 1):
        try:
            response = httpx.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json,
                data=data,
                timeout=timeout,
            )
            return {"ok": True, "response": response, "attempts": attempt}
        except transport_exceptions as exc:
            if attempt < max_attempts:
                time.sleep(retry_delay_seconds)
                continue

            return {
                "ok": False,
                "error": {
                    "status": "error",
                    "message": str(exc),
                    "request_id": request_id,
                    "target_path": path,
                    "error_type": exc.__class__.__name__,
                    "phase": "transport",
                    "url_host": host,
                    "attempts": attempt,
                    "retryable": True,
                },
            }
        except Exception as exc:
            return {
                "ok": False,
                "error": {
                    "status": "error",
                    "message": str(exc),
                    "request_id": request_id,
                    "target_path": path,
                    "error_type": exc.__class__.__name__,
                    "phase": "request",
                    "url_host": host,
                    "attempts": attempt,
                    "retryable": False,
                },
            }

    return {
        "ok": False,
        "error": {
            "status": "error",
            "message": "Unknown request failure",
            "request_id": request_id,
            "target_path": path,
            "error_type": "UnknownError",
            "phase": "request",
            "url_host": host,
            "attempts": max_attempts,
            "retryable": False,
        },
    }


def _env(*names: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    return ""


def _parse_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except Exception:
        return response.text or f"HTTP {response.status_code}"

    if isinstance(payload, dict):
        code = payload.get("code") or payload.get("error") or ""
        description = payload.get("description") or payload.get("message") or payload.get("error_description") or ""
        text = ": ".join([part for part in [str(code).strip(), str(description).strip()] if part])
        return text or str(payload)
    return str(payload)


def get_default_payment_code() -> str:
    """Get default payment code from env or access token metadata."""
    configured = _env("INTERSWITCH_DEFAULT_PAYMENT_CODE", "INTERSWITCH_PAY_ITEM_ID", "INTERSWITCH_PAYABLE_CODE")
    if configured:
        return configured
    return str(_token_cache.get("production_payment_code") or "").strip()


def get_access_token(force_refresh: bool = False) -> str:
    """Get and cache OAuth2 Bearer token for Interswitch APIs."""
    client_id = _env("INTERSWITCH_CLIENT_ID", "INTERSWITCH_API_CLIENT_ID")
    # Support naming used across docs and existing deployments.
    client_secret = _env(
        "INTERSWITCH_CLIENT_SECRET",
        "INTERSWITCH_SECRET_KEY",
        "INTERSWITCH_SECRET",
        "INTERSWITCH_API_SECRET",
    )

    if not force_refresh and _token_cache["token"] and time.time() < _token_cache["expires_at"] - 60:
        return _token_cache["token"]

    if not client_id or not client_secret:
        raise ValueError(
            "INTERSWITCH_CLIENT_ID and INTERSWITCH_CLIENT_SECRET/INTERSWITCH_SECRET "
            "must be set as environment variables."
        )

    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    try:
        response = httpx.post(
            TOKEN_URL,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            data={
                "grant_type": "client_credentials",
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        _token_cache["token"] = data["access_token"]
        _token_cache["expires_at"] = time.time() + data.get("expires_in", 3600)
        _token_cache["production_payment_code"] = data.get("production_payment_code")

        return _token_cache["token"]
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Interswitch auth failed: {_parse_error_message(e.response)}") from e
    except Exception as e:
        raise RuntimeError(f"Interswitch auth error: {str(e)}") from e


def get_name_inquiry_token(force_refresh: bool = False) -> str:
    """Get access token specifically scoped for Send Money / Name Inquiry."""
    client_id = _env("INTERSWITCH_CLIENT_ID", "INTERSWITCH_API_CLIENT_ID")
    client_secret = _env(
        "INTERSWITCH_CLIENT_SECRET",
        "INTERSWITCH_SECRET_KEY",
        "INTERSWITCH_SECRET",
        "INTERSWITCH_API_SECRET",
    )

    if not client_id or not client_secret:
        raise ValueError(
            "INTERSWITCH_CLIENT_ID and INTERSWITCH_CLIENT_SECRET/INTERSWITCH_SECRET "
            "must be set as environment variables."
        )

    if not force_refresh and _token_cache["profile_token"] and time.time() < _token_cache["profile_expires_at"] - 60:
        return _token_cache["profile_token"]

    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    response = httpx.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        data={
            "grant_type": "client_credentials",
            "scope": "profile",
        },
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    _token_cache["profile_token"] = data["access_token"]
    _token_cache["profile_expires_at"] = time.time() + data.get("expires_in", 1799)
    return _token_cache["profile_token"]


def _auth_headers(force_refresh: bool = False) -> dict:
    token = get_access_token(force_refresh=force_refresh)
    return {
        # Docs vary between Authorization and Authentication. Send both.
        "Authorization": f"Bearer {token}",
        "Authentication": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "TerminalID": TERMINAL_ID,
        "TerminalId": TERMINAL_ID,
    }


def _build_interswitch_auth_headers(http_method: str, url: str) -> dict:
    """Build InterswitchAuth headers used by Quickteller v2 bill-payment APIs."""
    client_id = _env("INTERSWITCH_CLIENT_ID", "INTERSWITCH_API_CLIENT_ID")
    secret_key = _env(
        "INTERSWITCH_CLIENT_SECRET",
        "INTERSWITCH_SECRET_KEY",
        "INTERSWITCH_SECRET",
        "INTERSWITCH_API_SECRET",
    )

    if not client_id or not secret_key:
        raise ValueError(
            "INTERSWITCH_CLIENT_ID and INTERSWITCH_CLIENT_SECRET/INTERSWITCH_SECRET "
            "must be set as environment variables."
        )

    timestamp = str(int(time.time()))
    nonce = uuid.uuid4().hex
    method = (http_method or "GET").upper().strip()

    signature_string = f"{client_id}{method}{url}{timestamp}{nonce}"
    raw_sig = hmac.new(
        secret_key.encode("utf-8"),
        signature_string.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    signature = base64.b64encode(raw_sig).decode("utf-8")

    auth_raw = f"{client_id}:{timestamp}:{nonce}:{signature}"
    auth_string = base64.b64encode(auth_raw.encode("utf-8")).decode("utf-8")

    return {
        "Authorization": f"InterswitchAuth {auth_string}",
        "Signature": signature,
        "Timestamp": timestamp,
        "Nonce": nonce,
        "SignatureMethod": "SHA1",
        "TerminalID": TERMINAL_ID,
        "TerminalId": TERMINAL_ID,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _basic_headers() -> dict:
    client_id = _env("INTERSWITCH_CLIENT_ID", "INTERSWITCH_API_CLIENT_ID")
    client_secret = _env(
        "INTERSWITCH_CLIENT_SECRET",
        "INTERSWITCH_SECRET_KEY",
        "INTERSWITCH_SECRET",
        "INTERSWITCH_API_SECRET",
    )
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    return {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "TerminalID": TERMINAL_ID,
        "TerminalId": TERMINAL_ID,
    }


def _generate_reference(prefix: str = "FS") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12].upper()}"


def get_billers() -> dict:
    """Fetch all supported billers for VAS payments."""
    try:
        url = f"{QUICKTELLER_V2_URL}/billers"
        response = httpx.get(
            url,
            headers=_build_interswitch_auth_headers("GET", url),
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            return {"status": "success", "data": payload}
        if isinstance(payload, dict):
            data = payload.get("data") or payload.get("billers") or payload.get("Billers")
            if isinstance(data, list):
                return {"status": "success", "data": data}
        return {"status": "success", "data": []}
    except httpx.HTTPStatusError as e:
        return {"status": "error", "message": _parse_error_message(e.response)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_payment_items(biller_id: int) -> dict:
    """Fetch biller payment items and payment codes."""
    try:
        url = f"{QUICKTELLER_V2_URL}/billers/{int(biller_id)}/paymentitems"
        timeout_seconds = float(os.getenv("INTERSWITCH_PAYMENT_ITEMS_TIMEOUT_SECONDS", "3"))
        wrapped = _request_with_retry(
            "GET",
            url,
            headers=_build_interswitch_auth_headers("GET", url),
            timeout=timeout_seconds,
            max_attempts=2,
            retry_delay_seconds=1.0,
        )

        if not wrapped.get("ok"):
            return wrapped.get("error", {"status": "error", "message": "Request failed"})

        response = wrapped["response"]
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            return {"status": "success", "data": payload}
        if isinstance(payload, dict):
            data = payload.get("data") or payload.get("paymentitems") or payload.get("paymentItems")
            if isinstance(data, list):
                return {"status": "success", "data": data}
        return {"status": "success", "data": []}
    except httpx.HTTPStatusError as e:
        parsed = urlparse(str(e.request.url) if e.request else QUICKTELLER_V2_URL)
        return {
            "status": "error",
            "message": _parse_error_message(e.response),
            "error_type": "HTTPStatusError",
            "phase": "http_status",
            "url_host": parsed.hostname or "",
            "status_code": e.response.status_code,
            "retryable": False,
        }
    except Exception as e:
        parsed = urlparse(QUICKTELLER_V2_URL)
        return {
            "status": "error",
            "message": str(e),
            "error_type": e.__class__.__name__,
            "phase": "request",
            "url_host": parsed.hostname or "",
            "retryable": False,
        }


def validate_customer(customer_id: str, payment_code: str) -> dict:
    """Validate customer details before VAS payment."""
    try:
        url = f"{QUICKTELLER_V2_URL}/customers/validations"
        response = httpx.post(
            url,
            headers=_build_interswitch_auth_headers("POST", url),
            json={
                "customers": [
                    {
                        "paymentCode": payment_code,
                        "customerId": customer_id,
                    }
                ],
                "TerminalId": TERMINAL_ID,
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        customers = []
        if isinstance(data, dict):
            customers = data.get("customers") or data.get("Customers") or data.get("data") or []

        if customers:
            customer_data = customers[0]
            return {
                "status": "success",
                "customer_name": customer_data.get("customerName") or customer_data.get("FullName", ""),
                "amount": customer_data.get("amount") or customer_data.get("Amount", 0),
                "amount_type": customer_data.get("amountType") or customer_data.get("AmountTypeDescription", ""),
                "surcharge": customer_data.get("surcharge") or customer_data.get("Surcharge", 0),
                "response_code": customer_data.get("responseCode") or customer_data.get("ResponseCode", ""),
                "raw": customer_data,
            }
        return {"status": "error", "message": str(data)}
    except httpx.HTTPStatusError as e:
        return {"status": "error", "message": _parse_error_message(e.response)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def pay_bill(
    customer_id: str,
    payment_code: str,
    amount_naira: float,
    reference: Optional[str] = None,
    customer_mobile: Optional[str] = None,
    customer_email: Optional[str] = None,
) -> dict:
    """Execute bill payment via Quickteller v2 payment advice endpoint."""
    ref_prefix = _env("INTERSWITCH_REQUEST_REF_PREFIX") or "1453"
    ref = reference or f"{ref_prefix}{int(time.time())}"
    amount_minor = int(round(float(amount_naira) * 100))
    mobile = (customer_mobile or _env("INTERSWITCH_TEST_CUSTOMER_MOBILE") or "2348056731576").strip()
    email = (customer_email or _env("INTERSWITCH_TEST_CUSTOMER_EMAIL") or "test@test.com").strip()

    try:
        url = f"{QUICKTELLER_V2_URL}/payments/advices"
        response = httpx.post(
            url,
            headers=_build_interswitch_auth_headers("POST", url),
            json={
                "TerminalId": TERMINAL_ID,
                "customerId": customer_id,
                "amount": str(amount_minor),
                "requestReference": ref,
                "paymentCode": payment_code,
                "customerMobile": mobile,
                "customerEmail": email,
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict):
            result = data.get("data", data)
            response_code = str(result.get("responseCode") or result.get("ResponseCode") or data.get("responseCode") or "")
            response_desc = (
                result.get("responseDescription")
                or result.get("ResponseDescription")
                or data.get("responseDescription")
                or data.get("message")
                or "Payment processed"
            )
            grouping = str(result.get("responseCodeGrouping") or result.get("ResponseCodeGrouping") or "")
            success = response_code in {"00", "0"} or grouping.upper() == "SUCCESSFUL"

            if not success:
                return {
                    "status": "error",
                    "reference": ref,
                    "amount": amount_naira,
                    "amount_minor": amount_minor,
                    "response_code": response_code,
                    "message": response_desc,
                    "raw": data,
                }

            return {
                "status": "success",
                "reference": (
                    result.get("requestReference")
                    or result.get("RequestReference")
                    or result.get("TransactionRef")
                    or ref
                ),
                "amount": amount_naira,
                "amount_minor": amount_minor,
                "response_code": response_code,
                "description": response_desc,
                "grouping": grouping,
                "provider": "Interswitch",
                "raw": data,
            }

        return {
            "status": "error",
            "message": "Payment failed",
            "reference": ref,
        }
    except httpx.HTTPStatusError as e:
        return {
            "status": "error",
            "message": _parse_error_message(e.response),
            "reference": ref,
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "reference": ref}


def check_transaction(request_reference: str) -> dict:
    """Check transaction status by reference."""
    try:
        response = httpx.get(
            f"{QUICKTELLER_URL}/Transactions",
            headers=_auth_headers(),
            params={"requestRef": request_reference},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict):
            result = data.get("data", data)
            return {
                "status": "success",
                "tx_ref": result.get("RequestReference") or result.get("TransactionRef", ""),
                "tx_status": result.get("Status", ""),
                "amount": result.get("Amount", 0),
                "service": result.get("ServiceName", ""),
                "paid_on": result.get("PaymentDate", ""),
                "raw": result,
            }

        return {"status": "error", "message": str(data)}
    except httpx.HTTPStatusError as e:
        return {"status": "error", "message": _parse_error_message(e.response)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_bank_list() -> dict:
    """Fetch list of banks and corresponding bank codes."""
    url = f"{QUICKTELLER_V2_URL}/banks"
    try:
        # Bank list is served by Quickteller, not the Verify identity API.
        logging.warning("[get_bank_list] Calling URL: %s", url)
        logging.warning("[get_bank_list] QUICKTELLER_V2_URL = %s", QUICKTELLER_V2_URL)
        response = httpx.get(url, headers=_auth_headers(), timeout=15)

        # Token may be stale; force refresh once on unauthorized.
        if response.status_code == 401:
            logging.warning("[get_bank_list] Received 401, retrying with refreshed token")
            response = httpx.get(url, headers=_auth_headers(force_refresh=True), timeout=15)

        logging.warning("[get_bank_list] Status code: %s", response.status_code)
        logging.warning("[get_bank_list] Raw response preview: %s", response.text[:500])
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return {"status": "success", "banks": data, "resolved_url": url}
        if isinstance(data, dict):
            return {
                "status": "success",
                "banks": data.get("data") or data.get("banks") or [],
                "resolved_url": url,
            }
        return {"status": "success", "banks": [], "resolved_url": url}
    except httpx.HTTPStatusError as e:
        response_text = ""
        status_code = None
        if e.response is not None:
            status_code = e.response.status_code
            response_text = e.response.text[:500]

        logging.warning("[get_bank_list] HTTP error status=%s body=%s", status_code, response_text)
        return {
            "status": "error",
            "message": _parse_error_message(e.response),
            "resolved_url": url,
            "status_code": status_code,
            "response_preview": response_text,
        }
    except Exception as e:
        logging.warning("[get_bank_list] Exception: %s", str(e))
        return {
            "status": "error",
            "message": str(e),
            "resolved_url": url,
        }


def verify_bank_account(account_number: str, bank_code: str) -> dict:
    """Resolve account name via Marketplace verify identity endpoint."""
    try:
        url = f"{VERIFY_BASE_URL}/verify/identity/account-number/resolve"
        payload = {
            "accountNumber": account_number,
            "bankCode": bank_code,
        }
        token = get_name_inquiry_token()

        response = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
            timeout=15,
        )

        # Token may be stale; force refresh once on unauthorized.
        if response.status_code == 401:
            token = get_name_inquiry_token(force_refresh=True)
            response = httpx.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=payload,
                timeout=15,
            )

        if os.getenv("INTERSWITCH_DEBUG_NAME_INQUIRY", "").strip().lower() in {"1", "true", "yes", "on"}:
            print("NAME_INQUIRY_STATUS:", response.status_code)
            print("NAME_INQUIRY_RAW:", response.text)

        response.raise_for_status()
        data = response.json()

        result = data.get("data") if isinstance(data, dict) else None
        if not isinstance(result, dict):
            result = {}

        response_code = str(data.get("responseCode") or data.get("ResponseCode") or "")
        top_level_code = str(data.get("code") or "")
        top_level_success = bool(data.get("success") is True)
        account_name = (
            result.get("accountName")
            or result.get("AccountName")
            or result.get("beneficiaryName")
            or result.get("BeneficiaryName")
            or (result.get("bankDetails") or {}).get("accountName")
            or data.get("accountName")
            or data.get("AccountName")
            or ""
        )

        is_success = bool(account_name) and (
            top_level_success
            or top_level_code == "200"
            or response_code not in {"", "ERROR", "VALIDATION_ERROR"}
        )

        if is_success and account_name:
            return {
                "status": "success",
                "account_name": account_name,
                "account_no": account_number,
                "bank_code": bank_code,
                "raw": data,
            }

        provider_code = str(data.get("responseCode") or data.get("ResponseCode") or "")
        log_id = str(data.get("logId") or data.get("logID") or "")
        error_message = data.get("message") or data.get("ResponseDescription") or f"Verification failed - code: {response_code}"
        if log_id:
            error_message = f"{error_message} (logId: {log_id})"
        return {
            "status": "error",
            "message": error_message,
            "raw": data,
            "provider_code": provider_code,
            "log_id": log_id,
        }
    except httpx.HTTPStatusError as e:
        log_id = ""
        provider_code = ""
        message = _parse_error_message(e.response)
        try:
            payload = e.response.json()
            if isinstance(payload, dict):
                log_id = str(payload.get("logId") or payload.get("logID") or "")
                provider_code = str(payload.get("responseCode") or payload.get("ResponseCode") or "")
                if log_id and "logId:" not in message:
                    message = f"{message} (logId: {log_id})"
        except Exception:
            pass
        return {
            "status": "error",
            "message": message,
            "provider_code": provider_code,
            "log_id": log_id,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def generate_otp(token_id: str) -> dict:
    """Generate Safetoken OTP for transaction confirmation."""
    try:
        response = httpx.post(
            f"{VERIFY_BASE_URL}/soft-token/generate",
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
        return {"status": "error", "message": _parse_error_message(e.response)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def verify_otp(token_id: str, otp: str) -> dict:
    """Verify Safetoken OTP and return authentication token when valid."""
    try:
        response = httpx.post(
            f"{VERIFY_BASE_URL}/soft-token/verify",
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
        return {"status": "error", "message": _parse_error_message(e.response)}
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
