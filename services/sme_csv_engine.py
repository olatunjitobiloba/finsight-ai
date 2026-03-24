# services/sme_csv_engine.py
# FinSight AI — SME CSV Classifier, Validator & Analyser
# Owner: Pogbe
#
# Accepts: Sales, Expense, Invoice, Inventory, Payroll CSVs
# Rejects: Calendars, schedules, contact lists, anything non-financial
# Calculates: Cash Flow, Burn Rate, Days to Zero, Health Score
# Explains: In plain language, derived from actual numbers

import csv
import io
import re
from typing import Optional


# ── CSV TYPE SIGNATURES ───────────────────────────
# Each type has required and optional column keywords
# We score each CSV against all types and pick the best match

CSV_SIGNATURES = {
    "sales": {
        "required": [
            ["revenue", "sales", "income", "amount", "total"],
            ["date", "period", "month", "week", "day"]
        ],
        "optional": ["product", "item", "customer", "qty", "quantity",
                     "unit", "price", "invoice", "order"],
        "min_score": 1
    },
    "expense": {
        "required": [
            ["expense", "cost", "spend", "payment", "amount", "debit"],
            ["date", "period", "month", "category", "description"]
        ],
        "optional": ["vendor", "supplier", "category", "type",
                     "receipt", "approved", "department"],
        "min_score": 1
    },
    "invoice": {
        "required": [
            ["invoice", "amount", "total", "due", "balance"],
            ["client", "customer", "date", "status", "paid"]
        ],
        "optional": ["overdue", "outstanding", "reference",
                     "payment_date", "terms"],
        "min_score": 1
    },
    "inventory": {
        "required": [
            ["inventory", "stock", "item", "product", "sku", "quantity"],
            ["value", "cost", "price", "amount", "total"]
        ],
        "optional": ["category", "reorder", "supplier",
                     "location", "unit", "available"],
        "min_score": 1
    },
    "payroll": {
        "required": [
            ["salary", "payroll", "employee", "staff", "name", "worker"],
            ["amount", "gross", "net", "pay", "wage"]
        ],
        "optional": ["tax", "pension", "deduction", "allowance",
                     "department", "bank", "account"],
        "min_score": 1
    }
}

# ── COLUMNS THAT SIGNAL NON-FINANCIAL CSV ─────────
REJECTION_SIGNALS = [
    "event", "meeting", "appointment", "calendar",
    "task", "todo", "reminder", "schedule",
    "contact", "phone", "email", "address",
    "subject", "body", "message", "sender",
    "latitude", "longitude", "coordinates",
    "student", "grade", "score", "marks", "class",
    "recipe", "ingredient", "nutrition", "calories"
]


# ── MAIN CLASSIFIER ───────────────────────────────

def classify_csv(csv_content: str) -> dict:
    """
    Classify a CSV as one of:
      sales | expense | invoice | inventory | payroll | unknown

    Returns:
      {
        "type": "sales",
        "confidence": 0.85,
        "valid": True,
        "reason": "Detected sales columns: revenue, date, product"
      }
    """
    if not csv_content or len(csv_content.strip()) < 10:
        return {"type": "unknown", "confidence": 0, "valid": False,
                "reason": "Empty or too short."}

    try:
        reader = csv.DictReader(io.StringIO(csv_content.strip()))
        headers = [h.lower().strip() for h in (reader.fieldnames or [])]
    except Exception:
        return {"type": "unknown", "confidence": 0, "valid": False,
                "reason": "Could not read CSV headers."}

    if not headers:
        return {"type": "unknown", "confidence": 0, "valid": False,
                "reason": "No column headers found."}

    # ── Check rejection signals first
    rejection_hits = [h for h in headers if h in REJECTION_SIGNALS]
    if len(rejection_hits) >= 2:
        return {
            "type":       "invalid",
            "confidence": 0,
            "valid":      False,
            "reason": (
                f"This does not appear to be a financial CSV. "
                f"Detected non-financial columns: {', '.join(rejection_hits)}. "
                f"Please upload one of: Sales, Expense, Invoice, "
                f"Inventory, or Payroll CSV."
            )
        }

    # ── Score each type
    scores = {}
    for csv_type, signature in CSV_SIGNATURES.items():
        score = 0
        matched_required = []
        matched_optional = []

        for required_group in signature["required"]:
            for kw in required_group:
                if any(kw in h for h in headers):
                    score += 2
                    matched_required.append(kw)
                    break

        for kw in signature["optional"]:
            if any(kw in h for h in headers):
                score += 1
                matched_optional.append(kw)

        scores[csv_type] = {
            "score":    score,
            "required": matched_required,
            "optional": matched_optional
        }

    # ── Pick best match
    best_type  = max(scores, key=lambda t: scores[t]["score"])
    best_score = scores[best_type]["score"]
    min_score  = CSV_SIGNATURES[best_type]["min_score"]

    if best_score < min_score * 2:
        return {
            "type":       "unknown",
            "confidence": 0,
            "valid":      False,
            "reason": (
                f"Could not identify this as a financial CSV. "
                f"Headers found: {', '.join(headers[:8])}. "
                f"Expected one of: Sales, Expense, Invoice, "
                f"Inventory, or Payroll CSV."
            )
        }

    max_possible = (len(CSV_SIGNATURES[best_type]["required"]) * 2
                    + len(CSV_SIGNATURES[best_type]["optional"]))
    confidence = round(best_score / max(max_possible, 1), 2)

    matched = scores[best_type]["required"] + scores[best_type]["optional"]
    return {
        "type":       best_type,
        "confidence": confidence,
        "valid":      True,
        "reason": (
            f"Identified as {best_type.upper()} CSV "
            f"(confidence: {round(confidence*100)}%). "
            f"Matched columns: {', '.join(matched[:5])}."
        )
    }


# ── SME MULTI-CSV ANALYSER ────────────────────────

def analyse_sme_csvs(csv_files: list) -> dict:
    """
    Input: list of {"filename": str, "content": str}
    Output: full SME financial analysis

    Accepts 1–5 CSVs of different types.
    Calculates Cash Flow, Burn Rate, Days to Zero,
    Health Score, and AI Explanation.
    """
    classified = {}
    errors     = []

    # ── Classify each CSV
    for f in csv_files:
        result = classify_csv(f["content"])
        if not result["valid"]:
            errors.append({
                "filename": f["filename"],
                "reason":   result["reason"]
            })
            continue
        csv_type = result["type"]
        if csv_type not in classified:
            classified[csv_type] = []
        classified[csv_type].append({
            "filename": f["filename"],
            "content":  f["content"],
            "classification": result
        })

    if not classified:
        return {
            "success": False,
            "errors":  errors,
            "message": (
                "None of the uploaded files could be identified as "
                "financial CSVs. Please upload Sales, Expense, Invoice, "
                "Inventory, or Payroll CSV files."
            )
        }

    # ── Extract numbers from each type
    revenue     = _extract_revenue(classified.get("sales", []))
    expenses    = _extract_expenses(classified.get("expense", []))
    invoices    = _extract_invoices(classified.get("invoice", []))
    inventory   = _extract_inventory(classified.get("inventory", []))
    payroll     = _extract_payroll(classified.get("payroll", []))

    # ── Core calculations
    cash_flow    = revenue - expenses
    burn_rate    = expenses  # monthly
    cash_on_hand = max(cash_flow, 0)

    # Estimate cash on hand if we have revenue but no explicit balance
    if cash_on_hand == 0 and revenue > 0:
        cash_on_hand = revenue * 0.15  # assume 15% retained

    daily_burn   = burn_rate / 30 if burn_rate > 0 else 0
    days_to_zero = int(cash_on_hand / daily_burn) if daily_burn > 0 else 999

    # ── Health Score (weighted)
    score = _calculate_sme_score(
        revenue, expenses, cash_flow,
        invoices, inventory, payroll
    )

    # ── AI Explanation (100% data-driven)
    explanation = _build_explanation(
        revenue, expenses, cash_flow,
        invoices, inventory, payroll,
        days_to_zero, score
    )

    # ── Actions
    actions = _build_sme_actions(
        revenue, expenses, cash_flow,
        invoices, inventory, payroll,
        days_to_zero, score
    )

    return {
        "success": True,
        "type":    "sme",
        "files_processed": len(classified),
        "files_rejected":  len(errors),
        "errors":  errors,
        "detected_types": list(classified.keys()),

        "financials": {
            "revenue":     round(revenue, 2),
            "expenses":    round(expenses, 2),
            "cash_flow":   round(cash_flow, 2),
            "burn_rate":   round(burn_rate, 2),
            "daily_burn":  round(daily_burn, 2),
            "cash_on_hand":round(cash_on_hand, 2),
            "invoices_outstanding": round(invoices, 2),
            "inventory_value":      round(inventory, 2),
            "payroll_total":        round(payroll, 2),
        },

        "score": {
            "score":   score,
            "label":   _sme_label(score),
            "color":   _sme_color(score),
            "message": explanation
        },

        "days_to_zero": {
            "days_remaining":  days_to_zero,
            "daily_burn_rate": round(daily_burn, 2),
            "current_balance": round(cash_on_hand, 2),
            "urgency":         _urgency(days_to_zero),
            "message": (
                f"At your current burn rate of ₦{daily_burn:,.0f}/day, "
                f"your business has {days_to_zero} days of cash runway."
            )
        },

        "actions": actions
    }


# ── EXTRACTORS ────────────────────────────────────

def _sum_column(csv_content: str, keywords: list) -> float:
    """Sum values from any column whose header matches keywords."""
    total = 0.0
    try:
        reader = csv.DictReader(io.StringIO(csv_content.strip()))
        headers = {h.lower().strip(): h for h in (reader.fieldnames or [])}
        target_col = None
        for kw in keywords:
            for h_lower, h_orig in headers.items():
                if kw in h_lower:
                    target_col = h_orig
                    break
            if target_col:
                break

        if not target_col:
            return 0.0

        for row in reader:
            val = row.get(target_col, "")
            cleaned = re.sub(r"[₦,\s]", "", str(val))
            try:
                total += abs(float(cleaned))
            except ValueError:
                continue
    except Exception:
        pass
    return total


def _extract_revenue(files: list) -> float:
    total = 0.0
    for f in files:
        total += _sum_column(f["content"],
            ["revenue","sales","income","amount","total","gross"])
    return total


def _extract_expenses(files: list) -> float:
    total = 0.0
    for f in files:
        total += _sum_column(f["content"],
            ["expense","cost","amount","total","spend","debit"])
    return total


def _extract_invoices(files: list) -> float:
    total = 0.0
    for f in files:
        # Sum unpaid invoices only
        try:
            reader = csv.DictReader(io.StringIO(f["content"].strip()))
            headers = {h.lower().strip(): h for h in (reader.fieldnames or [])}
            amount_col = None
            status_col = None
            for h_lower, h_orig in headers.items():
                if any(kw in h_lower for kw in ["amount","total","balance","due"]):
                    amount_col = h_orig
                if any(kw in h_lower for kw in ["status","paid","payment"]):
                    status_col = h_orig

            if not amount_col:
                continue

            for row in reader:
                status = str(row.get(status_col, "unpaid")).lower() if status_col else "unpaid"
                if "paid" in status and "unpaid" not in status:
                    continue  # skip paid invoices
                val = row.get(amount_col, "")
                cleaned = re.sub(r"[₦,\s]", "", str(val))
                try:
                    total += abs(float(cleaned))
                except ValueError:
                    continue
        except Exception:
            continue
    return total


def _extract_inventory(files: list) -> float:
    total = 0.0
    for f in files:
        total += _sum_column(f["content"],
            ["value","total","cost","amount","price"])
    return total


def _extract_payroll(files: list) -> float:
    total = 0.0
    for f in files:
        total += _sum_column(f["content"],
            ["gross","net","salary","pay","wage","amount","total"])
    return total


# ── SCORE ─────────────────────────────────────────

def _calculate_sme_score(revenue, expenses, cash_flow,
                          invoices, inventory, payroll) -> int:
    score = 0

    # Cash flow positive (30 pts)
    if cash_flow > 0:
        ratio = cash_flow / revenue if revenue > 0 else 0
        score += min(30, int(ratio * 100))

    # Revenue exists (20 pts)
    if revenue > 0:
        score += 20

    # Payroll manageable (20 pts)
    if revenue > 0 and payroll > 0:
        payroll_ratio = payroll / revenue
        if payroll_ratio < 0.4:
            score += 20
        elif payroll_ratio < 0.6:
            score += 12
        elif payroll_ratio < 0.8:
            score += 5

    # Invoices not blocking cash (15 pts)
    if revenue > 0:
        invoice_ratio = invoices / revenue
        if invoice_ratio < 0.2:
            score += 15
        elif invoice_ratio < 0.4:
            score += 8
        elif invoice_ratio < 0.6:
            score += 3

    # Inventory not over-stocked (15 pts)
    if revenue > 0:
        inv_ratio = inventory / revenue
        if inv_ratio < 0.3:
            score += 15
        elif inv_ratio < 0.5:
            score += 8
        elif inv_ratio < 0.7:
            score += 3

    return max(0, min(100, score))


def _build_explanation(revenue, expenses, cash_flow,
                        invoices, inventory, payroll,
                        days_to_zero, score) -> str:
    parts = []

    if revenue > 0 and expenses > 0:
        margin = round((cash_flow / revenue) * 100, 1)
        parts.append(
            f"Your revenue is ₦{revenue:,.0f} and expenses are "
            f"₦{expenses:,.0f}, giving a cash flow of "
            f"₦{cash_flow:,.0f} ({margin}% margin)."
        )

    if invoices > 0:
        pct = round((invoices / revenue) * 100) if revenue > 0 else 0
        parts.append(
            f"₦{invoices:,.0f} ({pct}% of revenue) is tied up in "
            f"unpaid invoices — cash you are owed but have not received."
        )

    if inventory > 0:
        parts.append(
            f"₦{inventory:,.0f} is locked in inventory — "
            f"stock you own but have not sold yet."
        )

    if payroll > 0 and revenue > 0:
        payroll_pct = round((payroll / revenue) * 100)
        parts.append(
            f"Payroll is ₦{payroll:,.0f} ({payroll_pct}% of revenue). "
            + ("This is sustainable." if payroll_pct < 40
               else "This is high — consider if all roles are revenue-generating.")
        )

    liquid = revenue - expenses - invoices - inventory
    if liquid < 0:
        parts.append(
            f"Your real liquid cash position is negative "
            f"(₦{abs(liquid):,.0f} shortfall) once locked capital is accounted for."
        )
    elif liquid > 0:
        parts.append(
            f"Your actual liquid cash is ₦{liquid:,.0f} "
            f"after accounting for locked capital."
        )

    if days_to_zero < 30:
        parts.append(
            f"At current burn rate, you have {days_to_zero} days of runway. "
            f"Immediate action is required."
        )

    return " ".join(parts) if parts else "Upload more CSV files for a complete analysis."


def _build_sme_actions(revenue, expenses, cash_flow,
                        invoices, inventory, payroll,
                        days_to_zero, score) -> list:
    actions = []

    if invoices > 0:
        recovery_target = round(invoices * 0.5, 0)
        actions.append({
            "title": f"Chase ₦{recovery_target:,.0f} in outstanding invoices this week",
            "detail": (
                f"You have ₦{invoices:,.0f} in unpaid invoices. "
                f"Recovering just 50% (₦{recovery_target:,.0f}) "
                f"would immediately improve your cash position. "
                f"Prioritize your 3 oldest unpaid invoices first."
            ),
            "impact": "high",
            "type": "invoice_recovery",
            "interswitch_action": None
        })

    if inventory > 0 and revenue > 0:
        inv_ratio = inventory / revenue
        if inv_ratio > 0.3:
            liquid_target = round(inventory * 0.2, 0)
            actions.append({
                "title": f"Liquidate ₦{liquid_target:,.0f} of slow-moving inventory",
                "detail": (
                    f"₦{inventory:,.0f} is locked in inventory "
                    f"({round(inv_ratio*100)}% of revenue). "
                    f"Selling 20% of stock at cost price releases "
                    f"₦{liquid_target:,.0f} in cash immediately."
                ),
                "impact": "high",
                "type": "inventory_liquidation",
                "interswitch_action": None
            })

    if payroll > 0 and revenue > 0:
        payroll_pct = payroll / revenue
        if payroll_pct > 0.5:
            actions.append({
                "title": f"Payroll is {round(payroll_pct*100)}% of revenue — review headcount",
                "detail": (
                    f"Your payroll of ₦{payroll:,.0f} consumes "
                    f"{round(payroll_pct*100)}% of revenue. "
                    f"Industry benchmark is 30–40%. "
                    f"Identify roles that are not directly generating revenue."
                ),
                "impact": "high",
                "type": "cost_reduction",
                "interswitch_action": None
            })

    if days_to_zero < 60:
        actions.append({
            "title": f"Only {days_to_zero} days of runway — reduce burn rate now",
            "detail": (
                f"At ₦{round(expenses/30):,.0f}/day burn rate, "
                f"you have {days_to_zero} days before cash runs out. "
                f"Cut all non-essential expenses immediately. "
                f"Focus only on activities that generate revenue this week."
            ),
            "impact": "high",
            "type": "burn_reduction",
            "interswitch_action": None
        })

    if not actions:
        actions.append({
            "title": "Maintain positive cash flow and grow revenue",
            "detail": (
                f"Your business is generating positive cash flow of "
                f"₦{cash_flow:,.0f}. Focus on growing revenue while "
                f"keeping expenses below {round((expenses/revenue)*100) if revenue > 0 else 70}% of revenue."
            ),
            "impact": "medium",
            "type": "growth",
            "interswitch_action": None
        })

    return actions[:4]


def _sme_label(score: int) -> str:
    if score >= 75: return "Financially Healthy"
    if score >= 50: return "Moderate Risk"
    if score >= 30: return "High Risk"
    return "Critical"


def _sme_color(score: int) -> str:
    if score >= 75: return "green"
    if score >= 50: return "yellow"
    if score >= 30: return "orange"
    return "red"


def _urgency(days: int) -> str:
    if days <= 7:  return "critical"
    if days <= 14: return "high"
    if days <= 30: return "medium"
    return "low"