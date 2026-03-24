"""
Integration Test Suite for FinSight AI

This file tests the complete integration of all services and endpoints
to ensure the fintech platform works end-to-end.
"""

import requests
import json
import time
from typing import Dict, Any

# Base URL for the API
BASE_URL = "http://localhost:8000"


class IntegrationTester:
    """Main integration testing class"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = []
    
    def log_result(self, test_name: str, success: bool, message: str, data: Any = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "data": data
        }
        self.results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if data and not success:
            print(f"   Error details: {json.dumps(data, indent=2)}")
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Health Check", True, f"Status: {data.get('status', 'unknown')}")
            else:
                self.log_result("Health Check", False, f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_result("Health Check", False, f"Connection error: {str(e)}")
    
    def test_root_endpoint(self):
        """Test the root endpoint"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                endpoints = data.get('endpoints', [])
                self.log_result("Root Endpoint", True, f"Found {len(endpoints)} endpoints")
            else:
                self.log_result("Root Endpoint", False, f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_result("Root Endpoint", False, f"Connection error: {str(e)}")
    
    def test_sms_parsing(self):
        """Test SMS parsing endpoints"""
        # Test single SMS parsing
        try:
            access_sms = """Credit 
Amt:NGN2,000.00 
Acc:190**678 
Desc:247HYDR260770074/tt 
Date:18/03/2026 
Avail Bal:NGN8,932.45 
Total:NGN8,932.45"""
            
            payload = {
                "sms_text": access_sms,
                "bank_type": "access"
            }
            
            response = requests.post(
                f"{self.base_url}/api/parse/sms",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    parsed_data = data.get('data', {})
                    self.log_result("SMS Parsing (Access Bank)", True, 
                                  f"Parsed amount: ₦{parsed_data.get('amount', 0)}")
                else:
                    self.log_result("SMS Parsing (Access Bank)", False, data.get('error', 'Unknown error'))
            else:
                self.log_result("SMS Parsing (Access Bank)", False, f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_result("SMS Parsing (Access Bank)", False, f"Request error: {str(e)}")
        
        # Test First Bank SMS
        try:
            first_bank_sms = """Debit: 2314XXXX455 Amt: NGN6,000.00 Date: 19-MAR-2026 14:55:21 Desc: POS TRAN-FLAT /XX/NG/1. Bal: NGN5,967.81CR. Dial *894*11# to get loan"""
            
            payload = {
                "sms_text": first_bank_sms,
                "bank_type": "first"
            }
            
            response = requests.post(
                f"{self.base_url}/api/parse/sms",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    parsed_data = data.get('data', {})
                    self.log_result("SMS Parsing (First Bank)", True, 
                                  f"Parsed amount: ₦{parsed_data.get('amount', 0)}")
                else:
                    self.log_result("SMS Parsing (First Bank)", False, data.get('error', 'Unknown error'))
            else:
                self.log_result("SMS Parsing (First Bank)", False, f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_result("SMS Parsing (First Bank)", False, f"Request error: {str(e)}")
        
        # Test GT Bank SMS
        try:
            gt_bank_sms = """Acct: ****728
Amt: NGN75,000.00 CR
Desc: -TRANSFER FROM ADISABABA GLOBAL CONCEPTS-OPAY-ADIS
Avail Bal: NGN104,657.26
Date: 2026-03-18 6:26:55 PM"""
            
            payload = {
                "sms_text": gt_bank_sms,
                "bank_type": "gt"
            }
            
            response = requests.post(
                f"{self.base_url}/api/parse/sms",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    parsed_data = data.get('data', {})
                    self.log_result("SMS Parsing (GT Bank)", True, 
                                  f"Parsed amount: ₦{parsed_data.get('amount', 0)}")
                else:
                    self.log_result("SMS Parsing (GT Bank)", False, data.get('error', 'Unknown error'))
            else:
                self.log_result("SMS Parsing (GT Bank)", False, f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_result("SMS Parsing (GT Bank)", False, f"Request error: {str(e)}")
    
    def test_csv_parsing(self):
        """Test CSV parsing endpoints"""
        # Test CSV text parsing
        try:
            csv_data = """Date,Description,Amount,Type,Category
2026-03-01,Salary March 2026,150000,Income,Income
2026-03-01,Uber Trip,5000,Debit,Transport
2026-03-02,KFC Ikeja,4500,Debit,Food"""
            
            response = requests.post(
                f"{self.base_url}/api/parse/csv/text",
                data={"csv_text": csv_data},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    parsed_data = data.get('data', {})
                    success_count = parsed_data.get('success_count', 0)
                    self.log_result("CSV Text Parsing", True, f"Parsed {success_count} transactions")
                else:
                    self.log_result("CSV Text Parsing", False, data.get('error', 'Unknown error'))
            else:
                self.log_result("CSV Text Parsing", False, f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_result("CSV Text Parsing", False, f"Request error: {str(e)}")
    
    def test_savings_plan(self):
        """Test savings plan creation"""
        try:
            payload = {
                "amount": 5000,
                "plan_type": "monthly",
                "user_profile": {
                    "income_level": "medium",
                    "age": 28
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/savings/plan",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    plan_data = data.get('data', {})
                    plan_id = plan_data.get('savings_plan', {}).get('plan_id', 'unknown')
                    self.log_result("Savings Plan Creation", True, f"Plan ID: {plan_id}")
                else:
                    self.log_result("Savings Plan Creation", False, data.get('error', 'Unknown error'))
            else:
                self.log_result("Savings Plan Creation", False, f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_result("Savings Plan Creation", False, f"Request error: {str(e)}")
    
    def test_savings_analysis(self):
        """Test savings analysis"""
        try:
            transactions = [
                {"amount": 5000, "type": "debit", "category": "Food", "description": "Restaurant"},
                {"amount": 15000, "type": "debit", "category": "Entertainment", "description": "Club"},
                {"amount": 8000, "type": "debit", "category": "Transport", "description": "Uber"}
            ]
            
            payload = {
                "transactions": transactions,
                "user_profile": {"income_level": "medium"}
            }
            
            response = requests.post(
                f"{self.base_url}/api/savings/analyze",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    analysis_data = data.get('data', {})
                    monthly_savings = analysis_data.get('potential_monthly_savings', 0)
                    self.log_result("Savings Analysis", True, f"Potential monthly savings: ₦{monthly_savings}")
                else:
                    self.log_result("Savings Analysis", False, data.get('error', 'Unknown error'))
            else:
                self.log_result("Savings Analysis", False, f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_result("Savings Analysis", False, f"Request error: {str(e)}")
    
    def test_bill_optimization(self):
        """Test bill optimization"""
        try:
            transactions = [
                {"amount": 5000, "type": "debit", "category": "Bills", "description": "DSTV Subscription"},
                {"amount": 12000, "type": "debit", "category": "Bills", "description": "Electricity Bill"}
            ]
            
            payload = {"transactions": transactions}
            
            response = requests.post(
                f"{self.base_url}/api/savings/bills/optimize",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    optimization_data = data.get('data', {})
                    strategies = optimization_data.get('optimization_strategies', [])
                    self.log_result("Bill Optimization", True, f"Found {len(strategies)} optimization strategies")
                else:
                    self.log_result("Bill Optimization", False, data.get('error', 'Unknown error'))
            else:
                self.log_result("Bill Optimization", False, f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_result("Bill Optimization", False, f"Request error: {str(e)}")
    
    def test_supported_banks(self):
        """Test supported banks endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/parse/banks", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    banks_data = data.get('data', {})
                    supported_banks = banks_data.get('supported_banks', [])
                    self.log_result("Supported Banks", True, f"Found {len(supported_banks)} supported banks")
                else:
                    self.log_result("Supported Banks", False, data.get('error', 'Unknown error'))
            else:
                self.log_result("Supported Banks", False, f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_result("Supported Banks", False, f"Request error: {str(e)}")
    
    def test_demo_data(self):
        """Test demo data endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/parse/demo", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    demo_data = data.get('data', {})
                    sample_sms = demo_data.get('sample_sms', [])
                    self.log_result("Demo Data", True, f"Found {len(sample_sms)} sample SMS messages")
                else:
                    self.log_result("Demo Data", False, data.get('error', 'Unknown error'))
            else:
                self.log_result("Demo Data", False, f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_result("Demo Data", False, f"Request error: {str(e)}")
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting FinSight AI Integration Tests")
        print("=" * 50)
        
        # Basic connectivity tests
        print("\n📡 Basic Connectivity Tests")
        print("-" * 30)
        self.test_health_endpoint()
        self.test_root_endpoint()
        
        # Parsing functionality tests
        print("\n📝 Parsing Functionality Tests")
        print("-" * 30)
        self.test_sms_parsing()
        self.test_csv_parsing()
        self.test_supported_banks()
        self.test_demo_data()
        
        # Savings functionality tests
        print("\n💰 Savings Functionality Tests")
        print("-" * 30)
        self.test_savings_plan()
        self.test_savings_analysis()
        self.test_bill_optimization()
        
        # Summary
        print("\n📊 Test Summary")
        print("=" * 50)
        
        passed = sum(1 for r in self.results if r['success'])
        failed = sum(1 for r in self.results if not r['success'])
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "success_rate": (passed/total*100),
            "results": self.results
        }


def main():
    """Main function to run integration tests"""
    tester = IntegrationTester()
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not running or not responding correctly")
            print("Please start the FastAPI server first:")
            print("  cd api && python main.py")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server")
        print("Please start the FastAPI server first:")
        print("  cd api && python main.py")
        return
    
    # Run all tests
    results = tester.run_all_tests()
    
    # Save results to file
    with open("integration_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Test results saved to: integration_test_results.json")
    
    # Return exit code based on results
    if results['failed'] > 0:
        print("\n❌ Some tests failed. Check the logs above.")
        exit(1)
    else:
        print("\n✅ All tests passed! Integration is working correctly.")
        exit(0)


if __name__ == "__main__":
    main()