from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from services.score_engine import calculate_score, days_to_zero, detect_patterns

router = APIRouter()


class Transaction(BaseModel):
    amount: float
    type: str
    category: Optional[str] = "Uncategorized"
    description: Optional[str] = ""
    transaction_date: Optional[str] = "2026-03-01"


class ScoreRequest(BaseModel):
    transactions: List[Transaction]
    balance: Optional[float] = None


@router.post("/api/score")
def score_endpoint(request: ScoreRequest):
    txns = [t.model_dump() for t in request.transactions]
    return {
        "score": calculate_score(txns),
        "days_to_zero": days_to_zero(txns, request.balance),
        "patterns": detect_patterns(txns),
    }