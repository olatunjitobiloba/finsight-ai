"""
Demo Seeder for Finsight AI

This module provides sample data and testing utilities for the financial insights platform.
It includes sample SMS messages, CSV data, and user profiles for testing the services.
"""

import json
from typing import Dict, List
from datetime import datetime, timedelta


# Sample SMS messages from different banks
SAMPLE_SMS_MESSAGES = [
    {
        "bank": "access",
        "message": """Debit
Amt: NGN7,500.00
Acc:190****678
Desc: 23r555432wa/MOBILE TRF TO PAY/ Payment for Ties/ MOSES
Date: 18/03/2026
Avail Bal: NGN1,405.57
Total: NGN""",
        "expected": {
            "bank": "access",
            "amount": 7500.0,
            "type": "debit",
            "date": "2026-03-18",
            "balance": 1405.57
        }
    },
    {
        "bank": "access",
        "message": """Credit
Amt: NGN50,000.00
Acc:190****678
Desc: SALARY CREDIT FOR MARCH 2026/ COMPANY LTD
Date: 01/03/2026
Avail Bal: NGN51,405.57
Total: NGN""",
        "expected": {
            "bank": "access",
            "amount": 50000.0,
            "type": "credit",
            "date": "2026-03-01",
            "balance": 51405.57
        }
    },
    {
        "bank": "access",
        "message": """Debit
Amt: NGN2,350.50
Acc:190****678
Desc: POS TRF/ SPAR LAGOS/ SHOPPING
Date: 15/03/2026
Avail Bal: NGN48,905.57
Total: NGN""",
        "expected": {
            "bank": "access",
            "amount": 2350.50,
            "type": "debit",
            "date": "2026-03-15",
            "balance": 48905.57
        }
    }
]

# Sample CSV data
SAMPLE_CSV_DATA = """Date,Description,Amount,Type,Category
2026-03-01,Salary March 2026,150000,Income,Income
2026-03-01,Uber Trip,5000,Debit,Transport
2026-03-02,KFC Ikeja,4500,Debit,Food
2026-03-07,Club Outing Lagos,12000,Debit,Entertainment
2026-03-03,DSTV Subscription,5000,Debit,Bills
2026-03-10,Electricity Bill,8500,Debit,Bills
2026-03-12,Shopping at Shoprite,8750,Debit,Shopping
2026-03-15,Pharmacy Purchase,3200,Debit,Healthcare
2026-03-18,Internet Subscription,3500,Debit,Bills
2026-03-20,Gas Station,12500,Debit,Transport
2026-03-22,Restaurant Dinner,9800,Debit,Food
2026-03-25,Cinema Tickets,4500,Debit,Entertainment
2026-03-28,Grocery Shopping,15600,Debit,Food
2026-03-30,Mobile Airtime,2000,Debit,Bills"""

# Sample user profiles
SAMPLE_USER_PROFILES = [
    {
        "user_id": "demo_user_1",
        "name": "John Doe",
        "age": 28,
        "income_level": "medium",
        "financial_goals": ["save_for_emergency", "reduce_spending"],
        "spending_habits": "frequent_dining",
        "risk_tolerance": "medium"
    },
    {
        "user_id": "demo_user_2", 
        "name": "Jane Smith",
        "age": 32,
        "income_level": "high",
        "financial_goals": ["investment_growth", "retirement_planning"],
        "spending_habits": "conscious_spender",
        "risk_tolerance": "low"
    },
    {
        "user_id": "demo_user_3",
        "name": "Mike Johnson",
        "age": 25,
        "income_level": "low",
        "financial_goals": ["budget_management", "debt_reduction"],
        "spending_habits": "impulse_buyer",
        "risk_tolerance": "high"
    }
]


def generate_sample_transactions(months: int = 3) -> List[Dict]:
    """
    Generate sample transaction data for testing.
    
    Args:
        months: Number of months of data to generate
        
    Returns:
        List of transaction dictionaries
    """
    transactions = []
    base_date = datetime.now() - timedelta(days=months * 30)
    
    # Transaction templates
    credit_transactions = [
        {"category": "Income", "description": "Salary", "amount_range": (80000, 200000)},
        {"category": "Income", "description": "Freelance Payment", "amount_range": (15000, 50000)},
        {"category": "Income", "description": "Investment Returns", "amount_range": (5000, 15000)}
    ]
    
    debit_transactions = [
        {"category": "Food", "description": "Restaurant", "amount_range": (2000, 8000)},
        {"category": "Food", "description": "Grocery Shopping", "amount_range": (5000, 15000)},
        {"category": "Transport", "description": "Uber Ride", "amount_range": (800, 3000)},
        {"category": "Transport", "description": "Fuel", "amount_range": (3000, 8000)},
        {"category": "Entertainment", "description": "Cinema", "amount_range": (2000, 5000)},
        {"category": "Entertainment", "description": "Club Outing", "amount_range": (5000, 15000)},
        {"category": "Bills", "description": "DSTV Subscription", "amount_range": (4500, 6500)},
        {"category": "Bills", "description": "Electricity Bill", "amount_range": (5000, 12000)},
        {"category": "Bills", "description": "Internet Subscription", "amount_range": (3000, 6000)},
        {"category": "Shopping", "description": "Clothing", "amount_range": (3000, 15000)},
        {"category": "Shopping", "description": "Electronics", "amount_range": (10000, 50000)},
        {"category": "Healthcare", "description": "Pharmacy", "amount_range": (1000, 5000)},
        {"category": "Healthcare", "description": "Hospital Visit", "amount_range": (5000, 20000)}
    ]
    
    import random
    
    # Generate transactions for each month
    for month in range(months):
        # Add salary (credit)
        salary_date = base_date + timedelta(days=month * 30)
        transactions.append({
            "amount": random.randint(80000, 200000),
            "type": "credit",
            "category": "Income",
            "description": "Salary",
            "transaction_date": salary_date.strftime("%Y-%m-%d"),
            "source": "generated",
            "bank": "Demo Bank",
            "balance": 0.0
        })
        
        # Generate random debit transactions (15-25 per month)
        num_debits = random.randint(15, 25)
        for i in range(num_debits):
            transaction_template = random.choice(debit_transactions)
            amount_range = transaction_template["amount_range"]
            amount = random.randint(amount_range[0], amount_range[1])
            
            # Random date within the month
            day_offset = random.randint(2, 28)
            transaction_date = salary_date + timedelta(days=day_offset)
            
            transactions.append({
                "amount": amount,
                "type": "debit",
                "category": transaction_template["category"],
                "description": transaction_template["description"],
                "transaction_date": transaction_date.strftime("%Y-%m-%d"),
                "source": "generated",
                "bank": "Demo Bank",
                "balance": 0.0
            })
    
    # Sort by date and calculate balances
    transactions.sort(key=lambda x: x['transaction_date'])
    
    running_balance = 0.0
    for transaction in transactions:
        if transaction['type'] == 'credit':
            running_balance += transaction['amount']
        else:
            running_balance -= transaction['amount']
        transaction['balance'] = running_balance
    
    return transactions


def seed_demo_data() -> Dict:
    """
    Seed the system with demo data for testing.
    
    Returns:
        Dictionary containing all demo data
    """
    return {
        "sms_messages": SAMPLE_SMS_MESSAGES,
        "csv_data": SAMPLE_CSV_DATA,
        "user_profiles": SAMPLE_USER_PROFILES,
        "sample_transactions": generate_sample_transactions(months=6),
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_transactions": len(generate_sample_transactions(months=6)),
            "data_period_months": 6,
            "banks_covered": ["access", "gt", "first", "zenith", "uba"],
            "categories": list(set(t["category"] for t in generate_sample_transactions(months=6)))
        }
    }


def test_all_services():
    """
    Test all services with demo data.
    
    Returns:
        Dictionary with test results
    """
    try:
        # Import services
        from sms_parser import parse_sms, parse_multiple_sms
        from csv_parser import parse_csv
        from interswitch import simulate_savings, simulate_bill_optimization
        
        # Test SMS parser
        sms_results = []
        for sample in SAMPLE_SMS_MESSAGES:
            parsed = parse_sms(sample["message"])
            sms_results.append({
                "input": sample["message"],
                "expected": sample["expected"],
                "actual": parsed,
                "success": bool(parsed and parsed.get("bank") == sample["expected"]["bank"])
            })
        
        # Test CSV parser
        csv_result = parse_csv(SAMPLE_CSV_DATA)
        
        # Test with generated transactions
        sample_transactions = generate_sample_transactions(months=3)
        
        # Test savings simulation
        savings_result = simulate_savings(sample_transactions)
        
        # Test bill optimization
        bill_optimization_result = simulate_bill_optimization(sample_transactions)
        
        return {
            "sms_parser_tests": sms_results,
            "csv_parser_test": csv_result,
            "savings_simulation_test": savings_result,
            "bill_optimization_test": bill_optimization_result,
            "test_summary": {
                "total_sms_tests": len(sms_results),
                "sms_tests_passed": sum(1 for r in sms_results if r["success"]),
                "csv_test_passed": csv_result.get("success_count", 0) > 0,
                "savings_test_passed": bool(savings_result.get("analysis")),
                "bill_optimization_test_passed": bool(bill_optimization_result.get("recurring_bills"))
            }
        }
        
    except ImportError as e:
        return {
            "error": f"Service import failed: {str(e)}",
            "note": "Make sure all service modules are in the same directory"
        }
    except Exception as e:
        return {
            "error": f"Testing failed: {str(e)}"
        }


def export_demo_data(filename: str = "demo_data.json"):
    """
    Export demo data to a JSON file.
    
    Args:
        filename: Output filename
    """
    demo_data = seed_demo_data()
    
    with open(filename, 'w') as f:
        json.dump(demo_data, f, indent=2, default=str)
    
    print(f"Demo data exported to {filename}")
    return filename


def import_demo_data(filename: str = "demo_data.json") -> Dict:
    """
    Import demo data from a JSON file.
    
    Args:
        filename: Input filename
        
    Returns:
        Demo data dictionary
    """
    try:
        with open(filename, 'r') as f:
            demo_data = json.load(f)
        
        print(f"Demo data imported from {filename}")
        return demo_data
        
    except FileNotFoundError:
        print(f"File {filename} not found. Generating new demo data...")
        return seed_demo_data()
    except json.JSONDecodeError as e:
        print(f"Error reading {filename}: {e}")
        return seed_demo_data()


# Performance testing utilities
def benchmark_services():
    """
    Benchmark service performance with different data sizes.
    
    Returns:
        Performance metrics
    """
    import time
    
    results = {}
    
    # Test with different data sizes
    data_sizes = [10, 50, 100, 500, 1000]
    
    for size in data_sizes:
        # Generate test data
        transactions = generate_sample_transactions(months=1)[:size]
        
        # Benchmark SMS parsing
        start_time = time.time()
        for sample in SAMPLE_SMS_MESSAGES[:min(3, len(SAMPLE_SMS_MESSAGES))]:
            from sms_parser import parse_sms
            parse_sms(sample["message"])
        sms_time = time.time() - start_time
        
        # Benchmark CSV parsing
        start_time = time.time()
        from csv_parser import parse_csv
        parse_csv(SAMPLE_CSV_DATA)
        csv_time = time.time() - start_time
        
        # Benchmark savings simulation
        start_time = time.time()
        from interswitch import simulate_savings
        simulate_savings(transactions)
        savings_time = time.time() - start_time
        
        results[f"size_{size}"] = {
            "sms_parse_time": sms_time,
            "csv_parse_time": csv_time,
            "savings_simulation_time": savings_time,
            "total_time": sms_time + csv_time + savings_time
        }
    
    return results


# Demo scenarios
def create_demo_scenarios() -> Dict:
    """
    Create predefined demo scenarios for different user types.
    
    Returns:
        Dictionary of demo scenarios
    """
    scenarios = {
        "young_professional": {
            "description": "28-year-old professional with moderate income",
            "transactions": generate_sample_transactions(months=3),
            "profile": SAMPLE_USER_PROFILES[0],
            "expected_insights": ["high_food_spending", "transport_optimization", "savings_potential"]
        },
        "high_earner": {
            "description": "32-year-old with high income and investment focus",
            "transactions": generate_sample_transactions(months=3),
            "profile": SAMPLE_USER_PROFILES[1],
            "expected_insights": ["investment_opportunities", "tax_optimization", "wealth_building"]
        },
        "budget_conscious": {
            "description": "25-year-old focused on budget management",
            "transactions": generate_sample_transactions(months=3),
            "profile": SAMPLE_USER_PROFILES[2],
            "expected_insights": ["expense_tracking", "bill_optimization", "emergency_fund"]
        }
    }
    
    return scenarios


if __name__ == "__main__":
    # Run demo tests
    print("=== Finsight AI Demo Seeder ===")
    print("\n1. Testing all services...")
    test_results = test_all_services()
    print(json.dumps(test_results, indent=2, default=str))
    
    print("\n2. Exporting demo data...")
    export_demo_data()
    
    print("\n3. Creating demo scenarios...")
    scenarios = create_demo_scenarios()
    print(f"Created {len(scenarios)} demo scenarios")
    
    print("\n4. Benchmarking performance...")
    benchmarks = benchmark_services()
    print("Performance benchmarks:")
    for size, metrics in benchmarks.items():
        print(f"  {size}: {metrics['total_time']:.3f}s total")
    
    print("\nDemo seeder completed successfully!")