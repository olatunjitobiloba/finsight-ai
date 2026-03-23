# services/db.py
# FinSight AI — Supabase Database Layer
# Owner: Backend Partner
# All database operations go through this file

import os
import hashlib
from datetime import date
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv(".env.local")

# ── Client ────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL") or os.environ.get("supabase_url")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("supabase_service_key")

supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        supabase = None


def get_client() -> Client:
    """Return the initialized Supabase client (legacy compatibility)."""
    return supabase


# ── TRANSACTIONS ───────────────────────────────────────

def save_transaction(user_id: str, data: dict) -> dict:
    """
    Save a single transaction.
    data must have: amount, type, category, description, transaction_date
    """
    if supabase is None:
        return {"status": "error", "message": "Database not configured"}

    try:
        # Deduplication hash
        raw = f"{user_id}{data['amount']}{data['transaction_date']}{data['description']}"
        data_hash = hashlib.sha256(raw.encode()).hexdigest()

        result = supabase.table("transactions").insert({
            "user_id": user_id,
            "amount": float(data["amount"]),
            "type": data["type"],
            "category": data.get("category", "Uncategorized"),
            "description": data.get("description", ""),
            "transaction_date": str(data["transaction_date"]),
            "source": data.get("source", "manual"),
            "hash": data_hash
        }).execute()

        return {"status": "success", "data": result.data}

    except Exception as e:
        # Duplicate hash — silently skip
        if "duplicate" in str(e).lower():
            return {"status": "duplicate", "data": None}
        return {"status": "error", "message": str(e)}


def get_user_transactions(user_id: str, limit: int = 50) -> list:
    """
    Fetch last N transactions for a user, newest first.
    """
    if supabase is None:
        return []

    try:
        result = (
            supabase.table("transactions")
            .select("*")
            .eq("user_id", user_id)
            .order("transaction_date", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    except Exception as e:
        print(f"[DB ERROR] get_user_transactions: {e}")
        return []


def get_transactions(user_id: str, limit: int = 50) -> list:
    """Backward-compatible alias for get_user_transactions."""
    return get_user_transactions(user_id, limit=limit)


def clear_user_transactions(user_id: str) -> dict:
    """Delete all transactions owned by a user."""
    try:
        supabase.table("transactions").delete().eq("user_id", user_id).execute()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def delete_transaction(transaction_id: str, user_id: str) -> dict:
    """
    Delete a transaction by ID. Verifies ownership.
    """
    if supabase is None:
        return {"status": "error", "message": "Database not configured"}

    try:
        result = (
            supabase.table("transactions")
            .delete()
            .eq("id", transaction_id)
            .eq("user_id", user_id)
            .execute()
        )
        return {"status": "success"}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── FINANCIAL SCORES ───────────────────────────────────

def save_score(user_id: str, score: int, grade: str, verdict: str) -> dict:
    """
    Save or update today's score for a user.
    One score per user per day (upsert).
    """
    if supabase is None:
        return {"status": "error", "message": "Database not configured"}

    try:
        result = supabase.table("financial_scores").upsert({
            "user_id": user_id,
            "score": score,
            "grade": grade,
            "verdict": verdict,
            "computed_at": str(date.today())
        }, on_conflict="user_id,computed_at").execute()

        return {"status": "success", "data": result.data}

    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_latest_score(user_id: str) -> dict | None:
    """
    Get the most recent score for a user.
    Returns None if no score exists yet.
    """
    if supabase is None:
        return None

    try:
        result = (
            supabase.table("financial_scores")
            .select("*")
            .eq("user_id", user_id)
            .order("computed_at", desc=True)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]
        return None

    except Exception as e:
        print(f"[DB ERROR] get_latest_score: {e}")
        return None


# ── INSIGHTS ───────────────────────────────────────────

def save_insight(user_id: str, content: str) -> dict:
    """
    Save an AI-generated insight for a user.
    """
    if supabase is None:
        return {"status": "error", "message": "Database not configured"}

    try:
        result = supabase.table("insights").insert({
            "user_id": user_id,
            "content": content
        }).execute()

        return {"status": "success", "data": result.data}

    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_latest_insights(user_id: str, limit: int = 3) -> list:
    """
    Get the most recent AI insights for a user.
    """
    if supabase is None:
        return []

    try:
        result = (
            supabase.table("insights")
            .select("*")
            .eq("user_id", user_id)
            .order("generated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    except Exception as e:
        print(f"[DB ERROR] get_latest_insights: {e}")
        return []


# ── HEALTH CHECK ───────────────────────────────────────

def ping() -> bool:
    """
    Returns True if Supabase connection is alive.
    Used by /api/health endpoint.
    """
    if supabase is None:
        return False

    try:
        supabase.table("transactions").select("id").limit(1).execute()
        return True
    except Exception:
        return False


__all__ = [
    "get_client",
    "save_transaction",
    "get_user_transactions",
    "get_transactions",
    "clear_user_transactions",
    "delete_transaction",
    "save_score",
    "get_latest_score",
    "save_insight",
    "get_latest_insights",
    "ping",
]