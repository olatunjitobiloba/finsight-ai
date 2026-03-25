"""Interswitch Marketplace VAS bills payment service layer."""

import base64
import os
import uuid
from typing import Any, Dict, List, Optional

import httpx

ISW_BASE_AUTH = "https://qa.interswitchng.com/passport/oauth/token"
ISW_BASE_VAS = "https://api-marketplace-routing.k8.isw.la/marketplace-routing/api/v1/vas"


def _get_token() -> str:
	"""Fetch OAuth2 bearer token for Marketplace APIs."""
	cid = (os.getenv("INTERSWITCH_CLIENT_ID") or "").strip()
	sec = (
		os.getenv("INTERSWITCH_CLIENT_SECRET")
		or os.getenv("INTERSWITCH_SECRET_KEY")
		or ""
	).strip()

	if not cid or not sec:
		raise ValueError("Missing INTERSWITCH_CLIENT_ID or INTERSWITCH_CLIENT_SECRET/INTERSWITCH_SECRET_KEY")

	cred = base64.b64encode(f"{cid}:{sec}".encode()).decode()
	response = httpx.post(
		ISW_BASE_AUTH,
		headers={
			"Authorization": f"Basic {cred}",
			"Content-Type": "application/x-www-form-urlencoded",
		},
		data={"grant_type": "client_credentials", "scope": "profile"},
		timeout=20,
	)
	response.raise_for_status()
	data = response.json()
	token = str(data.get("access_token") or "").strip()
	if not token:
		raise RuntimeError("No access_token in auth response")
	return token


def _headers() -> Dict[str, str]:
	return {
		"Authorization": f"Bearer {_get_token()}",
		"Content-Type": "application/json",
	}


def get_billers() -> Dict[str, Any]:
	"""Get Marketplace billers grouped by category."""
	response = httpx.get(f"{ISW_BASE_VAS}/billers", headers=_headers(), timeout=20)
	response.raise_for_status()
	return {
		"status_code": response.status_code,
		"body": response.json(),
	}


def get_payment_items(biller_id: int) -> Dict[str, Any]:
	"""Get payment items for a biller and return normalized list."""
	response = httpx.get(
		f"{ISW_BASE_VAS}/billers/payment-item",
		headers=_headers(),
		params={"biller-id": biller_id},
		timeout=20,
	)
	response.raise_for_status()
	return {
		"status_code": response.status_code,
		"body": response.json(),
	}


def validate_customer(customer_id: str, payment_code: str) -> Dict[str, Any]:
	"""Validate customer against a payment code.

	Returns status_code and response body since sandbox can return non-2xx business errors.
	"""
	response = httpx.post(
		f"{ISW_BASE_VAS}/validate-customer",
		headers=_headers(),
		json=[{"customerId": customer_id, "paymentCode": payment_code}],
		timeout=30,
	)
	return {
		"status_code": response.status_code,
		"body": response.json(),
	}


def pay_bill(
	payment_code: str,
	customer_id: str,
	amount: int,
	customer_mobile: str = "08000000000",
	customer_email: str = "user@finsight.com",
	terminal_id: str = "3DMO0001",
	reference: Optional[str] = None,
) -> Dict[str, Any]:
	"""Initiate bill payment using Marketplace VAS /pay endpoint."""
	ref = reference or f"FINSIGHT-{uuid.uuid4().hex[:12].upper()}"

	response = httpx.post(
		f"{ISW_BASE_VAS}/pay",
		headers=_headers(),
		json={
			"paymentCode": payment_code,
			"customerId": customer_id,
			"customerMobile": customer_mobile,
			"customerEmail": customer_email,
			"amount": amount,
			"reference": ref,
			"terminalId": terminal_id,
		},
		timeout=90,
	)

	return {
		"status_code": response.status_code,
		"reference": ref,
		"body": response.json(),
	}


def get_transaction_status(reference: str) -> Dict[str, Any]:
	"""Check bill payment status by request reference."""
	response = httpx.get(
		f"{ISW_BASE_VAS}/transactions",
		headers=_headers(),
		params={"request-reference": reference},
		timeout=20,
	)
	return {
		"status_code": response.status_code,
		"body": response.json(),
	}
