"""Bills Payment routes using Interswitch Marketplace VAS API."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services import (
    get_vas_billers,
    get_vas_payment_items,
    validate_vas_customer,
    pay_vas_bill,
    get_vas_transaction_status,
)

router = APIRouter(prefix="/api/bills", tags=["bills"])


# Request Models
class PaymentItemRequest(BaseModel):
    """Get payment items (codes) for a specific biller."""
    biller_id: int


class ValidateCustomerRequest(BaseModel):
    """Validate customer before payment."""
    customer_id: str = Field(..., min_length=1, description="Customer ID from biller")
    payment_code: str = Field(..., min_length=1, description="Payment code (e.g., 10902)")


class PayBillRequest(BaseModel):
    """Initiate bill payment."""
    customer_id: str = Field(..., min_length=1, description="Customer ID")
    payment_code: str = Field(..., min_length=1, description="Payment code")
    amount: int = Field(..., gt=0, description="Amount in kobo (minimum 20000 for ₦200)")
    customer_mobile: Optional[str] = Field(None, description="Customer phone number")
    customer_email: Optional[str] = Field(None, description="Customer email")
    reference: Optional[str] = Field(None, description="Unique reference; auto-generated if omitted")
    terminal_id: Optional[str] = Field("3DMO0001", description="Terminal ID for transaction")


class TransactionStatusRequest(BaseModel):
    """Check transaction status."""
    reference: str = Field(..., min_length=1, description="Transaction reference from pay response")


# Routes
@router.get("/billers")
async def get_billers():
    """
    Get list of all available billers organized by category.
    
    Returns categorized biller list with IDs and names.
    """
    try:
        result = get_vas_billers()
        status_code = result.get("status_code")
        body = result.get("body", {})
        
        if status_code == 200:
            return {
                "status": "success",
                "data": body.get("data", {}),
                "response_code": body.get("ResponseCode")
            }
        
        return {
            "status": "error",
            "message": body.get("message", "Failed to fetch billers"),
            "details": body
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Billers fetch failed: {str(e)}"
        )


@router.post("/items")
async def get_payment_items(req: PaymentItemRequest):
    """
    Get payment items (codes) for a specific biller.
    
    Args:
        biller_id: The biller ID from the billers endpoint
    
    Returns payment codes that can be used with validate_customer and pay endpoints.
    """
    try:
        result = get_vas_payment_items(req.biller_id)
        status_code = result.get("status_code")
        body = result.get("body", {})
        
        if status_code == 200:
            return {
                "status": "success",
                "data": body.get("data", {}),
                "response_code": body.get("ResponseCode")
            }
        
        return {
            "status": "error",
            "message": body.get("message", "Failed to fetch payment items"),
            "details": body
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Payment items fetch failed: {str(e)}"
        )


@router.post("/validate")
async def validate_customer(req: ValidateCustomerRequest):
    """
    Validate customer before initiating payment.
    
    Args:
        customer_id: Customer identifier (e.g., meter number, phone number)
        payment_code: Payment code from payment items endpoint
    
    Returns customer details and validation status. ResponseCode 90000 = valid.
    """
    try:
        result = validate_vas_customer(req.customer_id, req.payment_code)
        status_code = result.get("status_code")
        body = result.get("body", {})
        response_code = body.get("data", {}).get("ResponseCode")
        
        if status_code == 200 and response_code == "90000":
            customer_data = body.get("data", {}).get("Customers", [{}])[0] if body.get("data", {}).get("Customers") else {}
            return {
                "status": "success",
                "valid": True,
                "customer": customer_data,
                "response_code": response_code
            }
        
        # 200 but validation failed (customer not found, etc)
        if status_code == 200:
            return {
                "status": "failed",
                "valid": False,
                "response_code": response_code,
                "message": body.get("message", "Customer validation failed"),
                "details": body.get("data", {})
            }
        
        # Non-200 status
        return {
            "status": "error",
            "message": body.get("message", "Validation request failed"),
            "response_code": response_code,
            "details": body
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Customer validation failed: {str(e)}"
        )


@router.post("/pay")
async def pay_bill(req: PayBillRequest):
    """
    Initiate bill payment for a validated customer.
    
    Args:
        customer_id: Customer identifier
        payment_code: Payment code (must be valid for this customer)
        amount: Amount in kobo (₦200 minimum = 20000 kobo)
        customer_mobile: Phone number (optional, for receipt)
        customer_email: Email address (optional, for receipt)
        reference: Unique transaction reference (auto-generated if omitted)
        terminal_id: Terminal ID tracking (default: 3DMO0001)
    
    Returns:
        ResponseCode 90009 = PENDING (normal and expected)
        Use GET /api/bills/transaction to check final status.
    """
    try:
        result = pay_vas_bill(
            customer_id=req.customer_id,
            payment_code=req.payment_code,
            amount=req.amount,
            customer_mobile=req.customer_mobile or "",
            customer_email=req.customer_email or "",
            reference=req.reference,
            terminal_id=req.terminal_id or "3DMO0001"
        )
        
        status_code = result.get("status_code")
        body = result.get("body", {})
        response_code = body.get("data", {}).get("ResponseCode")
        reference = result.get("reference")  # Get from wrapper, not body
        
        if status_code == 200:
            return {
                "status": "initiated",
                "response_code": response_code,
                "response_description": body.get("data", {}).get("ResponseCodeGrouping", ""),
                "reference": reference,
                "message": "Payment initiated. Check status with transaction endpoint.",
                "data": body.get("data", {})
            }
        
        return {
            "status": "error",
            "message": body.get("message", "Payment initiation failed"),
            "response_code": response_code,
            "details": body
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Bill payment failed: {str(e)}"
        )


@router.get("/transaction")
async def get_transaction_status(reference: str):
    """
    Check the final status of a payment transaction.
    
    Args:
        reference: Transaction reference from the pay endpoint response
    
    Returns:
        ResponseCode 90000 = SUCCESSFUL
        Status field indicates: Complete, Pending, Failed, etc.
    """
    if not reference or not reference.strip():
        raise HTTPException(
            status_code=400,
            detail="Transaction reference required"
        )
    
    try:
        result = get_vas_transaction_status(reference.strip())
        status_code = result.get("status_code")
        body = result.get("body", {})
        response_code = body.get("data", {}).get("ResponseCode")
        
        if status_code == 200:
            tx_data = body.get("data", {})
            return {
                "status": "success",
                "reference": reference,
                "response_code": response_code,
                "transaction_status": tx_data.get("Status"),
                "amount": tx_data.get("Amount"),
                "transaction_ref": tx_data.get("TransactionRef"),
                "payment_date": tx_data.get("PaymentDate"),
                "service_name": tx_data.get("ServiceName"),
                "data": tx_data
            }
        
        return {
            "status": "error",
            "message": body.get("message", "Transaction lookup failed"),
            "response_code": response_code,
            "details": body
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Transaction status check failed: {str(e)}"
        )
