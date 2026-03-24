# api/transactions.py
# FinSight AI — Transaction CRUD Endpoints
# Owner: Margaret (Backend Track)

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Optional
from datetime import date

# Import DB layer — if not ready, stub is used automatically
try:
    from services.db import (
        save_transaction,
        get_user_transactions,
        delete_transaction,
        ping
    )
    DB_READY = True
except Exception:
    DB_READY = False

    # ── STUBS (if db.py is not ready) ─────────────────
    def save_transaction(user_id, data):
        return {"status": "stub", "data": [{"id": "stub-001"}]}

    def get_user_transactions(user_id, limit=50):
        return [
            {"id": "stub-001", "amount": 5000,
             "type": "debit", "category": "Food",
             "description": "Lunch", "transaction_date": "2026-03-18"},
        ]

    def delete_transaction(txn_id, user_id):
        return {"status": "stub"}

    def ping():
        return False


app = FastAPI(title="FinSight AI API", version="1.0.0")

# ── CORS — allow PWA frontend ──────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── REQUEST MODELS ─────────────────────────────────────

class TransactionIn(BaseModel):
    amount: float
    type: str
    category: str = "Uncategorized"
    description: str = ""
    transaction_date: str = str(date.today())

    @validator("type")
    def validate_type(cls, v):
        if v not in ("credit", "debit"):
            raise ValueError("type must be credit or debit")
        return v

    @validator("amount")
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("amount must be greater than 0")
        return v


# ── HELPER — extract user_id from header ──────────────
def get_user_id(x_user_id: Optional[str] = Header(None)) -> str:
    """
    For MVP — user_id passed as header.
    Replace with JWT decode in production.
    """
    if not x_user_id:
        raise HTTPException(
            status_code=401,
            detail="Missing X-User-Id header"
        )
    return x_user_id


# ── ROUTES ────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    """Ping endpoint — keeps Vercel warm, used by cron."""
    return {
        "status": "ok",
        "db": ping() if DB_READY else "stub",
        "version": "1.0.0"
    }


@app.post("/api/transactions")
def create_transaction(
    body: TransactionIn,
    x_user_id: Optional[str] = Header(None)
):
    """Add a new transaction for a user."""
    user_id = get_user_id(x_user_id)

    result = save_transaction(user_id, body.dict())

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    if result["status"] == "duplicate":
        raise HTTPException(status_code=409, detail="Duplicate transaction")

    return {
        "status": "success",
        "message": "Transaction saved",
        "data": result["data"]
    }


@app.get("/api/transactions")
def list_transactions(
    limit: int = 50,
    x_user_id: Optional[str] = Header(None)
):
    """Get all transactions for a user."""
    user_id = get_user_id(x_user_id)

    transactions = get_user_transactions(user_id, limit=limit)

    return {
        "status": "success",
        "count": len(transactions),
        "data": transactions
    }


@app.delete("/api/transactions/{transaction_id}")
def remove_transaction(
    transaction_id: str,
    x_user_id: Optional[str] = Header(None)
):
    """Delete a transaction by ID."""
    user_id = get_user_id(x_user_id)

    result = delete_transaction(transaction_id, user_id)

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    return {"status": "success", "message": "Transaction deleted"}