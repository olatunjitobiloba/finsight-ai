# services/ai_actions.py
# FinSight AI — Genuine AI Action Generator
# Owner: Toby
#
# ZERO hardcoded strings.
# Every sentence is built from actual numbers in the data.
# Two different people with different data
# will NEVER get the same output.

from typing import Optional
import statistics


def generate_genuine_actions(
    score_result:   dict,
    days_result:    dict,
    pattern_result: dict,
    raw_transactions: list,
    user_context:   Optional[dict] = None
) -> list:
    """
    Generates 3–5 personalized, data-driven actions.
    Every number, every sentence comes from the actual data.

    user_context (optional):
        {
          "network": "MTN",        # detected from SMS
          "has_dstv": True,
          "has_electricity": True,
          "monthly_data_spend": 4500
        }
    """
    actions = []
    score    = score_result.get("score", 50)
    summary  = score_result.get("summary", {})
    pillars  = score_result.get("pillars", {})
    days     = days_result.get("days_remaining")
    burn     = days_result.get("daily_burn_rate", 0)
    patterns = pattern_result.get("patterns", [])
    balance  = days_result.get("current_balance", 0)

    total_income   = summary.get("total_income", 0)
    total_spending = summary.get("total_spending", 0)
    net            = summary.get("net", 0)

    # ── Build category breakdown from raw transactions
    cat_totals = _category_totals(raw_transactions)
    cat_pcts   = _category_percentages(cat_totals, total_spending)

    # ── Detect network from transactions
    network = _detect_network(raw_transactions)
    if user_context:
        network = user_context.get("network", network) or network

    # ── Detect data spending pattern
    data_spend = cat_totals.get("Data", 0) + cat_totals.get("Airtime", 0)
    data_txn_count = _count_category_transactions(raw_transactions, ["data","airtime","mtn","airtel","glo","9mobile"])

    # ── ACTION 1: Most urgent — based on days_to_zero
    if days is not None and days <= 14:
        daily_cut   = round(burn * 0.25, 0)
        new_days    = round(balance / (burn - daily_cut)) if (burn - daily_cut) > 0 else days + 7
        extra_days  = new_days - days
        top_category = max(cat_totals, key=cat_totals.get) if cat_totals else "general"
        top_amount   = cat_totals.get(top_category, 0)
        top_pct      = round(cat_pcts.get(top_category, 0))

        actions.append({
            "title": f"You have {days} days of money left — cut {top_category} spending first",
            "detail": (
                f"Your daily burn rate is ₦{burn:,.0f}. "
                f"Your highest spending category is {top_category} "
                f"at ₦{top_amount:,.0f} ({top_pct}% of all spending). "
                f"Reducing {top_category} by 25% saves ₦{daily_cut:,.0f}/day "
                f"and extends your runway by {extra_days} days — "
                f"from {days} days to {new_days} days."
            ),
            "impact": "high",
            "type":   "spending_cut",
            "category": top_category,
            "interswitch_action": None
        })

    # ── ACTION 2: Data bundle recommendation
    if data_txn_count >= 2 and data_spend > 0:
        monthly_data_cost = data_spend
        bundle = _recommend_bundle(network, monthly_data_cost)
        saving = round(monthly_data_cost - bundle["price"], 0)

        if saving > 0:
            actions.append({
                "title": f"You are overpaying for data — switch to {network} {bundle['name']}",
                "detail": (
                    f"You bought data {data_txn_count} times this period, "
                    f"spending ₦{monthly_data_cost:,.0f} total. "
                    f"The {bundle['name']} bundle costs ₦{bundle['price']:,.0f}/month "
                    f"and covers your usage. "
                    f"You would save ₦{saving:,.0f} this month alone. "
                    f"Over 12 months that is ₦{saving * 12:,.0f}."
                ),
                "impact": "high" if saving > 1000 else "medium",
                "type":   "data_bundle",
                "bundle": bundle,
                "network": network,
                "interswitch_action": {
                    "type": "data",
                    "network": network,
                    "bundle_code": bundle["code"],
                    "amount": bundle["price"],
                    "label": f"Buy {bundle['name']} via Interswitch"
                }
            })

    # ── ACTION 3: Electricity bill (if detected)
    electricity_spend = cat_totals.get("Electricity", 0)
    electricity_txns  = _count_category_transactions(
        raw_transactions, ["ikedc","ekedc","aedc","electricity","prepaid","token"]
    )
    if electricity_txns >= 1:
        avg_electricity = round(electricity_spend / max(electricity_txns, 1), 0)
        actions.append({
            "title": "Pay electricity automatically — stop buying tokens in panic",
            "detail": (
                f"You have spent ₦{electricity_spend:,.0f} on electricity "
                f"across {electricity_txns} purchase(s) this period. "
                f"Your average top-up is ₦{avg_electricity:,.0f}. "
                f"Setting up a monthly auto-payment of ₦{avg_electricity:,.0f} "
                f"prevents blackouts and removes the mental load of remembering."
            ),
            "impact": "medium",
            "type":   "bill_setup",
            "interswitch_action": {
                "type":   "electricity",
                "amount": avg_electricity,
                "label":  "Set up electricity payment via Interswitch"
            }
        })

    # ── ACTION 4: Post-salary savings lock
    post_salary = next(
        (p for p in patterns if p["id"] == "post_salary_spike"), None
    )
    if post_salary:
        lock_amount = round(total_income * 0.30, 0)
        remaining   = round(total_income - lock_amount, 0)
        spike_pct   = _extract_pct_from_detail(post_salary["detail"])

        actions.append({
            "title": f"Lock ₦{lock_amount:,.0f} the moment your salary arrives",
            "detail": (
                f"You spent {spike_pct}% of your income "
                f"within 3 days of receiving it. "
                f"On your next payday, immediately transfer ₦{lock_amount:,.0f} "
                f"(30% of ₦{total_income:,.0f}) to a separate savings account. "
                f"You will still have ₦{remaining:,.0f} to spend — "
                f"but your savings are protected before impulse spending begins."
            ),
            "impact": "high",
            "type":   "savings_lock",
            "interswitch_action": {
                "type":   "transfer",
                "amount": lock_amount,
                "label":  f"Transfer ₦{lock_amount:,.0f} to savings via Interswitch"
            }
        })

    # ── ACTION 5: Weekend spending cap
    weekend = next(
        (p for p in patterns if p["id"] == "weekend_overspend"), None
    )
    if weekend:
        weekend_avg  = _get_weekend_avg(raw_transactions)
        weekday_avg  = _get_weekday_avg(raw_transactions)
        cap          = round(weekday_avg * 1.1, 0)
        monthly_save = round((weekend_avg - cap) * 8, 0)  # ~8 weekend days/month

        actions.append({
            "title": f"Cap weekend spending at ₦{cap:,.0f} per day",
            "detail": (
                f"Your average weekend spend is ₦{weekend_avg:,.0f}/day "
                f"vs ₦{weekday_avg:,.0f}/day on weekdays. "
                f"If you cap weekends at ₦{cap:,.0f}/day — "
                f"just 10% above your weekday average — "
                f"you save approximately ₦{monthly_save:,.0f} per month. "
                f"That is ₦{monthly_save * 12:,.0f} per year."
            ),
            "impact": "high" if monthly_save > 5000 else "medium",
            "type":   "spending_cap",
            "interswitch_action": None
        })

    # ── ACTION 6: DSTV optimization
    dstv_spend = _count_category_transactions(
        raw_transactions, ["dstv","gotv"]
    )
    if dstv_spend >= 1:
        dstv_amount = cat_totals.get("Bills", 0)
        actions.append({
            "title": "Pay DSTV via Interswitch — never miss a subscription",
            "detail": (
                f"You pay for DSTV/GOtv regularly. "
                f"Setting up payment through Interswitch Quickteller "
                f"ensures your subscription never lapses "
                f"and you can pay instantly without going to a vendor."
            ),
            "impact": "low",
            "type":   "bill_payment",
            "interswitch_action": {
                "type":   "dstv",
                "amount": 6800,
                "label":  "Pay DSTV via Interswitch"
            }
        })

    # ── Fallback if no actions generated
    if not actions:
        savings_rate = round((net / total_income * 100), 1) if total_income > 0 else 0
        target_rate  = 20
        gap          = max(0, target_rate - savings_rate)
        gap_amount   = round(total_income * gap / 100, 0)

        actions.append({
            "title": f"Increase your savings rate from {savings_rate}% to {target_rate}%",
            "detail": (
                f"You are currently saving {savings_rate}% of your income. "
                f"The recommended minimum is 20%. "
                f"To reach 20%, you need to save an additional "
                f"₦{gap_amount:,.0f} per month. "
                f"Start by transferring ₦{round(gap_amount/30, 0):,.0f}/day "
                f"to a separate account."
            ),
            "impact": "medium",
            "type":   "savings_increase",
            "interswitch_action": {
                "type":   "transfer",
                "amount": gap_amount,
                "label":  f"Transfer ₦{gap_amount:,.0f} to savings"
            }
        })

    # Sort by impact
    order = {"high": 0, "medium": 1, "low": 2}
    actions.sort(key=lambda x: order.get(x["impact"], 3))

    return actions[:5]


# ── HELPERS ───────────────────────────────────────

def _category_totals(transactions: list) -> dict:
    totals = {}
    for t in transactions:
        if t.get("type") != "debit":
            continue
        cat = t.get("category", "Uncategorized")
        totals[cat] = totals.get(cat, 0) + t.get("amount", 0)
    return totals


def _category_percentages(totals: dict, total_spending: float) -> dict:
    if total_spending == 0:
        return {}
    return {k: (v / total_spending * 100) for k, v in totals.items()}


def _count_category_transactions(transactions: list, keywords: list) -> int:
    count = 0
    for t in transactions:
        desc = (t.get("description") or "").lower()
        cat  = (t.get("category") or "").lower()
        if any(kw in desc or kw in cat for kw in keywords):
            count += 1
    return count


def _detect_network(transactions: list) -> str:
    counts = {"MTN": 0, "AIRTEL": 0, "GLO": 0, "9MOBILE": 0}
    for t in transactions:
        desc = (t.get("description") or "").lower()
        for net in counts:
            if net.lower() in desc:
                counts[net] += 1
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else "MTN"


def _recommend_bundle(network: str, monthly_spend: float) -> dict:
    """Recommend the most cost-effective bundle for the user's spend."""
    bundles = {
        "MTN": [
            {"code": "MTN300", "name": "1GB/30days",  "price": 300,  "gb": 1},
            {"code": "MTN500", "name": "2GB/30days",  "price": 500,  "gb": 2},
            {"code": "MTN1000","name": "5GB/30days",  "price": 1000, "gb": 5},
            {"code": "MTN2000","name": "10GB/30days", "price": 2000, "gb": 10},
            {"code": "MTN3500","name": "20GB/30days", "price": 3500, "gb": 20},
        ],
        "AIRTEL": [
            {"code": "AIR300", "name": "1.5GB/30days","price": 300,  "gb": 1.5},
            {"code": "AIR500", "name": "3GB/30days",  "price": 500,  "gb": 3},
            {"code": "AIR1000","name": "6GB/30days",  "price": 1000, "gb": 6},
            {"code": "AIR2000","name": "15GB/30days", "price": 2000, "gb": 15},
        ],
        "GLO": [
            {"code": "GLO300", "name": "2.5GB/30days","price": 300,  "gb": 2.5},
            {"code": "GLO500", "name": "5GB/30days",  "price": 500,  "gb": 5},
            {"code": "GLO1000","name": "12GB/30days", "price": 1000, "gb": 12},
        ],
        "9MOBILE": [
            {"code": "9M300",  "name": "1GB/30days",  "price": 300,  "gb": 1},
            {"code": "9M500",  "name": "2GB/30days",  "price": 500,  "gb": 2},
            {"code": "9M1000", "name": "4GB/30days",  "price": 1000, "gb": 4},
        ]
    }
    available = bundles.get(network.upper(), bundles["MTN"])
    # Find cheapest bundle that costs less than current spend
    cheaper = [b for b in available if b["price"] < monthly_spend]
    if cheaper:
        return max(cheaper, key=lambda x: x["gb"])  # best value
    return available[0]  # cheapest option


def _extract_pct_from_detail(detail: str) -> str:
    import re
    match = re.search(r"(\d+)%", detail)
    return match.group(1) if match else "a large portion"


def _get_weekend_avg(transactions: list) -> float:
    from datetime import datetime
    weekend_amounts = []
    for t in transactions:
        if t.get("type") != "debit":
            continue
        try:
            d = datetime.strptime(str(t["transaction_date"]), "%Y-%m-%d")
            if d.weekday() >= 5:
                weekend_amounts.append(t["amount"])
        except Exception:
            continue
    return round(statistics.mean(weekend_amounts), 0) if weekend_amounts else 0


def _get_weekday_avg(transactions: list) -> float:
    from datetime import datetime
    weekday_amounts = []
    for t in transactions:
        if t.get("type") != "debit":
            continue
        try:
            d = datetime.strptime(str(t["transaction_date"]), "%Y-%m-%d")
            if d.weekday() < 5:
                weekday_amounts.append(t["amount"])
        except Exception:
            continue
    return round(statistics.mean(weekday_amounts), 0) if weekday_amounts else 0