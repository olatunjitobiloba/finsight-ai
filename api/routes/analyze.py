# api/routes/analyze.py
# FinSight AI — Main Analysis Endpoint
# Owner: Margaret
#
# This is the single most important file in the backend.
# The entire demo flows through POST /api/analyze
#
# Flow:
#   1. Receive SMS text from frontend
#   2. Parse SMS → extract transactions
#   3. Save transactions to Supabase
#   4. Run score engine
#   5. Run days-to-zero predictor
#   6. Run behavior pattern detection
#   7. Generate AI actions
#   8. Return everything in one response

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Internal services
from services.sms_parser   import parse_multiple_sms
from services.score_engine import (
    calculate_score,
    days_to_zero,
    detect_patterns,
    generate_actions
)
from services.db import save_transaction, get_user_transactions

router = APIRouter()


# ── REQUEST MODEL ──────────────────────────────────
class AnalyzeRequest(BaseModel):
    sms_text:   str
    bank_type:  Optional[str] = None
    user_id:    Optional[str] = "demo-user"
    balance:    Optional[float] = None   # current balance if known


class AnalyzeTransactionsRequest(BaseModel):
    """Accept pre-parsed transactions directly (e.g., from PDF parser)"""
    transactions: List[Dict[str, Any]]
    user_id:    Optional[str] = "demo-user"
    balance:    Optional[float] = None


# ── RESPONSE STRUCTURE ─────────────────────────────
# (FastAPI auto-serializes — no need to define full model)


# ── MAIN ENDPOINT ──────────────────────────────────
@router.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    """
    Master endpoint. Takes raw SMS text.
    Returns full financial analysis.
    """

    # ── 1. Validate input
    if not request.sms_text or len(request.sms_text.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="SMS text is too short. Please paste your bank alerts."
        )

    # ── 2. Split SMS by newline — each line is one SMS
    sms_lines = [
        line.strip()
        for line in request.sms_text.strip().split("\n")
        if line.strip()
    ]

    if not sms_lines:
        raise HTTPException(
            status_code=400,
            detail="No valid SMS messages found."
        )

    # ── 3. Parse SMS messages
    try:
        parse_result = parse_multiple_sms(sms_lines, request.bank_type)
        transactions = parse_result.get("parsed", [])
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"SMS parsing failed: {str(e)}"
        )

    # ── 4. If nothing parsed, return graceful error
    if not transactions:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Could not extract transactions from SMS.",
                "hint": "Make sure you paste actual Nigerian bank SMS alerts.",
                "failed_count": len(sms_lines)
            }
        )

    # ── 5. Save to Supabase (non-blocking — don't fail if DB is slow)
    saved_count = 0
    try:
        for txn in transactions:
            result = save_transaction(request.user_id, txn)
            if result:
                saved_count += 1
    except Exception:
        # DB failure should NOT break the demo
        # Log it but continue
        pass

    # ── 6. Get balance from latest SMS if not provided
    balance = request.balance
    if balance is None:
        for txn in reversed(transactions):
            if txn.get("balance") and txn["balance"] > 0:
                balance = txn["balance"]
                break

    # ── 7. Run score engine
    try:
        score_result = calculate_score(transactions)
    except Exception as e:
        score_result = {
            "score": 0,
            "label": "Error",
            "color": "gray",
            "message": "Score calculation failed.",
            "pillars": {},
            "summary": {}
        }

    # ── 8. Run days-to-zero predictor
    try:
        days_result = days_to_zero(transactions, current_balance=balance)
    except Exception as e:
        days_result = {
            "days_remaining": None,
            "daily_burn_rate": None,
            "urgency": "unknown",
            "message": "Prediction unavailable."
        }

    # ── 9. Run behavior pattern detection
    try:
        pattern_result = detect_patterns(transactions)
    except Exception as e:
        pattern_result = {"patterns": [], "count": 0, "top_pattern": None}

    # ── 10. Generate AI actions
    try:
        actions = generate_actions(
            score_result,
            days_result,
            pattern_result,
            raw_transactions=transactions,
        )
    except Exception as e:
        actions = []

    # ── 11. Build and return full response
    return {
        "success": True,
        "user_id": request.user_id,

        # Core intelligence
        "score":       score_result,
        "days_to_zero": days_result,
        "patterns":    pattern_result,
        "actions":     actions,

        # Parse metadata
        "parse_summary": {
            "sms_received":   len(sms_lines),
            "transactions_parsed": len(transactions),
            "transactions_saved":  saved_count,
            "parse_rate": parse_result.get("success_rate", 0),
            "bank_type_used": request.bank_type
        },

        # Transaction list (for frontend timeline)
        "transactions": transactions
    }


# ── DIRECT TRANSACTIONS ANALYSIS ENDPOINT ─────────
# This endpoint accepts pre-parsed transactions (e.g., from PDF parser)
# and skips the SMS parsing step entirely.
@router.post("/api/analyze/transactions")
async def analyze_transactions(request: AnalyzeTransactionsRequest):
    """
    Analyze pre-parsed transactions directly.
    
    Used when:
    - PDF parser already has extracted transactions
    - CSV parser already has extracted transactions
    - Need to skip SMS parsing step
    
    Args:
        transactions: List of transaction dicts with amount, date, type, description, etc.
        user_id: User identifier
        balance: Current balance (optional)
        
    Returns:
        Full financial analysis (score, days-to-zero, patterns, etc.)
    """
    
    # ── 1. Validate input
    transactions = request.transactions or []
    if not transactions or not isinstance(transactions, list):
        raise HTTPException(
            status_code=400,
            detail="Transactions must be a non-empty list"
        )
    
    # ── 2. Save to Supabase (non-blocking)
    saved_count = 0
    try:
        for txn in transactions:
            result = save_transaction(request.user_id, txn)
            if result:
                saved_count += 1
    except Exception:
        # DB failure should NOT break the analysis
        pass
    
    # ── 3. Get balance from transactions if not provided
    balance = request.balance
    if balance is None:
        for txn in reversed(transactions):
            if txn.get("balance") and txn["balance"] > 0:
                balance = txn["balance"]
                break
    
    # ── 4. Run score engine
    try:
        score_result = calculate_score(transactions)
    except Exception as e:
        score_result = {
            "score": 0,
            "label": "Error",
            "color": "gray",
            "message": "Score calculation failed.",
            "pillars": {},
            "summary": {}
        }
    
    # ── 5. Run days-to-zero predictor
    try:
        days_result = days_to_zero(transactions, current_balance=balance)
    except Exception as e:
        days_result = {
            "days_remaining": None,
            "daily_burn_rate": None,
            "urgency": "unknown",
            "message": "Prediction unavailable."
        }
    
    # ── 6. Run behavior pattern detection
    try:
        pattern_result = detect_patterns(transactions)
    except Exception as e:
        pattern_result = {"patterns": [], "count": 0, "top_pattern": None}
    
    # ── 7. Generate AI actions
    try:
        actions = generate_actions(
            score_result,
            days_result,
            pattern_result,
            raw_transactions=transactions,
        )
    except Exception as e:
        actions = []
    
    # ── 8. Build and return full response
    return {
        "success": True,
        "user_id": request.user_id,
        
        # Core intelligence
        "score":       score_result,
        "days_to_zero": days_result,
        "patterns":    pattern_result,
        "actions":     actions,
        
        # Parse metadata
        "parse_summary": {
            "source": "direct",
            "transactions_received": len(transactions),
            "transactions_saved":  saved_count
        },
        
        # Transaction list (for frontend timeline)
        "transactions": transactions
    }


# ── HISTORY ENDPOINT ───────────────────────────────
@router.get("/api/history/{user_id}")
async def get_history(user_id: str):
    """
    Returns all saved transactions for a user.
    Used to re-analyze without re-pasting SMS.
    """
    try:
        transactions = get_user_transactions(user_id)
        if not transactions:
            return {"transactions": [], "message": "No history found."}

        score_result   = calculate_score(transactions)
        days_result    = days_to_zero(transactions)
        pattern_result = detect_patterns(transactions)
        actions        = generate_actions(
            score_result,
            days_result,
            pattern_result,
            raw_transactions=transactions,
        )

        return {
            "success": True,
            "user_id": user_id,
            "score":        score_result,
            "days_to_zero": days_result,
            "patterns":     pattern_result,
            "actions":      actions,
            "transactions": transactions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))