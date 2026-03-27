import csv
import io
import re
from datetime import datetime
from typing import Dict, List, Optional, Union
from decimal import Decimal, InvalidOperation


INVOICE_ESTIMATED_COST_RATIO = 0.62


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
        total_rows = 0
        
        # Use io.StringIO to treat string as file
        csv_file = io.StringIO(csv_content)
        
        # Try to detect delimiter
        sample = csv_content[:1024]
        delimiter = detect_delimiter(sample)
        
        # Read CSV
        reader = csv.DictReader(csv_file, delimiter=delimiter)

        if not reader.fieldnames:
            return {
                "parsed": [],
                "failed": ["CSV parsing error: Missing header row"],
                "total": 0,
                "success_count": 0,
                "fail_count": 0,
                "success_rate": 0.0
            }
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
            total_rows += 1
            try:
                # Skip fully blank rows that can appear at EOF.
                if not row or not any(str(v).strip() for v in row.values() if v is not None):
                    continue

                parsed_result = parse_csv_row(row, row_num)
                if isinstance(parsed_result, list):
                    transactions.extend(parsed_result)
                elif parsed_result:
                    transactions.append(parsed_result)
                else:
                    failed_rows.append(f"Row {row_num}: Invalid data format")
            except Exception as e:
                failed_rows.append(f"Row {row_num}: {str(e)}")
        
        # Calculate running balance
        transactions = calculate_balances(transactions)
        
        # Prepare results
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


def parse_csv_row(row: Dict, row_num: int) -> Optional[Union[Dict, List[Dict]]]:
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
        normalized_row = {}
        for k, v in row.items():
            if k is None:
                continue
            raw_key = str(k).strip()
            # Normalize snake_case, kebab-case, space-separated, and camelCase headers.
            key = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', raw_key)
            key = key.lower().replace("-", "_").replace(" ", "_")
            normalized_row[key] = "" if v is None else str(v).strip()
        
        # Extract date
        date_str = get_field_value(normalized_row, [
            'date',
            'transaction_date',
            'transactiondatetime',
            'transaction_datetime',
            'invoicedate',
            'invoice_date',
            'order_date',
            'ship_date',
            'posted_date',
            'value_date',
            'created_at',
            'timestamp'
        ])
        if not date_str:
            return None
        
        parsed_date = parse_date(date_str)
        if not parsed_date:
            return None
        
        # Extract description
        description = get_field_value(
            normalized_row,
            [
                'description',
                'particulars',
                'narration',
                'details',
                'memo',
                'remark',
                'merchant',
                'note',
                'item_type',
                'item',
                'product',
                'stock_code',
                'stockcode'
            ]
        )
        if not description:
            # Build a useful fallback description for generic business/sales CSVs.
            parts = [
                get_field_value(normalized_row, ['item_type', 'item', 'product']),
                get_field_value(normalized_row, ['country', 'region']),
                get_field_value(normalized_row, ['order_id', 'invoice', 'invoice_no', 'invoiceno', 'reference'])
            ]
            composed = " | ".join([p for p in parts if p])
            description = composed or "Transaction"

        # Sales/business CSV shape: emit revenue + cost transactions per row
        # so downstream cashflow/pattern engines receive both inflow and outflow signals.
        revenue = extract_sales_value(normalized_row, [
            'total_revenue', 'revenue', 'net_revenue', 'sales', 'gross_sales'
        ])
        cost = extract_sales_value(normalized_row, [
            'total_cost', 'cost', 'unit_cost', 'expense', 'expenses'
        ])
        if revenue is not None or cost is not None:
            sales_transactions = []
            sales_category = get_field_value(normalized_row, ['item_type', 'category', 'type']) or 'Sales'

            if revenue is not None and revenue > 0:
                sales_transactions.append({
                    "amount": abs(float(revenue)),
                    "type": "credit",
                    "category": sales_category,
                    "description": f"{description} (Revenue)",
                    "transaction_date": parsed_date,
                    "source": "csv",
                    "bank": "CSV Import",
                    "balance": 0.0
                })

            if cost is not None and cost > 0:
                sales_transactions.append({
                    "amount": abs(float(cost)),
                    "type": "debit",
                    "category": "Operations",
                    "description": f"{description} (Cost)",
                    "transaction_date": parsed_date,
                    "source": "csv",
                    "bank": "CSV Import",
                    "balance": 0.0
                })

            if sales_transactions:
                return sales_transactions

        # Invoice-ledger shape (e.g. InvoiceNo/Quantity/UnitPrice) with no explicit
        # debit/cost columns: emit revenue + estimated cost so runway/pattern engines
        # have both inflow and outflow signals.
        quantity_raw = get_field_value(normalized_row, ['quantity', 'qty'])
        unit_price_raw = get_field_value(normalized_row, ['unit_price', 'unitprice', 'price'])
        has_explicit_flow_columns = any(
            get_field_value(normalized_row, [name])
            for name in ['debit', 'credit', 'total_cost', 'cost', 'total_revenue', 'revenue']
        )
        if quantity_raw and unit_price_raw and not has_explicit_flow_columns:
            try:
                quantity = clean_numeric_value(quantity_raw)
                unit_price = clean_numeric_value(unit_price_raw)
                line_total = quantity * unit_price
            except (ValueError, InvalidOperation):
                line_total = 0

            if line_total > 0:
                estimated_cost = abs(line_total) * INVOICE_ESTIMATED_COST_RATIO
                invoice_category = get_field_value(normalized_row, ['category', 'item_type']) or 'Sales'
                return [
                    {
                        "amount": abs(float(line_total)),
                        "type": "credit",
                        "category": invoice_category,
                        "description": f"{description} (Revenue)",
                        "transaction_date": parsed_date,
                        "source": "csv",
                        "bank": "CSV Import",
                        "balance": 0.0
                    },
                    {
                        "amount": abs(float(estimated_cost)),
                        "type": "debit",
                        "category": "Operations",
                        "description": f"{description} (Estimated Cost)",
                        "transaction_date": parsed_date,
                        "source": "csv",
                        "bank": "CSV Import",
                        "balance": 0.0
                    }
                ]
            if line_total < 0:
                return {
                    "amount": abs(float(line_total)),
                    "type": "debit",
                    "category": "Returns",
                    "description": f"{description} (Return)",
                    "transaction_date": parsed_date,
                    "source": "csv",
                    "bank": "CSV Import",
                    "balance": 0.0
                }

        # Extract amount
        amount = extract_amount(normalized_row)
        if amount is None:
            return None

        # Extract transaction type
        transaction_type = determine_transaction_type(normalized_row, amount)
        
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
    # Try invoice-style amount derivation first: quantity * unit_price.
    quantity_raw = get_field_value(row, ['quantity', 'qty'])
    unit_price_raw = get_field_value(row, ['unit_price', 'unitprice', 'price'])
    if quantity_raw and unit_price_raw:
        try:
            quantity = clean_numeric_value(quantity_raw)
            unit_price = clean_numeric_value(unit_price_raw)
            derived = quantity * unit_price
            if derived != 0:
                return derived
        except (ValueError, InvalidOperation):
            pass

    # Try direct amount column
    amount_fields = [
        'amount',
        'value',
        'sum',
        'total',
        'amount_paid',
        'sales',
        'transaction_amount',
        'total_revenue',
        'revenue',
        'net_revenue',
        'total_profit',
        'profit',
        'gross_profit',
        'total_cost',
        'cost',
        'unit_price',
        'unitprice',
        'line_total',
        'linetotal'
    ]
    for field in amount_fields:
        if field in row and row[field]:
            try:
                return clean_numeric_value(str(row[field]))
            except (ValueError, InvalidOperation):
                continue
    
    # Try debit/credit columns
    debit = get_field_value(row, ['debit', 'withdrawal', 'expense', 'debit_amount', 'dr'])
    credit = get_field_value(row, ['credit', 'deposit', 'income', 'credit_amount', 'cr'])
    
    if debit:
        try:
            amount = clean_numeric_value(debit)
            return -abs(amount)  # Debits are negative
        except (ValueError, InvalidOperation):
            pass
    
    if credit:
        try:
            amount = clean_numeric_value(credit)
            return abs(amount)  # Credits are positive
        except (ValueError, InvalidOperation):
            pass
    
    return None


def extract_sales_value(row: Dict, fields: List[str]) -> Optional[float]:
    """Extract numeric value from the first available sales metric field."""
    for field in fields:
        raw = row.get(field)
        if raw in (None, ""):
            continue
        try:
            return clean_numeric_value(str(raw))
        except (ValueError, InvalidOperation):
            continue
    return None


def determine_transaction_type(row: Dict, amount: float) -> str:
    """Determine if transaction is credit or debit."""
    # Check explicit type field
    type_field = get_field_value(row, ['type', 'transaction_type', 'category'])
    if type_field:
        type_lower = type_field.lower()
        if 'credit' in type_lower or 'income' in type_lower or 'deposit' in type_lower or type_lower == 'cr':
            return 'credit'
        elif 'debit' in type_lower or 'expense' in type_lower or 'withdrawal' in type_lower or type_lower == 'dr':
            return 'debit'

    # Business/sales datasets are often inflows by default.
    sales_channel = get_field_value(row, ['sales_channel'])
    if sales_channel:
        return 'credit'
    
    # Determine from amount sign
    return 'credit' if amount >= 0 else 'debit'


def parse_date(date_str: str) -> Optional[str]:
    """Parse date in various formats and return YYYY-MM-DD."""
    cleaned = date_str.strip()
    date_formats = [
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%d/%m/%Y',
        '%d/%m/%Y %H:%M:%S',
        '%d/%m/%Y %H:%M',
        '%m/%d/%Y',
        '%m/%d/%Y %H:%M:%S',
        '%m/%d/%Y %H:%M',
        '%d-%m-%Y',
        '%d-%m-%Y %H:%M:%S',
        '%d-%m-%Y %H:%M',
        '%m-%d-%Y',
        '%Y/%m/%d',
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d %H:%M',
        '%d.%m.%Y',
        '%m.%d.%Y',
        '%d %b %Y',
        '%d %B %Y',
        '%d %b %Y %H:%M',
        '%d %B %Y %H:%M'
    ]
    
    for fmt in date_formats:
        try:
            date_obj = datetime.strptime(cleaned, fmt)
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            continue

    # Final fallback: common ISO-like timestamps with timezone suffix.
    try:
        iso_candidate = cleaned.replace('Z', '+00:00')
        date_obj = datetime.fromisoformat(iso_candidate)
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        pass
    
    return None


def clean_numeric_value(value: str) -> float:
    """Normalize and parse currency-like numeric strings to float."""
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Empty numeric value")

    # Handle negatives in accounting format, e.g. (1,234.56)
    is_negative = cleaned.startswith('(') and cleaned.endswith(')')
    if is_negative:
        cleaned = cleaned[1:-1]

    cleaned = cleaned.replace('NGN', '').replace('N', '').replace(',', '')
    cleaned = re.sub(r'[^0-9.\-]', '', cleaned)

    if cleaned in {'', '-', '.', '-.'}:
        raise ValueError(f"Invalid numeric value: {value}")

    numeric = float(cleaned)
    return -abs(numeric) if is_negative else numeric


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