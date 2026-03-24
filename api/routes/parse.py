"""
Parse API Routes - SMS and CSV parsing endpoints
"""

from fastapi import APIRouter, HTTPException, Form, File, UploadFile
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from services.sms_parser import parse_sms, parse_multiple_sms
from services.csv_parser import parse_csv
from services.interswitch import simulate_saving, simulate_savings, simulate_bill_optimization

router = APIRouter(prefix="/api", tags=["parse"])


class SMSParseRequest(BaseModel):
    """Request model for SMS parsing"""
    sms_text: str
    bank_type: Optional[str] = None


class SMSParseResponse(BaseModel):
    """Response model for SMS parsing"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class CSVParseResponse(BaseModel):
    """Response model for CSV parsing"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SavingsPlanRequest(BaseModel):
    """Request model for savings plan"""
    amount: float
    plan_type: str
    user_profile: Optional[Dict[str, Any]] = None


class SavingsAnalysisRequest(BaseModel):
    """Request model for savings analysis"""
    transactions: List[Dict[str, Any]]
    user_profile: Optional[Dict[str, Any]] = None


class BillOptimizationRequest(BaseModel):
    """Request model for bill optimization"""
    transactions: List[Dict[str, Any]]


@router.post("/parse/sms", response_model=SMSParseResponse)
async def parse_sms_endpoint(request: SMSParseRequest):
    """
    Parse a single SMS message and extract transaction details.
    
    Args:
        request: SMS text and optional bank type
        
    Returns:
        Parsed transaction data or error
    """
    try:
        result = parse_sms(request.sms_text, request.bank_type)
        
        if result:
            return SMSParseResponse(
                success=True,
                data=result,
                error=None
            )
        else:
            return SMSParseResponse(
                success=False,
                data=None,
                error="Failed to parse SMS. Check format and bank type."
            )
            
    except Exception as e:
        return SMSParseResponse(
            success=False,
            data=None,
            error=f"SMS parsing error: {str(e)}"
        )


@router.post("/parse/sms/batch", response_model=SMSParseResponse)
async def parse_multiple_sms_endpoint(request: SMSParseRequest):
    """
    Parse multiple SMS messages (for batch processing).
    
    Args:
        request: SMS text and optional bank type (applied to all)
        
    Returns:
        Batch parsing results with statistics
    """
    try:
        # For demo purposes, split single SMS by lines for batch testing
        # In real implementation, this would accept a list of SMS messages
        sms_list = request.sms_text.strip().split('\n\n')
        sms_list = [sms.strip() for sms in sms_list if sms.strip()]
        
        result = parse_multiple_sms(sms_list, request.bank_type)
        
        return SMSParseResponse(
            success=True,
            data=result,
            error=None
        )
            
    except Exception as e:
        return SMSParseResponse(
            success=False,
            data=None,
            error=f"Batch SMS parsing error: {str(e)}"
        )


@router.post("/parse/csv", response_model=CSVParseResponse)
async def parse_csv_endpoint(file: UploadFile = File(...)):
    """
    Parse CSV file and extract transaction data.
    
    Args:
        file: CSV file upload
        
    Returns:
        Parsed transaction data with statistics
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Parse CSV
        result = parse_csv(csv_content)
        
        return CSVParseResponse(
            success=True,
            data=result,
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return CSVParseResponse(
            success=False,
            data=None,
            error=f"CSV parsing error: {str(e)}"
        )


@router.post("/parse/csv/text", response_model=CSVParseResponse)
async def parse_csv_text_endpoint(csv_text: str = Form(...)):
    """
    Parse CSV text and extract transaction data.
    
    Args:
        csv_text: CSV content as text
        
    Returns:
        Parsed transaction data with statistics
    """
    try:
        result = parse_csv(csv_text)
        
        return CSVParseResponse(
            success=True,
            data=result,
            error=None
        )
        
    except Exception as e:
        return CSVParseResponse(
            success=False,
            data=None,
            error=f"CSV parsing error: {str(e)}"
        )


@router.post("/savings/plan")
async def create_savings_plan(request: SavingsPlanRequest):
    """
    Create a savings plan for the user.
    
    Args:
        request: Amount, plan type, and optional user profile
        
    Returns:
        Savings plan details and integration results
    """
    try:
        result = simulate_saving(request.amount, request.plan_type, request.user_profile)
        
        if result.get("success", False):
            return {
                "success": True,
                "data": result,
                "message": result.get("message", "Savings plan created successfully")
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Failed to create savings plan"),
                "data": None
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Savings plan creation error: {str(e)}",
            "data": None
        }


@router.post("/savings/analyze")
async def analyze_savings_endpoint(request: SavingsAnalysisRequest):
    """
    Analyze spending patterns and provide savings recommendations.
    
    Args:
        request: Transaction list and optional user profile
        
    Returns:
        Savings analysis and recommendations
    """
    try:
        result = simulate_savings(request.transactions, request.user_profile)
        
        return {
            "success": True,
            "data": result,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Savings analysis error: {str(e)}",
            "data": None
        }


@router.post("/savings/bills/optimize")
async def optimize_bills_endpoint(request: BillOptimizationRequest):
    """
    Analyze recurring bills and provide optimization strategies.
    
    Args:
        request: Transaction list
        
    Returns:
        Bill optimization recommendations
    """
    try:
        result = simulate_bill_optimization(request.transactions)
        
        return {
            "success": True,
            "data": result,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Bill optimization error: {str(e)}",
            "data": None
        }


@router.get("/parse/banks")
async def get_supported_banks():
    """
    Get list of supported banks for SMS parsing.
    
    Returns:
        List of supported banks with examples
    """
    return {
        "success": True,
        "data": {
            "supported_banks": [
                {
                    "code": "access",
                    "name": "Access Bank",
                    "example": "Credit Amt:NGN2,000.00 Acc:190**678 Desc:247HYDR260770074/tt Date:18/03/2026 Avail Bal:NGN8,932.45"
                },
                {
                    "code": "gt",
                    "name": "GTBank",
                    "example": "Acct: ****728 Amt: NGN75,000.00 CR Desc: -TRANSFER FROM ADISABABA GLOBAL CONCEPTS-OPAY-ADIS Avail Bal: NGN104,657.26 Date: 2026-03-18 6:26:55 PM"
                },
                {
                    "code": "first",
                    "name": "First Bank",
                    "example": "Debit: 2314XXXX455 Amt: NGN6,000.00 Date: 19-MAR-2026 14:55:21 Desc: POS TRAN-FLAT /XX/NG/1. Bal: NGN5,967.81CR. Dial *894*11# to get loan"
                },
                {
                    "code": "zenith",
                    "name": "Zenith Bank",
                    "example": "Not implemented yet"
                },
                {
                    "code": "uba",
                    "name": "United Bank for Africa (UBA)",
                    "example": "Not implemented yet"
                }
            ],
            "plan_types": ["weekly", "monthly", "quarterly", "custom"],
            "supported_formats": ["sms", "csv"]
        }
    }


@router.get("/parse/demo")
async def get_demo_data():
    """
    Get demo data for testing the parsing endpoints.
    
    Returns:
        Sample SMS messages and CSV data
    """
    from services.demo_seeder import SAMPLE_SMS_MESSAGES, SAMPLE_CSV_DATA
    
    return {
        "success": True,
        "data": {
            "sample_sms": SAMPLE_SMS_MESSAGES,
            "sample_csv": SAMPLE_CSV_DATA,
            "usage_examples": {
                "sms_single": "POST /api/parse/sms with {'sms_text': 'your_sms', 'bank_type': 'access'}",
                "sms_batch": "POST /api/parse/sms/batch with multiple SMS separated by double newlines",
                "csv_file": "POST /api/parse/csv with file upload",
                "csv_text": "POST /api/parse/csv/text with csv_text form field",
                "savings_plan": "POST /api/savings/plan with {'amount': 5000, 'plan_type': 'monthly'}",
                "analyze_savings": "POST /api/savings/analyze with transaction list"
            }
        }
    }
