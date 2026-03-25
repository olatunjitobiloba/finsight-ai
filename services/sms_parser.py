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
        if bank == "access":
            return parse_access_bank_sms(cleaned_text)
        elif bank == "gt":
            return parse_gtbank_sms(cleaned_text)
        elif bank == "first":
            return parse_first_bank_sms(cleaned_text)
        elif bank == "zenith":
            return parse_zenith_sms(cleaned_text)
        elif bank == "uba":
            return parse_uba_sms(cleaned_text)
        else:
            return None
            
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
    
    # Extract balance
    balance_match = re.search(r'Avail Bal:\s*NGN?([\d,]+\.\d{2})', sms_text, re.IGNORECASE)
    if balance_match:
        balance_str = balance_match.group(1).replace(',', '')
        result["balance"] = float(balance_str)
    
    # Extract description
    desc_match = re.search(r'Desc:\s*(.*)', sms_text, re.IGNORECASE)

    if desc_match:
        result["description"] = desc_match.group(1).strip()
    
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
        if parsed:
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