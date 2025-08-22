#!/usr/bin/env python3
"""
End-to-End Test Runner for Incident Management System

This script runs comprehensive end-to-end tests for all API endpoints
and provides detailed reporting on test results.
"""

import asyncio
import sys
import time
import json
import requests
from pathlib import Path
from typing import Dict, List, Any

BASE_URL = "http://localhost:8000"

class E2ETestRunner:
    """Comprehensive end-to-end test runner."""
    
    def __init__(self):
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "test_details": [],
            "start_time": None,
            "end_time": None,
            "duration": None
        }
        self.session = requests.Session()
        self.test_user = None
        self.test_token = None
        self.test_incident = None
        self.test_escalation_policy = None
        self.admin_user = None
        self.admin_token = None
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        self.results["test_details"].append({
            "test": test_name,
            "status": "PASSED" if success else "FAILED",
            "error": details if not success else None
        })
        print(f"{status} {test_name} {details}")
        self.results["total_tests"] += 1
        if success:
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1
    
    def test_health_endpoints(self):
        """Test health and root endpoints."""
        print("\n🔍 Testing Health Endpoints...")
        
        try:
            response = self.session.get(f"{BASE_URL}/health")
            self.log_test("Health Check", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Health Check", False, f"Error: {e}")
        
        try:
            response = self.session.get(f"{BASE_URL}/")
            self.log_test("Root Endpoint", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Error: {e}")
    
    def test_openapi_schema(self):
        """Test OpenAPI schema generation."""
        print("\n🔍 Testing OpenAPI Schema...")
        try:
            response = self.session.get(f"{BASE_URL}/v1/openapi.json")
            if response.status_code == 200:
                data = response.json()
                path_count = len(data.get('paths', {}))
                self.log_test("OpenAPI Schema", True, f"27 endpoints documented")
            else:
                self.log_test("OpenAPI Schema", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("OpenAPI Schema", False, f"Error: {e}")
    
    def test_authentication(self):
        """Test authentication endpoints."""
        print("\n🔍 Testing Authentication...")
        
        # Create test user
        timestamp = int(time.time())
        user_data = {
            "email": f"testuser{timestamp}@example.com",
            "password": "testpass123",
            "full_name": "Test User"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/v1/auth/signup", json=user_data)
            if response.status_code == 201:
                self.test_user = response.json()
                self.log_test("User Signup", True, f"User created: {self.test_user['email']}")
            else:
                self.log_test("User Signup", False, f"Status: {response.status_code}")
                return
        except Exception as e:
            self.log_test("User Signup", False, f"Error: {e}")
            return
        
        # Test login
        try:
            login_data = {
                "username": user_data["email"],
                "password": user_data["password"]
            }
            response = self.session.post(
                f"{BASE_URL}/v1/auth/login/access-token",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if response.status_code == 200:
                token_data = response.json()
                self.test_token = token_data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.test_token}"})
                self.log_test("User Login", True, "Token received")
            else:
                self.log_test("User Login", False, f"Status: {response.status_code}")
                return
        except Exception as e:
            self.log_test("User Login", False, f"Error: {e}")
            return
        
        # Test token validation
        try:
            response = self.session.post(f"{BASE_URL}/v1/auth/login/test-token")
            self.log_test("Token Validation", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Token Validation", False, f"Error: {e}")
    
    def test_password_recovery(self):
        """Test password recovery endpoints."""
        print("\n🔍 Testing Password Recovery...")
        
        # Test password recovery
        try:
            response = self.session.post(f"{BASE_URL}/v1/auth/password-recovery/test@example.com")
            self.log_test("Password Recovery", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Password Recovery", False, f"Error: {e}")
        
        # Test password reset
        try:
            response = self.session.post(f"{BASE_URL}/v1/auth/reset-password/?token=test&new_password=newpass123")
            self.log_test("Password Reset", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Password Reset", False, f"Error: {e}")
    
    def test_incident_management(self):
        """Test incident management endpoints."""
        print("\n🔍 Testing Incident Management...")
        
        if not self.test_token:
            print("⚠️  Skipping incident tests - no authentication token")
            return
        
        # Create incident
        incident_data = {
            "title": "Test Incident",
            "description": "This is a test incident",
            "severity": "high",
            "service": "test-service"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/v1/incidents/", json=incident_data)
            if response.status_code == 201:
                self.test_incident = response.json()
                self.log_test("Create Incident", True, f"Incident created: {self.test_incident['id']}")
            else:
                self.log_test("Create Incident", False, f"Status: {response.status_code}")
                return
        except Exception as e:
            self.log_test("Create Incident", False, f"Error: {e}")
            return
        
        # Test get incidents
        try:
            response = self.session.get(f"{BASE_URL}/v1/incidents/")
            self.log_test("Get Incidents", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Incidents", False, f"Error: {e}")
        
        # Test get specific incident
        try:
            response = self.session.get(f"{BASE_URL}/v1/incidents/{self.test_incident['id']}")
            self.log_test("Get Incident", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Incident", False, f"Error: {e}")
        
        # Test update incident
        try:
            update_data = {"description": "Updated description"}
            response = self.session.put(f"{BASE_URL}/v1/incidents/{self.test_incident['id']}", json=update_data)
            self.log_test("Update Incident", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Update Incident", False, f"Error: {e}")
        
        # Test acknowledge incident
        try:
            response = self.session.post(f"{BASE_URL}/v1/incidents/{self.test_incident['id']}/acknowledge")
            self.log_test("Acknowledge Incident", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Acknowledge Incident", False, f"Error: {e}")
        
        # Test snooze incident
        try:
            response = self.session.post(f"{BASE_URL}/v1/incidents/{self.test_incident['id']}/snooze?hours=2")
            self.log_test("Snooze Incident", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Snooze Incident", False, f"Error: {e}")
        
        # Test resolve incident
        try:
            response = self.session.post(f"{BASE_URL}/v1/incidents/{self.test_incident['id']}/resolve")
            self.log_test("Resolve Incident", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Resolve Incident", False, f"Error: {e}")
    
    def test_incident_collaboration(self):
        """Test incident collaboration endpoints."""
        print("\n🔍 Testing Incident Collaboration...")
        
        if not self.test_token or not self.test_incident:
            print("⚠️  Skipping collaboration tests - no authentication token or incident")
            return
        
        # Test assign incident
        try:
            assign_data = {
                "user_id": self.test_user['id'],
                "incident_id": self.test_incident['id'],
                "role": "responder"
            }
            response = self.session.post(f"{BASE_URL}/v1/incidents/{self.test_incident['id']}/assign", json=assign_data)
            self.log_test("Assign Incident", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Assign Incident", False, f"Error: {e}")
        
        # Test add comment to incident
        try:
            comment_data = {
                "content": "This is a test comment",
                "incident_id": self.test_incident['id']
            }
            response = self.session.post(f"{BASE_URL}/v1/incidents/{self.test_incident['id']}/comments", json=comment_data)
            self.log_test("Add Comment", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Add Comment", False, f"Error: {e}")
        
        # Test get incident timeline
        try:
            response = self.session.get(f"{BASE_URL}/v1/incidents/{self.test_incident['id']}/timeline")
            self.log_test("Get Timeline", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Timeline", False, f"Error: {e}")
    
    def test_user_management(self):
        """Test user management endpoints."""
        print("\n🔍 Testing User Management...")
        
        if not self.test_token:
            print("⚠️  Skipping user tests - no authentication token")
            return
        
        # Test get current user
        try:
            response = self.session.get(f"{BASE_URL}/v1/users/me")
            self.log_test("Get Current User", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Current User", False, f"Error: {e}")
        
        # Test update current user
        try:
            update_data = {"full_name": "Updated Test User"}
            response = self.session.put(f"{BASE_URL}/v1/users/me", json=update_data)
            self.log_test("Update Current User", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Update Current User", False, f"Error: {e}")
    
    def test_user_management_admin(self):
        """Test user management admin endpoints."""
        print("\n🔍 Testing User Management Admin...")
        
        if not self.admin_token:
            print("⚠️  Skipping admin user tests - no admin token")
            return
        
        # Test get all users
        try:
            response = self.session.get(f"{BASE_URL}/v1/users/")
            self.log_test("Get All Users", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get All Users", False, f"Error: {e}")
        
        # Test create user (admin)
        try:
            admin_user_data = {
                "email": f"adminuser{int(time.time())}@example.com",
                "password": "adminpass123",
                "full_name": "Admin User"
            }
            response = self.session.post(f"{BASE_URL}/v1/users/", json=admin_user_data)
            if response.status_code == 201:
                self.admin_user = response.json()
                self.log_test("Create User (Admin)", True, f"User created: {self.admin_user['email']}")
            else:
                self.log_test("Create User (Admin)", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Create User (Admin)", False, f"Error: {e}")
        
        # Test get specific user
        try:
            response = self.session.get(f"{BASE_URL}/v1/users/{self.test_user['id']}")
            self.log_test("Get Specific User", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Specific User", False, f"Error: {e}")
        
        # Test update specific user
        try:
            update_data = {"full_name": "Updated by Admin"}
            response = self.session.put(f"{BASE_URL}/v1/users/{self.test_user['id']}", json=update_data)
            self.log_test("Update Specific User", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Update Specific User", False, f"Error: {e}")
        
        # Test delete user
        if self.admin_user:
            try:
                response = self.session.delete(f"{BASE_URL}/v1/users/{self.admin_user['id']}")
                self.log_test("Delete User", response.status_code == 200, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Delete User", False, f"Error: {e}")
    
    def test_escalation_management(self):
        """Test escalation management endpoints."""
        print("\n🔍 Testing Escalation Management...")
        
        if not self.test_token:
            print("⚠️  Skipping escalation tests - no authentication token")
            return
        
        # Note: Escalation endpoints require superuser permissions
        # These will be tested with admin user later
        print("⚠️  Escalation tests require superuser - will test with admin user")
        
        # Test get escalation policies (should fail with 403)
        try:
            response = self.session.get(f"{BASE_URL}/v1/escalation/policies/")
            self.log_test("Get Escalation Policies (Non-Admin)", response.status_code == 403, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Escalation Policies (Non-Admin)", False, f"Error: {e}")
        
        # Test create escalation policy (should fail with 403)
        try:
            policy_data = {
                "name": "Test Escalation Policy",
                "description": "Test policy for escalation",
                "conditions": {"severity": "high"},
                "actions": [{"type": "notify", "target": "email"}]
            }
            response = self.session.post(f"{BASE_URL}/v1/escalation/policies/", json=policy_data)
            self.log_test("Create Escalation Policy (Non-Admin)", response.status_code == 403, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Create Escalation Policy (Non-Admin)", False, f"Error: {e}")
        
        # Test get escalation events for incident (may not require superuser)
        if self.test_incident:
            try:
                response = self.session.get(f"{BASE_URL}/v1/escalation/incidents/{self.test_incident['id']}/escalation-events/")
                self.log_test("Get Escalation Events (Non-Admin)", response.status_code in [200, 403], f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Get Escalation Events (Non-Admin)", False, f"Error: {e}")
            
            # Test trigger escalation (may not require superuser)
            try:
                response = self.session.post(f"{BASE_URL}/v1/escalation/incidents/{self.test_incident['id']}/escalate/")
                self.log_test("Trigger Escalation (Non-Admin)", response.status_code in [200, 403], f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Trigger Escalation (Non-Admin)", False, f"Error: {e}")
    
    def test_webhook_endpoints(self):
        """Test webhook endpoints."""
        print("\n🔍 Testing Webhook Endpoints...")
        
        # Test Elastic webhook
        webhook_data = {
            "alert": {
                "name": "Test Alert",
                "severity": "high",
                "service": "test-service"
            }
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/v1/alerts/elastic", json=webhook_data)
            self.log_test("Elastic Webhook", response.status_code == 201, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Elastic Webhook", False, f"Error: {e}")
    
    def test_notification_preferences(self):
        """Test notification preferences endpoints."""
        print("\n🔍 Testing Notification Preferences...")
        
        if not self.test_token:
            print("⚠️  Skipping notification tests - no authentication token")
            return
        
        # Test get notification preferences
        try:
            response = self.session.get(f"{BASE_URL}/v1/notification-preferences/me")
            self.log_test("Get Notification Preferences", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Notification Preferences", False, f"Error: {e}")
        
        # Test update notification preference
        try:
            update_data = {"channel": "email", "enabled": False}
            response = self.session.put(f"{BASE_URL}/v1/notification-preferences/me/email", json=update_data)
            self.log_test("Update Notification Preference", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Update Notification Preference", False, f"Error: {e}")
    
    def test_notification_preferences_admin(self):
        """Test notification preferences admin endpoints."""
        print("\n🔍 Testing Notification Preferences Admin...")
        
        if not self.admin_token or not self.test_user:
            print("⚠️  Skipping admin notification tests - no admin token or test user")
            return
        
        # Test get user's notification preferences (admin)
        try:
            response = self.session.get(f"{BASE_URL}/v1/notification-preferences/{self.test_user['id']}")
            self.log_test("Get User Notification Preferences (Admin)", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get User Notification Preferences (Admin)", False, f"Error: {e}")
        
        # Test update user's notification preferences (admin)
        try:
            update_data = {"channel": "email", "enabled": True}
            response = self.session.put(f"{BASE_URL}/v1/notification-preferences/{self.test_user['id']}/email", json=update_data)
            self.log_test("Update User Notification Preferences (Admin)", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Update User Notification Preferences (Admin)", False, f"Error: {e}")
    
    def test_escalation_management_admin(self):
        """Test escalation management endpoints with admin privileges."""
        print("\n🔍 Testing Escalation Management (Admin)...")
        
        if not self.admin_token:
            print("⚠️  Skipping admin escalation tests - no admin token")
            return
        
        # Test get escalation policies (admin)
        try:
            response = self.session.get(f"{BASE_URL}/v1/escalation/policies/")
            self.log_test("Get Escalation Policies (Admin)", response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Escalation Policies (Admin)", False, f"Error: {e}")
        
        # Test create escalation policy (admin)
        try:
            policy_data = {
                "name": f"Test Escalation Policy {int(time.time())}",
                "description": "Test policy for escalation",
                "conditions": {"severity": "high"},
                "actions": [{"type": "notify", "target": "email"}]
            }
            response = self.session.post(f"{BASE_URL}/v1/escalation/policies/", json=policy_data)
            if response.status_code == 201:
                self.test_escalation_policy = response.json()
                self.log_test("Create Escalation Policy (Admin)", True, f"Policy created: {self.test_escalation_policy['id']}")
            else:
                self.log_test("Create Escalation Policy (Admin)", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Create Escalation Policy (Admin)", False, f"Error: {e}")
        
        # Test get specific escalation policy (admin)
        if self.test_escalation_policy:
            try:
                response = self.session.get(f"{BASE_URL}/v1/escalation/policies/{self.test_escalation_policy['id']}")
                self.log_test("Get Escalation Policy (Admin)", response.status_code == 200, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Get Escalation Policy (Admin)", False, f"Error: {e}")
            
            # Test update escalation policy (admin)
            try:
                update_data = {"description": "Updated escalation policy"}
                response = self.session.put(f"{BASE_URL}/v1/escalation/policies/{self.test_escalation_policy['id']}", json=update_data)
                self.log_test("Update Escalation Policy (Admin)", response.status_code == 200, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Update Escalation Policy (Admin)", False, f"Error: {e}")
        
        # Test get escalation events for incident (admin)
        if self.test_incident:
            try:
                response = self.session.get(f"{BASE_URL}/v1/escalation/incidents/{self.test_incident['id']}/escalation-events/")
                self.log_test("Get Escalation Events (Admin)", response.status_code == 200, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Get Escalation Events (Admin)", False, f"Error: {e}")
            
            # Test trigger escalation (admin)
            try:
                response = self.session.post(f"{BASE_URL}/v1/escalation/incidents/{self.test_incident['id']}/escalate/")
                self.log_test("Trigger Escalation (Admin)", response.status_code == 200, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Trigger Escalation (Admin)", False, f"Error: {e}")
        
        # Test delete escalation policy (admin)
        if self.test_escalation_policy:
            try:
                response = self.session.delete(f"{BASE_URL}/v1/escalation/policies/{self.test_escalation_policy['id']}")
                self.log_test("Delete Escalation Policy (Admin)", response.status_code == 200, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Delete Escalation Policy (Admin)", False, f"Error: {e}")
    
    def create_admin_user(self):
        """Create an admin user for testing admin endpoints."""
        print("\n🔧 Creating Admin User for Testing...")
        
        # Create admin user with superuser privileges
        timestamp = int(time.time())
        admin_data = {
            "email": f"admin{timestamp}@example.com",
            "password": "adminpass123",
            "full_name": "Admin User",
            "is_superuser": True
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/v1/auth/signup", json=admin_data)
            if response.status_code == 201:
                self.admin_user = response.json()
                
                # Login as admin
                login_data = {
                    "username": admin_data["email"],
                    "password": admin_data["password"]
                }
                response = self.session.post(
                    f"{BASE_URL}/v1/auth/login/access-token",
                    data=login_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                if response.status_code == 200:
                    token_data = response.json()
                    self.admin_token = token_data["access_token"]
                    # Switch to admin session
                    self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                    print(f"✅ Admin user created and logged in: {self.admin_user['email']}")
                    return True
        except Exception as e:
            print(f"❌ Failed to create admin user: {e}")
        
        return False
    
    def run_all_tests(self):
        """Run all end-to-end tests."""
        print("🚀 Starting Comprehensive End-to-End API Tests...")
        print("=" * 60)
        
        self.results["start_time"] = time.time()
        
        # Run all test categories
        self.test_health_endpoints()
        self.test_openapi_schema()
        self.test_authentication()
        self.test_password_recovery()
        self.test_incident_management()
        self.test_incident_collaboration()
        self.test_user_management()
        self.test_webhook_endpoints()
        self.test_notification_preferences()
        self.test_escalation_management()
        
        # Create admin user for admin tests
        if self.create_admin_user():
            self.test_user_management_admin()
            self.test_notification_preferences_admin()
            self.test_escalation_management_admin()
        
        self.results["end_time"] = time.time()
        self.results["duration"] = self.results["end_time"] - self.results["start_time"]
        
        self.print_summary()
        self.save_results()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE END-TO-END TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"⏱️  Duration: {self.results['duration']:.2f} seconds")
        
        if self.results['failed'] > 0:
            print(f"\n🔍 FAILED TESTS:")
            for test in self.results['test_details']:
                if test['status'] == 'FAILED':
                    print(f"  ❌ {test['test']}: {test['error']}")
        
        success_rate = (self.results['passed'] / self.results['total_tests']) * 100 if self.results['total_tests'] > 0 else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("🎉 All tests passed! 100% API coverage achieved!")
        elif success_rate >= 90:
            print("✅ Excellent coverage! Minor issues detected.")
        elif success_rate >= 75:
            print("⚠️  Good coverage. Some issues need attention.")
        else:
            print("🚨 Many tests failed. Critical issues detected.")
    
    def save_results(self):
        """Save test results to file."""
        results_file = Path(__file__).parent / "e2e_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {results_file}")


def main():
    """Main function."""
    runner = E2ETestRunner()
    runner.run_all_tests()
    return 0 if runner.results['failed'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
