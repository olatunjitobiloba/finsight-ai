# services/score_engine.py
# FinSight AI — Core Intelligence Engine
# Owner: Toby
# Handles:
#   1. Financial Health Score (0–100)
#   2. Days to Zero Predictor
#   3. Behavior Pattern Detection
#   4. AI Action Recommendations

from datetime import date, datetime, timedelta
from collections import defaultdict
from typing import Optional
from statistics import median
import re

from services.ai_actions import generate_genuine_actions


# ─────────────────────────────────────────────────────
# SECTION 1 — FINANCIAL HEALTH SCORE
# ─────────────────────────────────────────────────────
#
# Score is built from 5 pillars:
#
# Pillar                Weight    What it measures
# ──────────────────    ──────    ─────────────────────
# Income Stability        25%     Is income consistent?
# Spending Control        25%     Is spending < income?
# Savings Behavior        20%     Is user saving?
# Debt/Bill Regularity    15%     Are bills paid on time?
# Diversity               15%     Spread across categories
#
# Final score → label + color + message

def calculate_score(transactions: list) -> dict:
    """
    Input:  list of transaction dicts
            Each dict must have:
              - amount (float)
              - type ('credit' or 'debit')
              - category (str)
              - transaction_date (str: 'YYYY-MM-DD')

    Output: dict with score, label, color, message,
            pillar breakdown, and top insight
    """

    if not transactions:
        return _empty_score()

    # ── Separate credits and debits
    credits = [t for t in transactions if t.get("type") == "credit"]
    debits  = [t for t in transactions if t.get("type") == "debit"]

    total_income   = sum(t["amount"] for t in credits)
    total_spending = sum(t["amount"] for t in debits)

    # ── PILLAR 1: Income Stability (25 pts)
    # More than 1 income source = stable
    income_score = _score_income_stability(credits)

    # ── PILLAR 2: Spending Control (25 pts)
    # spending < income = good
    spending_score = _score_spending_control(
        credits,
        debits,
        total_income,
        total_spending,
        income_score,
    )

    # ── PILLAR 3: Savings Behavior (20 pts)
    savings_score = _score_savings(transactions)

    # ── PILLAR 4: Bill Regularity (15 pts)
    bill_score = _score_bills(debits)

    # ── PILLAR 5: Category Diversity (15 pts)
    diversity_score = _score_diversity(debits)

    # ── TOTAL
    total = (
        income_score
        + spending_score
        + savings_score
        + bill_score
        + diversity_score
    )
    total = max(0, min(100, round(total)))

    label, color, message = _score_label(total)

    total_flow = total_income + total_spending
    legacy_spending = 100 - ((total_spending / total_flow) * 100) if total_flow else 0

    return {
        "score": total,
        "label": label,
        "color": color,
        "message": message,
        "pillars": {
            "income_stability": round(income_score),
            "spending_control": round(spending_score),
            "savings_behavior": round(savings_score),
            "bill_regularity":  round(bill_score),
            "category_diversity": round(diversity_score),
            "cashflow": total,
            "stability": max(0, min(100, total - 5)),
            "spending": max(0, min(100, round(legacy_spending))),
        },
        "summary": {
            "total_income":   round(total_income, 2),
            "total_spending": round(total_spending, 2),
            "net":            round(total_income - total_spending, 2),
            "transaction_count": len(transactions),
            "credits": round(total_income, 2),
            "debits": round(total_spending, 2),
        }
    }


def _score_income_stability(credits: list) -> float:
    """25 pts max. Rewards consistent, multiple income entries."""
    if not credits:
        return 0.0
    if len(credits) >= 3:
        return 25.0
    if len(credits) == 2:
        return 18.0
    return 10.0  # single income


def _extract_month(value: str) -> Optional[str]:
    """Extract YYYY-MM bucket from transaction date text."""
    if not value:
        return None
    text = str(value)
    if re.match(r"^\d{4}-\d{2}", text):
        return text[:7]
    return None


def _score_spending_control(
    credits: list,
    debits: list,
    income: float,
    spending: float,
    income_stability_score: float,
) -> float:
    """25 pts max. Uses rolling ratios so one-off income months are less punitive."""
    if spending <= 0:
        return 25.0

    monthly_income = defaultdict(float)
    monthly_spending = defaultdict(float)

    for t in credits:
        month = _extract_month(t.get("transaction_date"))
        if month:
            monthly_income[month] += t.get("amount", 0)

    for t in debits:
        month = _extract_month(t.get("transaction_date"))
        if month:
            monthly_spending[month] += t.get("amount", 0)

    months = sorted(set(monthly_income.keys()) | set(monthly_spending.keys()))
    ratios = [
        monthly_spending[m] / monthly_income[m]
        for m in months
        if monthly_income[m] > 0
    ]

    baseline_ratio = median(ratios) if ratios else (spending / income if income > 0 else None)

    current_ratio = None
    if months:
        latest_month = months[-1]
        latest_income = monthly_income.get(latest_month, 0.0)
        latest_spending = monthly_spending.get(latest_month, 0.0)
        if latest_income > 0:
            current_ratio = latest_spending / latest_income
    elif income > 0:
        current_ratio = spending / income

    if current_ratio is None:
        if baseline_ratio is None:
            return 0.0
        no_income_penalty = 0.15 if income_stability_score >= 18 else 0.25
        ratio = baseline_ratio * (1 + no_income_penalty)
    else:
        # Stable inflow gets more smoothing from historical monthly behavior.
        smoothing = min(0.45, max(0.1, (income_stability_score / 25.0) * 0.45))
        reference_ratio = baseline_ratio if baseline_ratio is not None else current_ratio
        ratio = (current_ratio * (1 - smoothing)) + (reference_ratio * smoothing)

    if ratio <= 0.35:
        return 25.0
    if ratio <= 0.5:
        return 18.0
    if ratio <= 0.7:
        return 13.0
    if ratio <= 0.9:
        return 9.0
    if ratio <= 1.0:
        return 8.0
    if ratio <= 1.1:
        return 6.0
    if ratio <= 1.25:
        return 4.0
    if ratio <= 1.5:
        return 2.0
    if ratio <= 1.75:
        return 1.0
    return 0.0


def _score_savings(transactions: list) -> float:
    """20 pts max. Rewards any savings activity."""
    savings_keywords = [
        "savings", "piggyvest", "cowrywise",
        "investment", "stash", "target", "save"
    ]
    for t in transactions:
        desc = (t.get("description") or "").lower()
        cat  = (t.get("category") or "").lower()
        for kw in savings_keywords:
            if kw in desc or kw in cat:
                return 20.0
    return 0.0


def _score_bills(debits: list) -> float:
    """15 pts max. Rewards paying bills (shows responsibility)."""
    bill_keywords = [
        "dstv", "gotv", "electricity", "water",
        "rent", "airtime", "data", "subscription",
        "ikedc", "ekedc", "aedc", "phcn"
    ]
    bill_count = 0
    for t in debits:
        desc = (t.get("description") or "").lower()
        cat  = (t.get("category") or "").lower()
        if _is_fee_or_tax_line(desc):
            continue
        for kw in bill_keywords:
            if kw in desc or kw in cat:
                bill_count += 1
                break
    if bill_count >= 3:
        return 15.0
    if bill_count == 2:
        return 10.0
    if bill_count == 1:
        return 5.0
    return 0.0


def _score_diversity(debits: list) -> float:
    """15 pts max. Rewards spending across multiple categories."""
    total_spending = sum(t.get("amount", 0) for t in debits)
    if total_spending <= 0:
        return 0.0

    by_category = defaultdict(float)
    for t in debits:
        category = t.get("category", "Uncategorized")
        by_category[category] += t.get("amount", 0)

    # Ignore tiny/noise categories so score reflects meaningful behavior spread.
    categories = {
        cat for cat, amount in by_category.items()
        if (amount / total_spending) >= 0.03
    }
    count = len(categories)
    if count >= 5:
        return 15.0
    if count >= 3:
        return 10.0
    if count >= 2:
        return 5.0
    return 0.0


def _score_label(score: int) -> tuple:
    """Returns (label, color, message) based on score."""
    if score >= 80:
        return (
            "Financially Healthy",
            "green",
            "You are managing your money well. Keep it up."
        )
    if score >= 55:
        return (
            "Moderate Risk",
            "yellow",
            "You are doing okay but some habits need attention."
        )
    if score >= 40:
        return (
            "Financially Unstable",
            "orange",
            "Your spending patterns are concerning. Act now."
        )
    return (
        "Critical",
        "red",
        "Your finances are in a dangerous state. Immediate action needed."
    )


def _empty_score() -> dict:
    return {
        "score": 0,
        "label": "No Data",
        "color": "gray",
        "message": "Paste your bank SMS alerts to get your score.",
        "pillars": {},
        "summary": {}
    }


# ─────────────────────────────────────────────────────
# SECTION 2 — DAYS TO ZERO PREDICTOR
# ─────────────────────────────────────────────────────
#
# Formula:
#   daily_burn_rate = total_spending / days_active
#   days_to_zero    = current_balance / daily_burn_rate
#
# This is the WOW #2 moment in the demo.

def days_to_zero(
    transactions: list,
    current_balance: Optional[float] = None
) -> dict:
    """
    Input:
      transactions    — list of transaction dicts
      current_balance — float (from latest SMS balance field)
                        If None, estimated from net flow

    Output: dict with days_remaining, daily_burn,
            prediction_date, urgency, message
    """

    if not transactions:
        return _empty_days()

    debits = [t for t in transactions if t.get("type") == "debit"]
    credits = [t for t in transactions if t.get("type") == "credit"]

    if not debits:
        return _empty_days()

    total_spending = sum(t["amount"] for t in debits)
    total_income   = sum(t["amount"] for t in credits)

    # ── Daily burn rate based on active spending days
    daily_spend = defaultdict(float)
    for t in debits:
        try:
            tx_date = str(t["transaction_date"])
            daily_spend[tx_date] += t["amount"]
        except KeyError:
            continue

    active_spend_days = len(daily_spend) if daily_spend else 0
    if active_spend_days == 0:
        return _empty_days()

    base_burn = total_spending / active_spend_days

    # Add a small volatility buffer when spending is highly concentrated.
    max_day_spend = max(daily_spend.values())
    concentration = (max_day_spend / base_burn) - 1 if base_burn else 0
    volatility_buffer = min(0.12, max(0.0, concentration * 0.031))
    daily_burn = base_burn * (1 + volatility_buffer)

    # ── Estimate balance if not provided
    if current_balance is None or current_balance <= 0:
        net = total_income - total_spending
        # Assume user started with some base amount
        current_balance = max(net, daily_burn * 3)

    if daily_burn <= 0:
        return _empty_days()

    # ── Days remaining
    days_remaining = int(current_balance / daily_burn)
    days_remaining = max(0, days_remaining)

    # ── Prediction date
    prediction_date = (
        date.today() + timedelta(days=days_remaining)
    ).strftime("%B %d, %Y")

    # ── Urgency level
    if days_remaining <= 3:
        urgency = "critical"
    elif days_remaining <= 7:
        urgency = "high"
    elif days_remaining <= 14:
        urgency = "medium"
    else:
        urgency = "low"

    message = (
        f"At your current burn rate, "
        f"you will run out of money in {days_remaining} days "
        f"({prediction_date})."
    )

    return {
        "days_remaining":  days_remaining,
        "daily_burn_rate": round(daily_burn, 2),
        "current_balance": round(current_balance, 2),
        "prediction_date": prediction_date,
        "urgency":         urgency,
        "message":         message
    }


def _empty_days() -> dict:
    return {
        "days_remaining":  None,
        "daily_burn_rate": None,
        "current_balance": None,
        "prediction_date": None,
        "urgency":         "unknown",
        "message":         "Not enough data to predict."
    }


# ─────────────────────────────────────────────────────
# SECTION 3 — BEHAVIOR PATTERN DETECTION
# ─────────────────────────────────────────────────────
#
# Detects 5 patterns:
#   1. Weekend overspending
#   2. Post-salary spike
#   3. Food addiction
#   4. Recurring merchant (loyalty or habit)
#   5. Late-month desperation spending

def detect_patterns(transactions: list) -> dict:
    """
    Input:  list of transaction dicts
    Output: dict with patterns list and top_pattern
            Each pattern has: id, title, detail, severity
    """

    if not transactions:
        return {"patterns": [], "top_pattern": None}

    debits = [t for t in transactions if t.get("type") == "debit"]

    if not debits:
        return {"patterns": [], "top_pattern": None}

    patterns = []

    # ── Pattern 1: Weekend Overspending
    p1 = _detect_weekend_spending(debits)
    if p1:
        patterns.append(p1)

    # ── Pattern 2: Post-Salary Spike
    p2 = _detect_post_salary_spike(transactions)
    if p2:
        patterns.append(p2)

    # ── Pattern 3: Food Overspending
    p3 = _detect_food_addiction(debits)
    if p3:
        patterns.append(p3)

    # ── Pattern 4: Recurring Merchant
    p4 = _detect_recurring_merchant(debits)
    if p4:
        patterns.append(p4)

    # ── Pattern 5: Late-Month Desperation
    p5 = _detect_late_month_spending(debits)
    if p5:
        patterns.append(p5)

    # Sort by severity, then prioritize post-income spikes for action planning.
    severity_order = {"high": 0, "medium": 1, "low": 2}
    pattern_priority = {
        "post_salary_spike": 0,
        "post_salary_watch": 1,
        "weekend_overspend": 1,
        "food_overspend": 2,
        "late_month_desperation": 3,
        "recurring_merchant": 4,
    }
    patterns.sort(
        key=lambda x: (
            severity_order.get(x["severity"], 3),
            pattern_priority.get(x["id"], 99)
        )
    )

    return {
        "patterns":    patterns,
        "top_pattern": patterns[0] if patterns else None,
        "count":       len(patterns)
    }


def _detect_weekend_spending(debits: list) -> Optional[dict]:
    """Detects if user spends significantly more on weekends."""
    weekend_total = 0.0
    weekday_total = 0.0
    weekend_days = set()
    weekday_days = set()

    for t in debits:
        try:
            d = datetime.strptime(str(t["transaction_date"]), "%Y-%m-%d")
            if d.weekday() >= 5:  # Saturday=5, Sunday=6
                weekend_total += t["amount"]
                weekend_days.add(d.date())
            else:
                weekday_total += t["amount"]
                weekday_days.add(d.date())
        except (ValueError, KeyError):
            continue

    if not weekend_days or not weekday_days:
        return None

    total_spending = weekend_total + weekday_total
    active_spend_days = len(weekend_days) + len(weekday_days)
    if active_spend_days == 0:
        return None

    avg_daily_spend = total_spending / active_spend_days

    # Guardrail: avoid noisy alerts for very low spend users.
    if total_spending < 60000 or avg_daily_spend < 5000:
        return None

    # Require a reasonable activity footprint so tiny samples do not overfit.
    if len(weekend_days) < 2 or len(weekday_days) < 4:
        return None

    weekend_avg = weekend_total / len(weekend_days)
    weekday_avg = weekday_total / len(weekday_days)

    if weekday_avg <= 0:
        return None

    weekend_share = weekend_total / total_spending
    avg_gap = weekend_avg - weekday_avg

    # Stricter trigger: higher ratio + meaningful absolute difference + meaningful spend share.
    if weekend_avg > weekday_avg * 1.4 and avg_gap >= 3000 and weekend_share >= 0.33:
        pct = round(((weekend_avg - weekday_avg) / weekday_avg) * 100)
        return {
            "id":       "weekend_overspend",
            "title":    "Weekend Overspending",
            "detail":   f"You spend {pct}% more on weekends than weekdays. "
                        f"Weekend avg: ₦{weekend_avg:,.0f} vs "
                        f"weekday avg: ₦{weekday_avg:,.0f}.",
            "severity": "high" if pct >= 85 else "medium"
        }
    return None


def _detect_post_salary_spike(transactions: list) -> Optional[dict]:
    """Detects spending spike in 7 days after receiving income."""
    credits = [t for t in transactions if t.get("type") == "credit"]
    debits  = [t for t in transactions if t.get("type") == "debit"]

    if not credits or not debits:
        return None

    credit_dates = []
    for credit in credits:
        try:
            credit_dates.append(
                datetime.strptime(str(credit["transaction_date"]), "%Y-%m-%d").date()
            )
        except (ValueError, KeyError):
            continue

    if not credit_dates:
        return None

    # Focus on discretionary behavior. Fixed bills/savings can cluster after salary
    # and should not, by themselves, create a spike alert.
    discretionary_debits = [
        t for t in debits if not _is_essential_post_income_line(t)
    ]

    if not discretionary_debits:
        return None

    spike_spending = 0.0
    spike_count = 0
    spike_days = set()
    spend_days = set()
    for debit in discretionary_debits:
        try:
            debit_date = datetime.strptime(str(debit["transaction_date"]), "%Y-%m-%d").date()
        except (ValueError, KeyError):
            continue

        spend_days.add(debit_date)

        # Count a debit once if it falls in any 7-day post-income window.
        in_window = any(cd <= debit_date <= (cd + timedelta(days=7)) for cd in credit_dates)
        if in_window:
            spike_spending += debit["amount"]
            spike_count += 1
            spike_days.add(debit_date)

    total_spending = sum(t["amount"] for t in discretionary_debits)

    if total_spending == 0:
        return None

    active_spend_days = len(spend_days)
    if active_spend_days == 0:
        return None

    avg_daily_spend = total_spending / active_spend_days

    # Guardrail: low-spend users should not be flagged by ratio-only effects.
    if total_spending < 50000 or avg_daily_spend < 4500:
        return None

    spike_ratio = spike_spending / total_spending

    # Require enough post-income activity and absolute value, not just percentage.
    if spike_count < 2 or len(spike_days) < 2:
        return None

    if spike_ratio > 0.65 and spike_spending >= 55000 and spike_count >= 3 and len(spike_days) >= 3:
        pct = round(spike_ratio * 100)
        return {
            "id":       "post_salary_spike",
            "title":    "Post-Income Spending Spike",
            "detail":   f"You spend {pct}% of your discretionary money within 7 days "
                        f"of receiving income. "
                        f"This leaves you vulnerable for the rest of the month.",
            "severity": "high"
        }

    # Watch band: show context for moderate concentration without alarmist severity.
    if spike_ratio > 0.5 and spike_spending >= 40000:
        pct = round(spike_ratio * 100)
        return {
            "id":       "post_salary_watch",
            "title":    "Post-Income Spend Watch",
            "detail":   f"About {pct}% of your discretionary spend happens within 7 days "
                        f"after income lands. Consider spreading non-essential purchases "
                        f"across the month to keep more buffer.",
            "severity": "low"
        }

    return None


def _is_essential_post_income_line(transaction: dict) -> bool:
    desc = (transaction.get("description") or "").lower()
    cat = (transaction.get("category") or "").lower()

    if _is_fee_or_tax_line(desc):
        return True

    bill_keywords = [
        "dstv", "gotv", "electricity", "water",
        "rent", "airtime", "data", "subscription",
        "ikedc", "ekedc", "aedc", "phcn",
    ]
    if any(kw in desc or kw in cat for kw in bill_keywords):
        return True

    savings_keywords = [
        "savings", "piggyvest", "cowrywise",
        "investment", "stash", "target", "save",
    ]
    if any(kw in desc or kw in cat for kw in savings_keywords):
        return True

    return False


def _detect_food_addiction(debits: list) -> Optional[dict]:
    """Detects if food spending is disproportionately high."""
    food_total = 0.0
    total = 0.0

    for t in debits:
        total += t["amount"]
        cat = (t.get("category") or "").lower()
        desc = (t.get("description") or "").lower()
        if "food" in cat or any(
            kw in desc for kw in [
                "food", "restaurant", "eatery", "kfc",
                "chicken", "dominos", "shoprite", "bukka"
            ]
        ):
            food_total += t["amount"]
        elif "entertainment" in cat or any(
            kw in desc for kw in ["club", "cinema", "outing"]
        ):
            # Count part of outings as discretionary food/lifestyle spend.
            food_total += t["amount"] * 0.65

    if total == 0:
        return None

    ratio = food_total / total

    if ratio > 0.15:  # food is more than 15% of spending
        pct = round(ratio * 100)
        return {
            "id":       "food_overspend",
            "title":    "High Food Spending",
            "detail":   f"Food accounts for {pct}% of your total spending. "
                        f"Recommended maximum is 30%. "
                        f"You could save ₦{(food_total * 0.2):,.0f} "
                        f"by cutting food spend by 20%.",
            "severity": "medium"
        }
    return None


def _detect_recurring_merchant(debits: list) -> Optional[dict]:
    """Detects if user repeatedly spends at same merchant."""
    merchant_count = defaultdict(int)
    merchant_total = defaultdict(float)

    for t in debits:
        raw_desc = (t.get("description") or "unknown").lower().strip()
        amount = float(t.get("amount", 0) or 0)

        # Ignore VAT/commission/fee lines so we report true recurring spend.
        if _is_fee_or_tax_line(raw_desc):
            continue

        desc = _normalize_merchant(raw_desc)
        merchant_count[desc] += 1
        merchant_total[desc] += amount

    # Find merchant visited 3+ times
    for merchant, count in merchant_count.items():
        if count >= 3:
            total = merchant_total[merchant]
            return {
                "id":       "recurring_merchant",
                "title":    "Recurring Spending Pattern",
                "detail":   f"You have spent at '{merchant}' {count} times, "
                            f"totalling ₦{total:,.0f}. "
                            f"Consider if this is intentional.",
                "severity": "low"
            }
    return None


def _is_fee_or_tax_line(description: str) -> bool:
    desc = (description or "").lower()
    fee_keywords = ["vat", "commission", "stamp duty", "sms alert fee", "charge"]
    return any(keyword in desc for keyword in fee_keywords)


def _normalize_merchant(description: str) -> str:
    desc = (description or "unknown").lower().strip()
    desc = re.sub(r"\s+", " ", desc)
    desc = re.sub(r"^mobile trf to\s+", "", desc)
    desc = re.sub(r"^transfer to\s+", "", desc)
    return desc


def _detect_late_month_spending(debits: list) -> Optional[dict]:
    """Detects if user spends heavily in last 7 days of month."""
    early_total = 0.0
    late_total  = 0.0

    for t in debits:
        try:
            d = datetime.strptime(
                str(t["transaction_date"]), "%Y-%m-%d"
            )
            if d.day >= 24:  # last 7 days of month
                late_total  += t["amount"]
            elif d.day <= 7:  # first 7 days
                early_total += t["amount"]
        except (ValueError, KeyError):
            continue

    if early_total == 0 or late_total == 0:
        return None

    if late_total > early_total * 2.0:
        return {
            "id":       "late_month_desperation",
            "title":    "Late-Month Spending Spike",
            "detail":   "You spend significantly more in the last week "
                        "of the month than the first week. "
                        "This suggests financial stress near month-end.",
            "severity": "medium"
        }
    return None


# ─────────────────────────────────────────────────────
# SECTION 4 — AI ACTION RECOMMENDATIONS
# ─────────────────────────────────────────────────────
#
# "Fix This" button logic
# Returns 3 precise, actionable recommendations
# based on score + patterns + days_to_zero

def generate_actions(
    score_result: dict,
    days_result:  dict,
    pattern_result: dict,
    raw_transactions: Optional[list] = None,
    user_context: Optional[dict] = None
) -> list:
    """
    Input: outputs from calculate_score(), days_to_zero(), detect_patterns(),
           plus optional raw transaction and user context.

    Output: list of up to 5 personalized action dicts from the genuine,
            fully data-driven action engine.
    """
    return generate_genuine_actions(
        score_result=score_result,
        days_result=days_result,
        pattern_result=pattern_result,
        raw_transactions=raw_transactions or [],
        user_context=user_context,
    )