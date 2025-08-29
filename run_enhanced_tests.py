#!/usr/bin/env python3
"""
Enhanced Test Runner for Recent Changes

This script runs comprehensive tests for all the recent changes including:
- New escalation events API endpoints
- New notifications API endpoints
- Updated CRUD operations
- Frontend functionality improvements
- Event delegation
- Time display fixes
"""

import sys
import os
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(__file__))

class EnhancedTestRunner:
    """Enhanced test runner for recent changes."""
    
    def __init__(self):
        self.results = {
            "unit_tests": {"total": 0, "passed": 0, "failed": 0, "errors": []},
            "e2e_tests": {"total": 0, "passed": 0, "failed": 0, "errors": []},
            "frontend_tests": {"total": 0, "passed": 0, "failed": 0, "errors": []},
            "start_time": None,
            "end_time": None,
            "duration": None
        }
    
    def log_test_result(self, test_type: str, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} {details}")
        
        self.results[test_type]["total"] += 1
        if success:
            self.results[test_type]["passed"] += 1
        else:
            self.results[test_type]["failed"] += 1
            self.results[test_type]["errors"].append(f"{test_name}: {details}")
    
    def run_unit_tests(self):
        """Run unit tests for recent changes."""
        print("\n🧪 Running Unit Tests for Recent Changes...")
        print("=" * 60)
        
        test_files = [
            "tests/test_escalation_events_api.py",
            "tests/test_notifications_api.py", 
            "tests/test_updated_crud_operations.py",
            "tests/test_frontend_functionality.py"
        ]
        
        for test_file in test_files:
            if os.path.exists(test_file):
                try:
                    print(f"\n📋 Running {test_file}...")
                    result = subprocess.run(
                        [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
                        capture_output=True,
                        text=True,
                        cwd=os.path.dirname(__file__)
                    )
                    
                    if result.returncode == 0:
                        self.log_test_result("unit_tests", test_file, True, "All tests passed")
                    else:
                        self.log_test_result("unit_tests", test_file, False, f"Tests failed: {result.stderr}")
                        
                except Exception as e:
                    self.log_test_result("unit_tests", test_file, False, f"Error running tests: {e}")
            else:
                self.log_test_result("unit_tests", test_file, False, "Test file not found")
    
    def run_e2e_tests(self):
        """Run end-to-end tests."""
        print("\n🌐 Running End-to-End Tests...")
        print("=" * 60)
        
        try:
            print("📋 Running comprehensive E2E tests...")
            result = subprocess.run(
                [sys.executable, "run_e2e_tests.py"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(__file__)
            )
            
            if result.returncode == 0:
                self.log_test_result("e2e_tests", "Comprehensive E2E Tests", True, "All tests passed")
            else:
                self.log_test_result("e2e_tests", "Comprehensive E2E Tests", False, f"Tests failed: {result.stderr}")
                
        except Exception as e:
            self.log_test_result("e2e_tests", "Comprehensive E2E Tests", False, f"Error running tests: {e}")
    
    def run_frontend_tests(self):
        """Run frontend-specific tests."""
        print("\n🎨 Running Frontend Tests...")
        print("=" * 60)
        
        # Test frontend files exist
        frontend_files = [
            "app/frontend/index.html",
            "app/frontend/app.js"
        ]
        
        for file_path in frontend_files:
            if os.path.exists(file_path):
                self.log_test_result("frontend_tests", f"Frontend file: {file_path}", True, "File exists")
            else:
                self.log_test_result("frontend_tests", f"Frontend file: {file_path}", False, "File not found")
        
        # Test cache busting
        try:
            with open("app/frontend/index.html", "r") as f:
                html_content = f.read()
            
            if "app.js?v=" in html_content:
                self.log_test_result("frontend_tests", "Cache Busting", True, "Cache busting parameters present")
            else:
                self.log_test_result("frontend_tests", "Cache Busting", False, "Cache busting parameters missing")
                
        except Exception as e:
            self.log_test_result("frontend_tests", "Cache Busting", False, f"Error checking cache busting: {e}")
        
        # Test JavaScript functionality
        try:
            with open("app/frontend/app.js", "r") as f:
                js_content = f.read()
            
            required_functions = [
                "triggerEscalation",
                "getTimeAgo", 
                "loadEscalations",
                "loadNotifications",
                "trigger-escalation-btn",
                "acknowledge-btn",
                "resolve-btn",
                "snooze-btn"
            ]
            
            for func in required_functions:
                if func in js_content:
                    self.log_test_result("frontend_tests", f"JavaScript function: {func}", True, "Function present")
                else:
                    self.log_test_result("frontend_tests", f"JavaScript function: {func}", False, "Function missing")
                    
        except Exception as e:
            self.log_test_result("frontend_tests", "JavaScript Functions", False, f"Error checking JavaScript: {e}")
    
    def run_api_tests(self):
        """Run specific API tests for new endpoints."""
        print("\n🔌 Running API Tests for New Endpoints...")
        print("=" * 60)
        
        # Test escalation events API
        try:
            import requests
            
            # Test without authentication (should return 401)
            response = requests.get("http://localhost:8000/v1/escalation/events/")
            if response.status_code == 401:
                self.log_test_result("e2e_tests", "Escalation Events API Auth", True, "Authentication required")
            else:
                self.log_test_result("e2e_tests", "Escalation Events API Auth", False, f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_test_result("e2e_tests", "Escalation Events API Auth", False, f"Error testing API: {e}")
        
        # Test notifications API
        try:
            response = requests.get("http://localhost:8000/v1/notifications/")
            if response.status_code == 401:
                self.log_test_result("e2e_tests", "Notifications API Auth", True, "Authentication required")
            else:
                self.log_test_result("e2e_tests", "Notifications API Auth", False, f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_test_result("e2e_tests", "Notifications API Auth", False, f"Error testing API: {e}")
    
    def run_all_tests(self):
        """Run all enhanced tests."""
        print("🚀 Starting Enhanced Test Suite for Recent Changes...")
        print("=" * 80)
        
        self.results["start_time"] = time.time()
        
        # Run all test categories
        self.run_unit_tests()
        self.run_e2e_tests()
        self.run_frontend_tests()
        self.run_api_tests()
        
        self.results["end_time"] = time.time()
        self.results["duration"] = self.results["end_time"] - self.results["start_time"]
        
        self.print_summary()
        self.save_results()
    
    def print_summary(self):
        """Print comprehensive test summary."""
        print("\n" + "=" * 80)
        print("📊 ENHANCED TEST SUITE SUMMARY")
        print("=" * 80)
        
        total_tests = 0
        total_passed = 0
        total_failed = 0
        
        for test_type, results in self.results.items():
            if test_type in ["unit_tests", "e2e_tests", "frontend_tests"]:
                total_tests += results["total"]
                total_passed += results["passed"]
                total_failed += results["failed"]
                
                print(f"\n{test_type.upper().replace('_', ' ')}:")
                print(f"  Total: {results['total']}")
                print(f"  ✅ Passed: {results['passed']}")
                print(f"  ❌ Failed: {results['failed']}")
                
                if results["errors"]:
                    print(f"  🔍 Errors:")
                    for error in results["errors"][:5]:  # Show first 5 errors
                        print(f"    - {error}")
                    if len(results["errors"]) > 5:
                        print(f"    ... and {len(results['errors']) - 5} more errors")
        
        print(f"\n📈 OVERALL SUMMARY:")
        print(f"  Total Tests: {total_tests}")
        print(f"  ✅ Passed: {total_passed}")
        print(f"  ❌ Failed: {total_failed}")
        print(f"  ⏱️  Duration: {self.results['duration']:.2f} seconds")
        
        if total_tests > 0:
            success_rate = (total_passed / total_tests) * 100
            print(f"  📊 Success Rate: {success_rate:.1f}%")
            
            if success_rate == 100:
                print("🎉 All tests passed! Recent changes are working perfectly!")
            elif success_rate >= 90:
                print("✅ Excellent! Recent changes are working well with minor issues.")
            elif success_rate >= 75:
                print("⚠️  Good coverage. Some recent changes need attention.")
            else:
                print("🚨 Many tests failed. Recent changes have critical issues.")
    
    def save_results(self):
        """Save test results to file."""
        results_file = Path(__file__).parent / "enhanced_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {results_file}")


def main():
    """Main function."""
    runner = EnhancedTestRunner()
    runner.run_all_tests()
    
    # Return exit code based on test results
    total_failed = sum(
        results["failed"] for test_type, results in runner.results.items() 
        if test_type in ["unit_tests", "e2e_tests", "frontend_tests"]
    )
    
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
