import csv
import io
from datetime import datetime
from typing import Dict, List, Optional, Union
from decimal import Decimal, InvalidOperation


def parse_csv(csv_content: Union[str, bytes]) -> Dict:
    """
    Parse CSV transaction data and return structured format.
    
    Args:
        csv_content: CSV content as string or bytes
        
    Returns:
        Dictionary with parsed transactions and statistics
    """
    try:
        # Handle bytes input
        if isinstance(csv_content, bytes):
            csv_content = csv_content.decode('utf-8')
        
        # Parse CSV content
        transactions = []
        failed_rows = []
        
        # Use io.StringIO to treat string as file
        csv_file = io.StringIO(csv_content)
        
        # Try to detect delimiter
        sample = csv_content[:1024]
        delimiter = detect_delimiter(sample)
        
        # Read CSV
        reader = csv.DictReader(csv_file, delimiter=delimiter)
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
            try:
                transaction = parse_csv_row(row, row_num)
                if transaction:
                    transactions.append(transaction)
                else:
                    failed_rows.append(f"Row {row_num}: Invalid data format")
            except Exception as e:
                failed_rows.append(f"Row {row_num}: {str(e)}")
        
        # Calculate running balance
        transactions = calculate_balances(transactions)
        
        # Prepare results
        total_rows = row_num - 1  # Subtract 1 for header
        success_count = len(transactions)
        fail_count = len(failed_rows)
        
        return {
            "parsed": transactions,
            "failed": failed_rows,
            "total": total_rows,
            "success_count": success_count,
            "fail_count": fail_count,
            "success_rate": (success_count / total_rows * 100) if total_rows > 0 else 0.0
        }
        
    except Exception as e:
        return {
            "parsed": [],
            "failed": [f"CSV parsing error: {str(e)}"],
            "total": 0,
            "success_count": 0,
            "fail_count": 0,
            "success_rate": 0.0
        }


def detect_delimiter(sample: str) -> str:
    """Detect CSV delimiter (comma, semicolon, or tab)."""
    delimiter_counts = {
        ',': sample.count(','),
        ';': sample.count(';'),
        '\t': sample.count('\t')
    }
    
    return max(delimiter_counts, key=delimiter_counts.get)


def parse_csv_row(row: Dict, row_num: int) -> Optional[Dict]:
    """
    Parse a single CSV row into transaction format.
    
    Expected columns (case-insensitive):
    - date, transaction_date
    - amount, debit, credit
    - description, description, particulars
    - type, transaction_type
    - category (optional)
    """
    try:
        # Standardize column names
        normalized_row = {k.strip().lower(): v for k, v in row.items()}
        
        # Extract date
        date_str = get_field_value(normalized_row, ['date', 'transaction_date', 'date'])
        if not date_str:
            return None
        
        parsed_date = parse_date(date_str)
        if not parsed_date:
            return None
        
        # Extract amount
        amount = extract_amount(normalized_row)
        if amount is None:
            return None
        
        # Extract transaction type
        transaction_type = determine_transaction_type(normalized_row, amount)
        
        # Extract description
        description = get_field_value(normalized_row, 
                                   ['description', 'particulars', 'narration', 'details', 'memo'])
        if not description:
            description = "Transaction"
        
        # Extract or assign category
        category = get_field_value(normalized_row, ['category', 'type'])
        if not category:
            category = categorize_transaction(description, transaction_type)
        
        return {
            "amount": abs(float(amount)),
            "type": transaction_type,
            "category": category,
            "description": description.strip(),
            "transaction_date": parsed_date,
            "source": "csv",
            "bank": "CSV Import",
            "balance": 0.0  # Will be calculated later
        }
        
    except Exception as e:
        print(f"Error parsing row {row_num}: {e}")
        return None


def get_field_value(row: Dict, field_names: List[str]) -> Optional[str]:
    """Get value from row using multiple possible field names."""
    for field in field_names:
        if field in row and row[field]:
            return str(row[field]).strip()
    return None


def extract_amount(row: Dict) -> Optional[float]:
    """Extract amount from various possible column formats."""
    # Try direct amount column
    amount_fields = ['amount', 'value', 'sum']
    for field in amount_fields:
        if field in row and row[field]:
            try:
                return float(str(row[field]).replace(',', '').replace('NGN', '').strip())
            except (ValueError, InvalidOperation):
                continue
    
    # Try debit/credit columns
    debit = get_field_value(row, ['debit', 'withdrawal', 'expense'])
    credit = get_field_value(row, ['credit', 'deposit', 'income'])
    
    if debit:
        try:
            amount = float(debit.replace(',', '').replace('NGN', '').strip())
            return -abs(amount)  # Debits are negative
        except (ValueError, InvalidOperation):
            pass
    
    if credit:
        try:
            amount = float(credit.replace(',', '').replace('NGN', '').strip())
            return abs(amount)  # Credits are positive
        except (ValueError, InvalidOperation):
            pass
    
    return None


def determine_transaction_type(row: Dict, amount: float) -> str:
    """Determine if transaction is credit or debit."""
    # Check explicit type field
    type_field = get_field_value(row, ['type', 'transaction_type', 'category'])
    if type_field:
        type_lower = type_field.lower()
        if 'credit' in type_lower or 'income' in type_lower or 'deposit' in type_lower:
            return 'credit'
        elif 'debit' in type_lower or 'expense' in type_lower or 'withdrawal' in type_lower:
            return 'debit'
    
    # Determine from amount sign
    return 'credit' if amount >= 0 else 'debit'


def parse_date(date_str: str) -> Optional[str]:
    """Parse date in various formats and return YYYY-MM-DD."""
    date_formats = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%d-%m-%Y',
        '%m-%d-%Y',
        '%Y/%m/%d',
        '%d.%m.%Y',
        '%m.%d.%Y'
    ]
    
    for fmt in date_formats:
        try:
            date_obj = datetime.strptime(date_str.strip(), fmt)
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return None


def categorize_transaction(description: str, transaction_type: str) -> str:
    """Auto-categorize transaction based on description."""
    desc_lower = description.lower()
    
    # Common categories with keywords
    categories = {
        'Food': ['food', 'restaurant', 'kfc', 'mcdonalds', 'eat', 'dining', 'meal'],
        'Transport': ['uber', 'taxi', 'transport', 'travel', 'fuel', 'gas', 'car', 'bus'],
        'Shopping': ['shop', 'store', 'mall', 'buy', 'purchase', 'market'],
        'Entertainment': ['movie', 'club', 'entertainment', 'game', 'fun', 'party'],
        'Bills': ['bill', 'subscription', 'rent', 'utility', 'electricity', 'water'],
        'Healthcare': ['hospital', 'doctor', 'medical', 'health', 'pharmacy'],
        'Education': ['school', 'tuition', 'education', 'course', 'book'],
        'Income': ['salary', 'wage', 'income', 'payment', 'receive'],
        'Transfer': ['transfer', 'send', 'move', 'trf']
    }
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in desc_lower:
                return category
    
    # Default categories
    return 'Income' if transaction_type == 'credit' else 'Expenses'


def calculate_balances(transactions: List[Dict]) -> List[Dict]:
    """Calculate running balance for transactions."""
    if not transactions:
        return transactions
    
    # Sort by date
    transactions.sort(key=lambda x: x['transaction_date'])
    
    # Calculate running balance
    running_balance = 0.0
    for transaction in transactions:
        if transaction['type'] == 'credit':
            running_balance += transaction['amount']
        else:
            running_balance -= transaction['amount']
        transaction['balance'] = running_balance
    
    return transactions


def validate_csv_structure(csv_content: str) -> Dict:
    """
    Validate CSV structure and return information about columns.
    
    Args:
        csv_content: CSV content as string
        
    Returns:
        Dictionary with validation results
    """
    try:
        csv_file = io.StringIO(csv_content)
        delimiter = detect_delimiter(csv_content[:1024])
        reader = csv.DictReader(csv_file, delimiter=delimiter)
        
        return {
            "valid": True,
            "delimiter": delimiter,
            "columns": reader.fieldnames,
            "column_count": len(reader.fieldnames) if reader.fieldnames else 0,
            "sample_rows": list(reader)[:5]  # First 5 rows as sample
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "delimiter": None,
            "columns": [],
            "column_count": 0,
            "sample_rows": []
        }


# Test function
def test_csv_parser():
    """Test the CSV parser with sample data."""
    sample_csv = """Date,Description,Amount,Type,Category
2026-03-01,Salary March 2026,150000,Income,Income
2026-03-01,Uber Trip,5000,Debit,Transport
2026-03-02,KFC Ikeja,4500,Debit,Food
2026-03-07,Club Outing Lagos,12000,Debit,Entertainment
2026-03-03,DSTV Subscription,5000,Debit,Bills"""
    
    result = parse_csv(sample_csv)
    print("CSV Parser Result:", result)
    return result


if __name__ == "__main__":
    test_csv_parser()