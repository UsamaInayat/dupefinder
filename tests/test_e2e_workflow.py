"""
End-to-End Workflow Testing for DupeFinder
Tests complete user journey from image upload to results display
"""

import requests
import time
import json
from pathlib import Path

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
TEST_IMAGES_DIR = Path(__file__).parent.parent / "data" / "products"

# ANSI color codes for better output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.tests = []
    
    def add_test(self, name, passed, message="", duration=0):
        self.tests.append({
            'name': name,
            'passed': passed,
            'message': message,
            'duration': duration
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def add_warning(self, message):
        self.warnings += 1
        print(f"{YELLOW}[WARNING]{RESET} {message}")
    
    def print_summary(self):
        print("\n" + "="*80)
        print(f"{BLUE}TEST SUMMARY{RESET}")
        print("="*80)
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"{GREEN}Passed: {self.passed}{RESET}")
        print(f"{RED}Failed: {self.failed}{RESET}")
        print(f"{YELLOW}Warnings: {self.warnings}{RESET}")
        print(f"Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        print("="*80)
        
        if self.failed > 0:
            print(f"\n{RED}FAILED TESTS:{RESET}")
            for test in self.tests:
                if not test['passed']:
                    print(f"  - {test['name']}: {test['message']}")

results = TestResults()

def test_backend_health():
    """Test 1: Backend Health Check"""
    print(f"\n{BLUE}[TEST 1]{RESET} Backend Health Check...")
    try:
        start = time.time()
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        duration = time.time() - start
        
        if response.status_code == 200:
            print(f"{GREEN}[PASS]{RESET} Backend is running (response time: {duration*1000:.0f}ms)")
            results.add_test("Backend Health", True, duration=duration)
            return True
        else:
            print(f"{RED}[FAIL]{RESET} Backend returned status {response.status_code}")
            results.add_test("Backend Health", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"{RED}[FAIL]{RESET} Backend not accessible: {e}")
        results.add_test("Backend Health", False, str(e))
        return False

def test_products_api():
    """Test 2: Products API Endpoint"""
    print(f"\n{BLUE}[TEST 2]{RESET} Products API Endpoint...")
    try:
        start = time.time()
        response = requests.get(f"{BACKEND_URL}/api/products", timeout=10)
        duration = time.time() - start
        
        if response.status_code == 200:
            products = response.json()
            count = len(products)
            print(f"{GREEN}[PASS]{RESET} Retrieved {count} products (response time: {duration*1000:.0f}ms)")
            
            if count < 50:
                results.add_warning(f"Product count is low: {count} (expected 50-100)")
            
            results.add_test("Products API", True, duration=duration)
            return True, count
        else:
            print(f"{RED}[FAIL]{RESET} Products API returned status {response.status_code}")
            results.add_test("Products API", False, f"Status code: {response.status_code}")
            return False, 0
    except Exception as e:
        print(f"{RED}[FAIL]{RESET} Products API error: {e}")
        results.add_test("Products API", False, str(e))
        return False, 0

def test_image_search():
    """Test 3: Image Search Functionality"""
    print(f"\n{BLUE}[TEST 3]{RESET} Image Search Functionality...")
    
    # Find a test image
    test_images = list(TEST_IMAGES_DIR.glob("**/*.jpg"))[:5]
    
    if not test_images:
        print(f"{RED}[FAIL]{RESET} No test images found in {TEST_IMAGES_DIR}")
        results.add_test("Image Search", False, "No test images available")
        return False
    
    passed_searches = 0
    total_time = 0
    
    for i, image_path in enumerate(test_images[:3], 1):  # Test 3 images
        print(f"\n  Testing image {i}/3: {image_path.name}")
        try:
            start = time.time()
            with open(image_path, 'rb') as f:
                files = {'file': (image_path.name, f, 'image/jpeg')}
                response = requests.post(
                    f"{BACKEND_URL}/api/search/similar",
                    files=files,
                    timeout=30
                )
            duration = time.time() - start
            total_time += duration
            
            if response.status_code == 200:
                data = response.json()
                similar_products = data.get('similar_products', [])
                query_image = data.get('query_image', {})
                
                print(f"  {GREEN}[PASS]{RESET} Found {len(similar_products)} similar products")
                print(f"  Response time: {duration:.2f}s")
                
                if duration > 10:
                    results.add_warning(f"Slow search response: {duration:.2f}s (target: <10s)")
                
                # Check result quality
                if similar_products:
                    top_result = similar_products[0]
                    print(f"  Top result: {top_result.get('name', 'N/A')} "
                          f"(similarity: {top_result.get('similarity_score', 0):.2%})")
                    
                    # Get category from query image path
                    query_category = image_path.parent.name
                    top_category = top_result.get('category', '')
                    
                    if query_category == top_category:
                        print(f"  {GREEN}[ACCURATE]{RESET} Category match: {query_category}")
                    else:
                        results.add_warning(f"Category mismatch: query={query_category}, result={top_category}")
                
                passed_searches += 1
            else:
                print(f"  {RED}[FAIL]{RESET} Search returned status {response.status_code}")
                
        except Exception as e:
            print(f"  {RED}[FAIL]{RESET} Search error: {e}")
    
    avg_time = total_time / 3
    success_rate = passed_searches / 3
    
    print(f"\n  Search Summary: {passed_searches}/3 successful (avg time: {avg_time:.2f}s)")
    
    if success_rate >= 0.66:
        results.add_test("Image Search", True, f"Success rate: {success_rate:.0%}", avg_time)
        return True
    else:
        results.add_test("Image Search", False, f"Low success rate: {success_rate:.0%}")
        return False

def test_admin_auth():
    """Test 4: Admin Authentication"""
    print(f"\n{BLUE}[TEST 4]{RESET} Admin Authentication...")
    try:
        start = time.time()
        response = requests.post(
            f"{BACKEND_URL}/api/admin/token",
            json={
                "email": "admin@dupefinder.com",
                "password": "admin123"
            },
            timeout=10
        )
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            if token:
                print(f"{GREEN}[PASS]{RESET} Admin login successful (response time: {duration*1000:.0f}ms)")
                results.add_test("Admin Auth", True, duration=duration)
                return True, token
            else:
                print(f"{RED}[FAIL]{RESET} No access token in response")
                results.add_test("Admin Auth", False, "No token returned")
                return False, None
        else:
            print(f"{RED}[FAIL]{RESET} Admin login failed with status {response.status_code}")
            results.add_test("Admin Auth", False, f"Status: {response.status_code}")
            return False, None
    except Exception as e:
        print(f"{RED}[FAIL]{RESET} Admin auth error: {e}")
        results.add_test("Admin Auth", False, str(e))
        return False, None

def test_admin_endpoints(token):
    """Test 5: Admin Protected Endpoints"""
    print(f"\n{BLUE}[TEST 5]{RESET} Admin Protected Endpoints...")
    
    if not token:
        print(f"{RED}[SKIP]{RESET} No admin token available")
        results.add_test("Admin Endpoints", False, "No token")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    endpoints_passed = 0
    total_endpoints = 3
    
    # Test 5.1: Get all users
    print("\n  Testing: GET /api/admin/users")
    try:
        response = requests.get(f"{BACKEND_URL}/api/admin/users", headers=headers, timeout=10)
        if response.status_code == 200:
            users = response.json()
            print(f"  {GREEN}[PASS]{RESET} Retrieved {len(users)} users")
            endpoints_passed += 1
        else:
            print(f"  {RED}[FAIL]{RESET} Status: {response.status_code}")
    except Exception as e:
        print(f"  {RED}[FAIL]{RESET} Error: {e}")
    
    # Test 5.2: Get all products
    print("\n  Testing: GET /api/admin/products")
    try:
        response = requests.get(f"{BACKEND_URL}/api/admin/products", headers=headers, timeout=10)
        if response.status_code == 200:
            products = response.json()
            print(f"  {GREEN}[PASS]{RESET} Retrieved {len(products)} products")
            endpoints_passed += 1
        else:
            print(f"  {RED}[FAIL]{RESET} Status: {response.status_code}")
    except Exception as e:
        print(f"  {RED}[FAIL]{RESET} Error: {e}")
    
    # Test 5.3: Get analytics
    print("\n  Testing: GET /api/admin/analytics")
    try:
        response = requests.get(f"{BACKEND_URL}/api/admin/analytics", headers=headers, timeout=10)
        if response.status_code == 200:
            analytics = response.json()
            print(f"  {GREEN}[PASS]{RESET} Retrieved analytics data")
            print(f"    - Total users: {analytics.get('total_users', 0)}")
            print(f"    - Total products: {analytics.get('total_products', 0)}")
            print(f"    - Total searches: {analytics.get('total_searches', 0)}")
            endpoints_passed += 1
        else:
            print(f"  {RED}[FAIL]{RESET} Status: {response.status_code}")
    except Exception as e:
        print(f"  {RED}[FAIL]{RESET} Error: {e}")
    
    success = endpoints_passed == total_endpoints
    results.add_test("Admin Endpoints", success, f"{endpoints_passed}/{total_endpoints} passed")
    return success

def run_all_tests():
    """Run all end-to-end tests"""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}DUPEFINDER - END-TO-END WORKFLOW TESTING{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Frontend URL: {FRONTEND_URL}")
    print(f"Test Images: {TEST_IMAGES_DIR}")
    
    # Run tests
    test_backend_health()
    test_products_api()
    test_image_search()
    auth_success, admin_token = test_admin_auth()
    if auth_success:
        test_admin_endpoints(admin_token)
    
    # Print summary
    results.print_summary()
    
    # Return exit code
    return 0 if results.failed == 0 else 1

if __name__ == "__main__":
    import sys
    exit_code = run_all_tests()
    sys.exit(exit_code)

