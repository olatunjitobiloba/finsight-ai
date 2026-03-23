import requests
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import json


def simulate_saving(amount: float, plan_type: str, user_profile: Optional[Dict] = None) -> Dict:
    """
    Simulate and initiate a savings plan for a user.
    
    Args:
        amount: Amount to save (in NGN)
        plan_type: Type of savings plan ('weekly', 'monthly', 'quarterly', 'custom')
        user_profile: Optional user profile data
        
    Returns:
        Dictionary with savings plan details and projections
    """
    try:
        # Validate inputs
        if amount <= 0:
            return {
                "error": "Amount must be greater than 0",
                "status": "failed"
            }
        
        valid_plans = ['weekly', 'monthly', 'quarterly', 'custom']
        if plan_type not in valid_plans:
            return {
                "error": f"Invalid plan type. Must be one of: {valid_plans}",
                "status": "failed"
            }
        
        # Calculate savings schedule
        schedule = calculate_savings_schedule(amount, plan_type)
        
        # Calculate projections
        projections = calculate_savings_projections(amount, plan_type, schedule)
        
        # Generate recommendations
        recommendations = generate_savings_plan_recommendations(amount, plan_type, user_profile)
        
        # Create savings plan
        savings_plan = {
            "plan_id": f"SAV_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "amount": amount,
            "plan_type": plan_type,
            "schedule": schedule,
            "projections": projections,
            "recommendations": recommendations,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "user_profile": user_profile or {}
        }
        
        # Simulate Interswitch integration
        integration_result = initiate_savings_with_interswitch(savings_plan)
        
        return {
            "savings_plan": savings_plan,
            "integration": integration_result,
            "success": True,
            "message": f"Savings plan of ₦{amount:,.2f} ({plan_type}) initiated successfully"
        }
        
    except Exception as e:
        return {
            "error": f"Savings plan initiation failed: {str(e)}",
            "status": "failed",
            "success": False
        }


def calculate_savings_schedule(amount: float, plan_type: str) -> Dict:
    """Calculate savings schedule based on plan type."""
    now = datetime.now()
    
    if plan_type == "weekly":
        # Save every week
        frequency = "weekly"
        interval_days = 7
        next_date = now + timedelta(days=7)
        annual_frequency = 52
        
    elif plan_type == "monthly":
        # Save every month
        frequency = "monthly"
        interval_days = 30
        next_date = now + timedelta(days=30)
        annual_frequency = 12
        
    elif plan_type == "quarterly":
        # Save every quarter
        frequency = "quarterly"
        interval_days = 90
        next_date = now + timedelta(days=90)
        annual_frequency = 4
        
    else:  # custom
        frequency = "custom"
        interval_days = 30  # Default to monthly
        next_date = now + timedelta(days=30)
        annual_frequency = 12
    
    return {
        "frequency": frequency,
        "interval_days": interval_days,
        "next_deposit_date": next_date.strftime("%Y-%m-%d"),
        "annual_deposits": annual_frequency,
        "total_annual_amount": amount * annual_frequency
    }


def calculate_savings_projections(amount: float, plan_type: str, schedule: Dict) -> Dict:
    """Calculate savings projections with interest."""
    # Assume 5% annual interest rate for savings
    annual_interest_rate = 0.05
    
    # Calculate projections for different time periods
    projections = {}
    
    periods = [1, 3, 6, 12, 24, 36, 60]  # months
    
    for months in periods:
        years = months / 12
        total_deposits = amount * schedule["annual_deposits"] * years
        
        # Simple interest calculation (can be enhanced to compound interest)
        interest_earned = total_deposits * annual_interest_rate * years
        total_value = total_deposits + interest_earned
        
        projections[f"{months}_months"] = {
            "total_deposits": total_deposits,
            "interest_earned": interest_earned,
            "total_value": total_value,
            "monthly_average": total_value / months if months > 0 else 0
        }
    
    return projections


def generate_savings_plan_recommendations(amount: float, plan_type: str, user_profile: Optional[Dict]) -> List[Dict]:
    """Generate recommendations for the savings plan."""
    recommendations = []
    
    # Income-based recommendations
    if user_profile and "income_level" in user_profile:
        income_level = user_profile["income_level"]
        
        if income_level == "low":
            if amount > 5000:
                recommendations.append({
                    "type": "affordability",
                    "message": "Consider starting with a smaller amount and gradually increasing",
                    "priority": "high"
                })
        elif income_level == "high":
            recommendations.append({
                "type": "optimization",
                "message": "Consider diversifying savings across multiple plans for better returns",
                "priority": "medium"
            })
    
    # Plan type recommendations
    if plan_type == "weekly":
        recommendations.append({
            "type": "frequency",
            "message": "Weekly savings build discipline but require consistent cash flow",
            "priority": "medium"
        })
    elif plan_type == "monthly":
        recommendations.append({
            "type": "timing",
            "message": "Monthly savings align well with salary schedules",
            "priority": "low"
        })
    
    # General recommendations
    recommendations.append({
        "type": "emergency",
        "message": "Build an emergency fund equivalent to 3-6 months of expenses",
        "priority": "high"
    })
    
    recommendations.append({
        "type": "automation",
        "message": "Set up automatic deductions to ensure consistency",
        "priority": "high"
    })
    
    return recommendations


def initiate_savings_with_interswitch(savings_plan: Dict) -> Dict:
    """
    Simulate integration with Interswitch for savings plan initiation.
    
    Args:
        savings_plan: The savings plan details
        
    Returns:
        Integration result from Interswitch
    """
    # Mock Interswitch API response
    integration_id = f"ISW_SAV_{datetime.now().timestamp()}"
    
    return {
        "integration_id": integration_id,
        "provider": "Interswitch",
        "status": "confirmed",
        "transaction_reference": f"TRX_{integration_id}",
        "confirmation_message": "Savings plan has been registered with Interswitch payment system",
        "next_steps": [
            "Link your bank account for automatic deductions",
            "Set up payment method",
            "Verify your identity",
            "Confirm first deposit date"
        ],
        "fees": {
            "setup_fee": 0.0,  # No setup fee
            "transaction_fee": 0.0,  # No transaction fee for savings
            "maintenance_fee": 0.0  # No maintenance fee
        }
    }


def simulate_savings(transactions: List[Dict], user_profile: Optional[Dict] = None) -> Dict:
    """
    Simulate potential savings based on transaction patterns.
    
    Args:
        transactions: List of transaction dictionaries
        user_profile: Optional user profile data
        
    Returns:
        Dictionary with savings recommendations and analysis
    """
    try:
        # Analyze spending patterns
        spending_analysis = analyze_spending_patterns(transactions)
        
        # Calculate potential savings
        savings_opportunities = identify_savings_opportunities(spending_analysis)
        
        # Generate recommendations
        recommendations = generate_savings_recommendations(savings_opportunities, user_profile)
        
        return {
            "analysis": spending_analysis,
            "opportunities": savings_opportunities,
            "recommendations": recommendations,
            "potential_monthly_savings": sum(opp["potential_savings"] for opp in savings_opportunities),
            "projected_annual_savings": sum(opp["potential_savings"] for opp in savings_opportunities) * 12,
            "confidence_score": calculate_confidence_score(transactions),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": f"Savings simulation failed: {str(e)}",
            "analysis": {},
            "opportunities": [],
            "recommendations": [],
            "potential_monthly_savings": 0.0,
            "projected_annual_savings": 0.0
        }


def simulate_bill_optimization(transactions: List[Dict]) -> Dict:
    """
    Simulate bill payment optimization strategies.
    
    Args:
        transactions: List of transaction dictionaries
        
    Returns:
        Dictionary with bill optimization recommendations
    """
    try:
        # Identify recurring bills
        recurring_bills = identify_recurring_bills(transactions)
        
        # Analyze payment patterns
        payment_analysis = analyze_payment_patterns(recurring_bills)
        
        # Generate optimization strategies
        optimization_strategies = generate_optimization_strategies(recurring_bills, payment_analysis)
        
        return {
            "recurring_bills": recurring_bills,
            "payment_analysis": payment_analysis,
            "optimization_strategies": optimization_strategies,
            "potential_monthly_savings": calculate_bill_savings(optimization_strategies),
            "implementation_priority": prioritize_optimizations(optimization_strategies),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": f"Bill optimization failed: {str(e)}",
            "recurring_bills": [],
            "optimization_strategies": [],
            "potential_monthly_savings": 0.0
        }


def analyze_spending_patterns(transactions: List[Dict]) -> Dict:
    """Analyze spending patterns across different categories."""
    if not transactions:
        return {}
    
    # Filter only debit transactions
    debit_transactions = [t for t in transactions if t.get('type') == 'debit']
    
    # Group by category
    category_spending = {}
    for transaction in debit_transactions:
        category = transaction.get('category', 'Uncategorized')
        amount = transaction.get('amount', 0.0)
        
        if category not in category_spending:
            category_spending[category] = {
                'total_spent': 0.0,
                'transaction_count': 0,
                'average_transaction': 0.0,
                'transactions': []
            }
        
        category_spending[category]['total_spent'] += amount
        category_spending[category]['transaction_count'] += 1
        category_spending[category]['transactions'].append(transaction)
    
    # Calculate averages
    for category in category_spending:
        count = category_spending[category]['transaction_count']
        if count > 0:
            category_spending[category]['average_transaction'] = (
                category_spending[category]['total_spent'] / count
            )
    
    # Calculate monthly averages
    monthly_spending = calculate_monthly_averages(debit_transactions)
    
    return {
        'category_breakdown': category_spending,
        'monthly_averages': monthly_spending,
        'total_debit_transactions': len(debit_transactions),
        'total_spent': sum(t.get('amount', 0.0) for t in debit_transactions)
    }


def identify_savings_opportunities(spending_analysis: Dict) -> List[Dict]:
    """Identify potential savings opportunities based on spending patterns."""
    opportunities = []
    
    if not spending_analysis or 'category_breakdown' not in spending_analysis:
        return opportunities
    
    categories = spending_analysis['category_breakdown']
    
    # High spending categories
    for category, data in categories.items():
        monthly_avg = data['total_spent'] / 12  # Assuming data covers ~12 months
        
        # Food/Restaurant savings
        if category.lower() in ['food', 'restaurant', 'dining']:
            if monthly_avg > 20000:  # NGN 20k+ monthly on food
                potential_savings = monthly_avg * 0.3  # 30% potential savings
                opportunities.append({
                    'category': category,
                    'type': 'reduce_frequency',
                    'current_monthly': monthly_avg,
                    'potential_savings': potential_savings,
                    'recommendation': 'Consider meal planning and reducing restaurant visits',
                    'difficulty': 'medium'
                })
        
        # Entertainment savings
        elif category.lower() in ['entertainment', 'fun', 'party']:
            if monthly_avg > 15000:
                potential_savings = monthly_avg * 0.4  # 40% potential savings
                opportunities.append({
                    'category': category,
                    'type': 'budget_cut',
                    'current_monthly': monthly_avg,
                    'potential_savings': potential_savings,
                    'recommendation': 'Set monthly entertainment budget and explore free alternatives',
                    'difficulty': 'easy'
                })
        
        # Transport savings
        elif category.lower() in ['transport', 'uber', 'taxi']:
            if monthly_avg > 25000:
                potential_savings = monthly_avg * 0.25  # 25% potential savings
                opportunities.append({
                    'category': category,
                    'type': 'alternative_transport',
                    'current_monthly': monthly_avg,
                    'potential_savings': potential_savings,
                    'recommendation': 'Consider public transport or carpooling options',
                    'difficulty': 'medium'
                })
    
    return sorted(opportunities, key=lambda x: x['potential_savings'], reverse=True)


def generate_savings_recommendations(opportunities: List[Dict], user_profile: Optional[Dict]) -> List[Dict]:
    """Generate actionable savings recommendations."""
    recommendations = []
    
    for opp in opportunities:
        recommendation = {
            'title': f"Reduce {opp['category']} Spending",
            'description': opp['recommendation'],
            'potential_monthly_savings': opp['potential_savings'],
            'difficulty': opp['difficulty'],
            'time_to_implement': get_implementation_time(opp['difficulty']),
            'steps': get_implementation_steps(opp['type']),
            'success_metrics': get_success_metrics(opp['category'])
        }
        recommendations.append(recommendation)
    
    return recommendations


def identify_recurring_bills(transactions: List[Dict]) -> List[Dict]:
    """Identify recurring bills from transactions."""
    if not transactions:
        return []
    
    # Filter debit transactions with bill-like descriptions
    bill_keywords = ['subscription', 'bill', 'rent', 'utility', 'dstv', 'gotv', 'electricity', 'water']
    potential_bills = []
    
    for transaction in transactions:
        if transaction.get('type') == 'debit':
            description = transaction.get('description', '').lower()
            if any(keyword in description for keyword in bill_keywords):
                potential_bills.append(transaction)
    
    # Group similar bills
    recurring_bills = group_similar_bills(potential_bills)
    
    return recurring_bills


def group_similar_bills(bills: List[Dict]) -> List[Dict]:
    """Group similar bills to identify recurring patterns."""
    if not bills:
        return []
    
    # Simple grouping by description similarity
    grouped = {}
    
    for bill in bills:
        description = bill.get('description', '')
        # Simplify description for grouping
        simplified = simplify_bill_description(description)
        
        if simplified not in grouped:
            grouped[simplified] = []
        grouped[simplified].append(bill)
    
    # Create recurring bill objects
    recurring_bills = []
    for simplified_desc, bill_list in grouped.items():
        if len(bill_list) >= 2:  # At least 2 occurrences to be considered recurring
            amounts = [b.get('amount', 0.0) for b in bill_list]
            recurring_bills.append({
                'name': simplified_desc,
                'frequency': len(bill_list),
                'average_amount': sum(amounts) / len(amounts),
                'amount_range': {'min': min(amounts), 'max': max(amounts)},
                'total_spent': sum(amounts),
                'transactions': bill_list,
                'category': bill_list[0].get('category', 'Bills')
            })
    
    return sorted(recurring_bills, key=lambda x: x['total_spent'], reverse=True)


def simplify_bill_description(description: str) -> str:
    """Simplify bill description for grouping."""
    # Remove numbers, dates, and specific details
    import re
    simplified = re.sub(r'\d+', '', description)  # Remove numbers
    simplified = re.sub(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b', '', simplified, flags=re.IGNORECASE)
    simplified = ' '.join(simplified.split())  # Normalize whitespace
    
    return simplified.strip().title()


def analyze_payment_patterns(recurring_bills: List[Dict]) -> Dict:
    """Analyze payment patterns for recurring bills."""
    if not recurring_bills:
        return {}
    
    total_monthly_bills = sum(bill['average_amount'] for bill in recurring_bills)
    
    # Categorize by amount
    high_value_bills = [b for b in recurring_bills if b['average_amount'] > 10000]
    medium_value_bills = [b for b in recurring_bills if 5000 <= b['average_amount'] <= 10000]
    low_value_bills = [b for b in recurring_bills if b['average_amount'] < 5000]
    
    return {
        'total_monthly_bills': total_monthly_bills,
        'bill_count': len(recurring_bills),
        'high_value_bills': high_value_bills,
        'medium_value_bills': medium_value_bills,
        'low_value_bills': low_value_bills,
        'highest_bill': max(recurring_bills, key=lambda x: x['average_amount']) if recurring_bills else None
    }


def generate_optimization_strategies(recurring_bills: List[Dict], payment_analysis: Dict) -> List[Dict]:
    """Generate bill optimization strategies."""
    strategies = []
    
    for bill in recurring_bills:
        # Subscription optimization
        if 'subscription' in bill['name'].lower():
            strategies.append({
                'bill_name': bill['name'],
                'strategy': 'subscription_review',
                'potential_savings': bill['average_amount'] * 0.5,  # 50% potential savings
                'description': 'Review subscription usage and consider downgrading or canceling',
                'action_items': [
                    'Check if you use this service regularly',
                    'Look for cheaper alternatives',
                    'Consider annual billing for discounts'
                ]
            })
        
        # Utility optimization
        elif any(keyword in bill['name'].lower() for keyword in ['electricity', 'water', 'utility']):
            strategies.append({
                'bill_name': bill['name'],
                'strategy': 'utility_conservation',
                'potential_savings': bill['average_amount'] * 0.2,  # 20% potential savings
                'description': 'Implement conservation measures to reduce utility costs',
                'action_items': [
                    'Use energy-efficient appliances',
                    'Fix leaks and drafts',
                    'Consider off-peak usage'
                ]
            })
    
    return strategies


def calculate_bill_savings(strategies: List[Dict]) -> float:
    """Calculate total potential bill savings."""
    return sum(strategy['potential_savings'] for strategy in strategies)


def prioritize_optimizations(strategies: List[Dict]) -> List[Dict]:
    """Prioritize optimization strategies by impact and ease."""
    # Sort by potential savings (descending)
    return sorted(strategies, key=lambda x: x['potential_savings'], reverse=True)


def calculate_monthly_averages(transactions: List[Dict]) -> Dict:
    """Calculate monthly spending averages."""
    monthly_data = {}
    
    for transaction in transactions:
        date_str = transaction.get('transaction_date', '')
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                month_key = date_obj.strftime('%Y-%m')
                
                if month_key not in monthly_data:
                    monthly_data[month_key] = 0.0
                
                monthly_data[month_key] += transaction.get('amount', 0.0)
            except ValueError:
                continue
    
    return monthly_data


def calculate_confidence_score(transactions: List[Dict]) -> float:
    """Calculate confidence score for recommendations based on data quality."""
    if not transactions:
        return 0.0
    
    # Factors affecting confidence
    transaction_count = len(transactions)
    date_range = calculate_date_range(transactions)
    category_diversity = len(set(t.get('category', '') for t in transactions))
    
    # Score calculation (0-100)
    score = 0.0
    
    # Transaction count factor (max 40 points)
    if transaction_count >= 100:
        score += 40
    elif transaction_count >= 50:
        score += 30
    elif transaction_count >= 20:
        score += 20
    elif transaction_count >= 10:
        score += 10
    
    # Date range factor (max 30 points)
    if date_range >= 180:  # 6+ months
        score += 30
    elif date_range >= 90:  # 3+ months
        score += 20
    elif date_range >= 30:  # 1+ month
        score += 10
    
    # Category diversity factor (max 30 points)
    if category_diversity >= 8:
        score += 30
    elif category_diversity >= 5:
        score += 20
    elif category_diversity >= 3:
        score += 10
    
    return min(score, 100.0)


def calculate_date_range(transactions: List[Dict]) -> int:
    """Calculate the date range in days."""
    if not transactions:
        return 0
    
    dates = []
    for transaction in transactions:
        date_str = transaction.get('transaction_date', '')
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                dates.append(date_obj)
            except ValueError:
                continue
    
    if len(dates) < 2:
        return 0
    
    return (max(dates) - min(dates)).days


def get_implementation_time(difficulty: str) -> str:
    """Get estimated implementation time based on difficulty."""
    time_map = {
        'easy': '1-2 weeks',
        'medium': '3-4 weeks',
        'hard': '1-2 months'
    }
    return time_map.get(difficulty, 'Unknown')


def get_implementation_steps(strategy_type: str) -> List[str]:
    """Get implementation steps for different strategy types."""
    steps_map = {
        'reduce_frequency': [
            'Track current spending habits',
            'Set reduction targets',
            'Find alternatives',
            'Monitor progress weekly'
        ],
        'budget_cut': [
            'Set monthly budget limits',
            'Use expense tracking apps',
            'Review spending weekly',
            'Adjust as needed'
        ],
        'alternative_transport': [
            'Research transport options',
            'Compare costs and time',
            'Try alternatives gradually',
            'Measure savings'
        ]
    }
    return steps_map.get(strategy_type, ['Analyze current patterns', 'Set goals', 'Implement changes', 'Track results'])


def get_success_metrics(category: str) -> List[str]:
    """Get success metrics for different categories."""
    metrics_map = {
        'Food': ['Monthly food spending reduced by 20%', 'Home-cooked meals increased to 70%'],
        'Entertainment': ['Entertainment budget adherence', 'Free activities utilization'],
        'Transport': ['Transport costs reduced', 'Alternative transport usage frequency']
    }
    return metrics_map.get(category, ['Spending reduction achieved', 'Budget maintained'])


# Mock Interswitch API functions (for demonstration)
def call_interswitch_api(endpoint: str, data: Dict) -> Dict:
    """
    Mock function for Interswitch API calls.
    In production, this would make actual HTTP requests to Interswitch APIs.
    """
    # This is a placeholder for actual API integration
    return {
        "status": "success",
        "message": "API call simulated",
        "endpoint": endpoint,
        "data": data
    }


def validate_transaction_with_interswitch(transaction: Dict) -> Dict:
    """
    Validate transaction using Interswitch services.
    """
    # Mock validation
    return {
        "valid": True,
        "transaction_id": f"ISW_{datetime.now().timestamp()}",
        "validation_score": 0.95,
        "risk_level": "low"
    }


# Test functions
def test_savings_simulation():
    """Test the savings simulation with sample data."""
    sample_transactions = [
        {"amount": 5000, "type": "debit", "category": "Food", "description": "Restaurant", "transaction_date": "2026-03-01"},
        {"amount": 15000, "type": "debit", "category": "Entertainment", "description": "Club outing", "transaction_date": "2026-03-02"},
        {"amount": 8000, "type": "debit", "category": "Transport", "description": "Uber rides", "transaction_date": "2026-03-03"}
    ]
    
    result = simulate_savings(sample_transactions)
    print("Savings Simulation:", json.dumps(result, indent=2))
    return result


def test_bill_optimization():
    """Test the bill optimization with sample data."""
    sample_transactions = [
        {"amount": 5000, "type": "debit", "category": "Bills", "description": "DSTV Subscription", "transaction_date": "2026-03-01"},
        {"amount": 12000, "type": "debit", "category": "Bills", "description": "Electricity Bill", "transaction_date": "2026-03-05"}
    ]
    
    result = simulate_bill_optimization(sample_transactions)
    print("Bill Optimization:", json.dumps(result, indent=2))
    return result


def test_saving_plan():
    """Test the new savings plan function."""
    print("=== Testing Savings Plan Function ===")
    
    # Test basic savings plan
    result1 = simulate_saving(5000, "monthly")
    print("\n1. Basic Monthly Plan:")
    print(json.dumps(result1, indent=2))
    
    # Test with user profile
    user_profile = {
        "income_level": "medium",
        "age": 28,
        "financial_goals": ["emergency_fund"]
    }
    result2 = simulate_saving(10000, "weekly", user_profile)
    print("\n2. Weekly Plan with Profile:")
    print(json.dumps(result2, indent=2))
    
    # Test error cases
    result3 = simulate_saving(-1000, "monthly")
    print("\n3. Invalid Amount:")
    print(json.dumps(result3, indent=2))
    
    result4 = simulate_saving(5000, "invalid_plan")
    print("\n4. Invalid Plan Type:")
    print(json.dumps(result4, indent=2))


if __name__ == "__main__":
    test_saving_plan()
    test_savings_simulation()
    test_bill_optimization()    