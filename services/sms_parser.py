# banks covered for SMS parser
# gtbank, access, first bank, zenith, UBA

# result sample
# dictionary with 
# {
#     "bank": "gtbank",
#     "amount": 1000, 
#     "date": "2025-10-15", 
#     "time": "12:00:00", 
#     "type":"credit",
#     "description":"transport",
#     "balance":10000
# }

import re
from datetime import datetime
from typing import Dict, Optional, List


MONTH_MAP = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def _clean_money(value: str) -> float:
    return float((value or "0").replace(",", "").strip())


def _parse_flexible_date(date_text: str) -> Optional[str]:
    if not date_text:
        return None

    raw = str(date_text).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%b-%Y", "%d-%b-%y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _infer_month_year_date(text: str) -> Optional[str]:
    if not text:
        return None

    m = re.search(
        r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b",
        text,
        re.IGNORECASE,
    )
    if not m:
        return None

    month_name = m.group(1)[:3].lower()
    month = MONTH_MAP.get(month_name)
    year = int(m.group(2))
    if not month:
        return None

    return f"{year:04d}-{month:02d}-01"


def _normalize_transaction_schema(parsed: Dict) -> Dict:
    if not parsed:
        return parsed

    tx_date = parsed.get("transaction_date") or parsed.get("date")
    if tx_date:
        parsed["transaction_date"] = tx_date
        parsed["date"] = tx_date

    amount = parsed.get("amount", 0)
    try:
        parsed["amount"] = abs(float(amount))
    except (ValueError, TypeError):
        parsed["amount"] = 0.0

    tx_type = (parsed.get("type") or "").lower().strip()
    parsed["type"] = "credit" if tx_type == "credit" else "debit"

    parsed["description"] = _clean_description(parsed.get("description") or "Transaction")

    category = str(parsed.get("category") or "").strip()
    if not category or category.lower() == "uncategorized":
        parsed["category"] = _categorize_transaction(parsed["description"], parsed["type"])

    return parsed


def _clean_description(description: str) -> str:
    text = str(description or "").strip()
    if not text:
        return "Transaction"

    # Strip trailing balance fragments that some bank formats append to description.
    text = re.sub(r"\.?\s*(bal|avail\s*bal)\s*:\s*(ngn|n)?\s*[\d,]+(?:\.\d{1,2})?.*$", "", text, flags=re.IGNORECASE)
    return text.strip().rstrip(".") or "Transaction"


def _categorize_transaction(description: str, tx_type: str) -> str:
    desc = (description or "").lower()
    normalized_type = (tx_type or "").lower().strip()

    if normalized_type == "credit":
        income_keywords = [
            "salary", "allowance", "bonus", "project", "freelance", "consultation",
            "payment received", "credited", "refund"
        ]
        if any(kw in desc for kw in income_keywords):
            return "Income"
        return "Transfers"

    categories = {
        "Savings": ["savings", "piggyvest", "cowrywise", "investment", "stash", "save"],
        "Bills": ["rent", "dstv", "gotv", "electricity", "ikedc", "ekedc", "aedc", "phcn", "airtel data", "data", "airtime", "subscription", "utility"],
        "Transport": ["uber", "bolt", "ride", "fuel", "transport", "trip"],
        "Food": ["shoprite", "kfc", "chicken republic", "restaurant", "dinner", "grocer", "supermarket", "food"],
        "Shopping": ["jumia", "shopping", "fashion", "store", "electronics"],
        "Entertainment": ["cinema", "club", "outing", "netflix", "showmax", "spotify", "event"],
    }

    for category, keywords in categories.items():
        if any(kw in desc for kw in keywords):
            return category

    transfer_keywords = ["transfer", "pos", "atm", "withdraw", "trx", "trf"]
    if any(kw in desc for kw in transfer_keywords):
        return "Transfers"

    return "Uncategorized"


def _is_valid_transaction(parsed: Optional[Dict]) -> bool:
    if not parsed:
        return False

    tx_date = parsed.get("transaction_date") or parsed.get("date")
    amount = parsed.get("amount")
    tx_type = (parsed.get("type") or "").lower()
    return bool(tx_date and isinstance(amount, (int, float)) and amount > 0 and tx_type in {"credit", "debit"})


def _parse_common_alert_sms(sms_text: str, bank: str) -> Optional[Dict]:
    text = (sms_text or "").strip()
    if not text:
        return None

    pattern_with_date = re.search(
        r"(?P<type>credited|debited)\s+with\s*(?:NGN|N)\s*(?P<amount>[\d,]+(?:\.\d{1,2})?)"
        r".*?\bon\s*(?P<date>\d{2}-[A-Za-z]{3}-\d{2,4})"
        r".*?(?:Desc|Narration):\s*(?P<desc>.*?)"
        r"(?:\.\s*Bal:\s*(?:NGN|N)\s*(?P<bal>[\d,]+(?:\.\d{1,2})?))",
        text,
        re.IGNORECASE,
    )

    if pattern_with_date:
        tx_type = "credit" if pattern_with_date.group("type").lower() == "credited" else "debit"
        tx_date = _parse_flexible_date(pattern_with_date.group("date"))
        if not tx_date:
            return None

        balance = pattern_with_date.group("bal")
        return {
            "bank": bank,
            "amount": _clean_money(pattern_with_date.group("amount")),
            "date": tx_date,
            "transaction_date": tx_date,
            "type": tx_type,
            "description": (pattern_with_date.group("desc") or "Transaction").strip().rstrip("."),
            "balance": _clean_money(balance) if balance else 0.0,
            "category": "Uncategorized",
        }

    pattern_without_date = re.search(
        r"(?P<type>credited|debited)\s+with\s*(?:NGN|N)\s*(?P<amount>[\d,]+(?:\.\d{1,2})?)"
        r".*?(?:Desc|Narration):\s*(?P<desc>.*?)"
        r"(?:\.\s*Bal:\s*(?:NGN|N)\s*(?P<bal>[\d,]+(?:\.\d{1,2})?))",
        text,
        re.IGNORECASE,
    )

    if pattern_without_date:
        inferred_date = _infer_month_year_date(pattern_without_date.group("desc") or "")
        if not inferred_date:
            return None

        tx_type = "credit" if pattern_without_date.group("type").lower() == "credited" else "debit"
        balance = pattern_without_date.group("bal")
        return {
            "bank": bank,
            "amount": _clean_money(pattern_without_date.group("amount")),
            "date": inferred_date,
            "transaction_date": inferred_date,
            "type": tx_type,
            "description": (pattern_without_date.group("desc") or "Transaction").strip().rstrip("."),
            "balance": _clean_money(balance) if balance else 0.0,
            "category": "Uncategorized",
        }

    return None


def normalize_bank_type(bank_type: Optional[str]) -> Optional[str]:
    """Normalize user-provided bank labels to parser bank codes."""
    if not bank_type:
        return None

    normalized = re.sub(r"[^a-z]", "", bank_type.lower())
    aliases = {
        "access": "access",
        "accessbank": "access",
        "gt": "gt",
        "gtb": "gt",
        "gtbank": "gt",
        "guarantytrust": "gt",
        "guarantytrustbank": "gt",
        "first": "first",
        "firstbank": "first",
        "fbn": "first",
        "zenith": "zenith",
        "zenithbank": "zenith",
        "uba": "uba",
        "unitedbankforafrica": "uba"
    }

    return aliases.get(normalized)


def parse_sms(sms_text: str, bank_type: Optional[str] = None) -> Optional[Dict]:
    """
    Parse transaction SMS and return structured data.
    
    Args:
        sms_text: Raw SMS text from bank
        bank_type: Bank type provided by user ('access', 'gt', 'first', 'zenith', 'uba')
                  If not provided, will attempt to auto-detect
        
    Returns:
        Dictionary with transaction details or None if parsing fails
    """
    try:
        # Clean and normalize the SMS text
        cleaned_text = sms_text.strip()
        
        # Use bank type from user or detect it
        if bank_type:
            bank = normalize_bank_type(bank_type)
            if not bank:
                return None
        else:
            bank = detect_bank(cleaned_text)
            if not bank:
                return None
        
        # Parse based on bank
        parsed = None
        if bank == "access":
            parsed = parse_access_bank_sms(cleaned_text)
        elif bank == "gt":
            parsed = parse_gtbank_sms(cleaned_text)
        elif bank == "first":
            parsed = parse_first_bank_sms(cleaned_text)
        elif bank == "zenith":
            parsed = parse_zenith_sms(cleaned_text)
        elif bank == "uba":
            parsed = parse_uba_sms(cleaned_text)
        else:
            return None

        # Fallback for compact Nigerian alert formats used in demo and real app flows.
        if not _is_valid_transaction(parsed):
            parsed = _parse_common_alert_sms(cleaned_text, bank)

        if not _is_valid_transaction(parsed):
            return None

        return _normalize_transaction_schema(parsed)
            
    except Exception as e:
        print(f"Error parsing SMS: {e}")
        return None


def detect_bank(sms_text: str) -> Optional[str]:
    """Detect the bank from SMS text."""
    text_lower = sms_text.lower()
    
    if "access bank" in text_lower or "acmb" in text_lower:
        return "access"
    elif "gtbank" in text_lower or "guaranty trust" in text_lower:
        return "gt"
    elif "first bank" in text_lower or "firstbank" in text_lower:
        return "first"
    elif "zenith bank" in text_lower:
        return "zenith"
    elif "uba" in text_lower or "united bank" in text_lower:
        return "uba"
    
    return None


def parse_access_bank_sms(sms_text: str) -> Dict:
    """
    Parse Access Bank SMS format.
    
    Example format:
    Debit
    Amt: NGN7,500.00
    Acc:190****678
    Desc: 23r555432wa/MOBILE TRF TO PAY/ Payment for Ties/ MOSES
    Date: 18/03/2026
    Avail Bal: NGN1,405.57
    Total: NGN
    """
    result = {
        "bank": "access",
        "amount": 0.0,
        "date": "",
        "type": "debit",
        "description": "",
        "balance": 0.0
    }
    
    # Extract transaction type
    if re.search(r'Credit', sms_text, re.IGNORECASE):
        result["type"] = "credit"
    elif re.search(r'Debit', sms_text, re.IGNORECASE):
        result["type"] = "debit"
    
    # Extract amount
    amount_match = re.search(r'Amt:\s*NGN?([\d,]+\.\d{2})', sms_text, re.IGNORECASE)
    if amount_match:
        amount_str = amount_match.group(1).replace(',', '')
        result["amount"] = float(amount_str)
    else:
        alt_amount_match = re.search(
            r'(?:credited|debited)\s+with\s*(?:NGN|N)\s*([\d,]+(?:\.\d{1,2})?)',
            sms_text,
            re.IGNORECASE,
        )
        if alt_amount_match:
            result["amount"] = _clean_money(alt_amount_match.group(1))
    
    # Extract date
    date_match = re.search(r'Date:\s*(\d{2}/\d{2}/\d{4})', sms_text, re.IGNORECASE)
    if date_match:
        date_str = date_match.group(1)
        try:
            # Convert DD/MM/YYYY to YYYY-MM-DD
            date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            result["date"] = date_obj.strftime("%Y-%m-%d")
        except ValueError:
            result["date"] = date_str
    else:
        alt_date_match = re.search(r'\bon\s*(\d{2}-[A-Za-z]{3}-\d{2,4})', sms_text, re.IGNORECASE)
        if alt_date_match:
            normalized = _parse_flexible_date(alt_date_match.group(1))
            if normalized:
                result["date"] = normalized
        else:
            inferred = _infer_month_year_date(sms_text)
            if inferred:
                result["date"] = inferred
    
    # Extract balance
    balance_match = re.search(r'Avail Bal:\s*NGN?([\d,]+\.\d{2})', sms_text, re.IGNORECASE)
    if balance_match:
        balance_str = balance_match.group(1).replace(',', '')
        result["balance"] = float(balance_str)
    else:
        alt_balance_match = re.search(r'Bal:\s*(?:NGN|N)\s*([\d,]+(?:\.\d{1,2})?)', sms_text, re.IGNORECASE)
        if alt_balance_match:
            result["balance"] = _clean_money(alt_balance_match.group(1))
    
    # Extract description
    desc_match = re.search(r'Desc:\s*(.*?)(?:\.\s*Bal:|$)', sms_text, re.IGNORECASE)

    if desc_match:
        result["description"] = desc_match.group(1).strip()
    else:
        narration_match = re.search(r'Narration:\s*(.*?)(?:\.\s*Bal:|$)', sms_text, re.IGNORECASE)
        if narration_match:
            result["description"] = narration_match.group(1).strip().rstrip('.')
    
    # Extract account number (masked)
    acc_match = re.search(r'Acc:\s*(\d+\*+\d+)', sms_text, re.IGNORECASE)
    if acc_match:
        result["account"] = acc_match.group(1)
    
    return result


def parse_gtbank_sms(sms_text: str) -> Dict:
    """
    Parse GTBank SMS format.
    
    Example format:
    Acct: ****728
    Amt: NGN75,000.00 CR
    Desc: -TRANSFER FROM ADISABABA GLOBAL CONCEPTS-OPAY-ADIS
    Avail Bal: NGN104,657.26
    Date: 2026-03-18 6:26:55 PM
    """
    result = {
        "bank": "gt",
        "amount": 0.0,
        "date": "",
        "time": "",
        "type": "debit",
        "description": "",
        "balance": 0.0
    }
    
    # Extract transaction type from amount suffix
    if re.search(r'NGN[\d,\.]+\s+CR', sms_text, re.IGNORECASE):
        result["type"] = "credit"
    elif re.search(r'NGN[\d,\.]+\s+DR', sms_text, re.IGNORECASE):
        result["type"] = "debit"
    
    # Extract amount
    amount_match = re.search(r'Amt:\s*NGN?([\d,]+\.\d{2})\s*(CR|DR)?', sms_text, re.IGNORECASE)
    if amount_match:
        amount_str = amount_match.group(1).replace(',', '')
        result["amount"] = float(amount_str)
    
    # Extract date and time
    datetime_match = re.search(r'Date:\s*(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2}:\d{2})\s*(AM|PM)', sms_text, re.IGNORECASE)
    if datetime_match:
        date_str = datetime_match.group(1)  # 2026-03-18
        time_str = datetime_match.group(2)  # 6:26:55
        period = datetime_match.group(3)  # PM
        
        try:
            # Convert YYYY-MM-DD to YYYY-MM-DD (already in correct format)
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            result["date"] = date_obj.strftime("%Y-%m-%d")
            
            # Convert 12-hour to 24-hour format
            time_obj = datetime.strptime(f"{time_str} {period}", "%I:%M:%S %p")
            result["time"] = time_obj.strftime("%H:%M:%S")
        except ValueError:
            result["date"] = date_str
            result["time"] = f"{time_str} {period}"
    
    # Extract balance
    balance_match = re.search(r'Avail Bal:\s*NGN?([\d,]+\.\d{2})', sms_text, re.IGNORECASE)
    if balance_match:
        balance_str = balance_match.group(1).replace(',', '')
        result["balance"] = float(balance_str)
    
    # Extract description
    desc_match = re.search(r'Desc:\s*([^\.]+)', sms_text, re.IGNORECASE)
    if desc_match:
        result["description"] = desc_match.group(1).strip()
    
    # Extract account number (masked)
    acc_match = re.search(r'Acct:\s*(\*+\d+)', sms_text, re.IGNORECASE)
    if acc_match:
        result["account"] = acc_match.group(1)
    
    return result


def parse_first_bank_sms(sms_text: str) -> Dict:
    """
    Parse First Bank SMS format.
    
    Example format:
    Debit: 2314XXXX455 Amt: NGN6,000.00 Date: 19-MAR-2026 14:55:21 Desc: POS TRAN-FLAT /XX/NG/1. Bal: NGN5,967.81CR. Dial *894*11# to get loan
    """
    result = {
        "bank": "first",
        "amount": 0.0,
        "date": "",
        "time": "",
        "type": "debit",
        "description": "",
        "balance": 0.0
    }
    
    # Extract transaction type
    if re.search(r'Credit', sms_text, re.IGNORECASE):
        result["type"] = "credit"
    elif re.search(r'Debit', sms_text, re.IGNORECASE):
        result["type"] = "debit"
    
    # Extract amount
    amount_match = re.search(r'Amt:\s*NGN?([\d,]+\.\d{2})', sms_text, re.IGNORECASE)
    if amount_match:
        amount_str = amount_match.group(1).replace(',', '')
        result["amount"] = float(amount_str)
    
    # Extract date and time
    datetime_match = re.search(r'Date:\s*(\d{2}-[A-Z]{3}-\d{4})\s+(\d{2}:\d{2}:\d{2})', sms_text, re.IGNORECASE)
    if datetime_match:
        date_str = datetime_match.group(1)  # 19-MAR-2026
        time_str = datetime_match.group(2)  # 14:55:21
        
        try:
            # Convert DD-MMM-YYYY to YYYY-MM-DD
            date_obj = datetime.strptime(date_str, "%d-%b-%Y")
            result["date"] = date_obj.strftime("%Y-%m-%d")
            result["time"] = time_str
        except ValueError:
            result["date"] = date_str
            result["time"] = time_str
    
    # Extract balance
    balance_match = re.search(r'Bal:\s*NGN?([\d,]+\.\d{2})', sms_text, re.IGNORECASE)
    if balance_match:
        balance_str = balance_match.group(1).replace(',', '')
        result["balance"] = float(balance_str)
    
    # Extract description
    desc_match = re.search(r'Desc:\s*([^\.]+)', sms_text, re.IGNORECASE)
    if desc_match:
        result["description"] = desc_match.group(1).strip()
    
    # Extract account number (masked)
    acc_match = re.search(r'(\d{4}XXXX\d{3})', sms_text, re.IGNORECASE)
    if acc_match:
        result["account"] = acc_match.group(1)
    
    return result


def parse_zenith_sms(sms_text: str) -> Dict:
    """Parse Zenith Bank SMS format (placeholder implementation)."""
    # TODO: Implement Zenith Bank specific parsing
    return {
        "bank": "zenith",
        "amount": 0.0,
        "date": "",
        "time": "",
        "type": "debit",
        "description": "Zenith Bank parsing not implemented",
        "balance": 0.0
    }


def parse_uba_sms(sms_text: str) -> Dict:
    """Parse UBA Bank SMS format (placeholder implementation)."""
    # TODO: Implement UBA Bank specific parsing
    return {
        "bank": "uba",
        "amount": 0.0,
        "date": "",
        "time": "",
        "type": "debit",
        "description": "UBA Bank parsing not implemented",
        "balance": 0.0
    }


def parse_multiple_sms(sms_list: List[str], bank_type: Optional[str] = None) -> Dict:
    """
    Parse multiple SMS messages and return results with statistics.
    
    Args:
        sms_list: List of SMS text strings
        bank_type: Bank type provided by user (applied to all SMS)
        
    Returns:
        Dictionary with parsed results and statistics
    """
    results = {
        "parsed": [],
        "failed": [],
        "total": len(sms_list),
        "success_count": 0,
        "fail_count": 0,
        "success_rate": 0.0
    }
    
    for sms in sms_list:
        parsed = parse_sms(sms, bank_type)
        if _is_valid_transaction(parsed):
            parsed = _normalize_transaction_schema(parsed)
            results["parsed"].append(parsed)
            results["success_count"] += 1
        else:
            results["failed"].append(sms)
            results["fail_count"] += 1
    
    if results["total"] > 0:
        results["success_rate"] = (results["success_count"] / results["total"]) * 100
    
    return results


# Test function
def test_sms_parser():
    """Test the SMS parser with sample data from different banks."""
    
    # Test Access Bank
    access_sms = """Credit 
Amt:NGN2,000.00 
Acc:190**678 
Desc:247HYDR260770074/tt 
Date:18/03/2026 
Avail Bal:NGN8,932.45 
Total:NGN8,932.45"""
    
    # Test First Bank
    first_bank_sms = """Debit: 2314XXXX455 Amt: NGN6,000.00 Date: 19-MAR-2026 14:55:21 Desc: POS TRAN-FLAT /XX/NG/1. Bal: NGN5,967.81CR. Dial *894*11# to get loan"""
    
    # Test GT Bank
    gt_bank_sms = """Acct: ****728
Amt: NGN75,000.00 CR
Desc: -TRANSFER FROM ADISABABA GLOBAL CONCEPTS-OPAY-ADIS
Avail Bal: NGN940,657.26
Date: 2026-03-18 6:26:55 PM"""
    
    print("=== SMS Parser Tests ===")
    
    # Test with bank type parameter
    print("\n1. Access Bank (with bank_type parameter):")
    result1 = parse_sms(access_sms, "access")
    print(result1)
    
    print("\n2. First Bank (with bank_type parameter):")
    result2 = parse_sms(first_bank_sms, "first")
    print(result2)
    
    print("\n3. GT Bank (with bank_type parameter):")
    result3 = parse_sms(gt_bank_sms, "gt")
    print(result3)
    
    # Test multiple SMS parsing
    print("\n4. Multiple SMS parsing:")
    multiple_result = parse_multiple_sms([access_sms, first_bank_sms, gt_bank_sms])
    print(f"Total: {multiple_result['total']}, Success: {multiple_result['success_count']}, Failed: {multiple_result['fail_count']}")
    
    return {
        "access_bank": result1,
        "first_bank": result2,
        "gt_bank": result3,
        "multiple": multiple_result
    }


if __name__ == "__main__":
    test_sms_parser()