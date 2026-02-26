#!/usr/bin/env python
"""
Complete API Test Script for Club Luxora Travel Platform
Tests all endpoints with proper authentication
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    END = '\033[0m'

class APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.access_token = None
        self.refresh_token = None
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = []
        
    def print_header(self, text):
        print(f"\n{'='*60}")
        print(f"{Colors.BLUE}{text}{Colors.END}")
        print('='*60)
        
    def test_api(self, name, method, endpoint, data=None, headers=None, expect_success=True):
        """Test an API endpoint"""
        self.total_tests += 1
        url = f"{self.base_url}{endpoint}"
        
        print(f"\n{Colors.YELLOW}Test {self.total_tests}: {name}{Colors.END}")
        print(f"Method: {method} {endpoint}")
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers)
            elif method == "PATCH":
                response = requests.patch(url, json=data, headers=headers)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Print response
            try:
                response_data = response.json()
                print(f"Status Code: {response.status_code}")
                print(f"Response: {json.dumps(response_data, indent=2)}")
                
                # Check if test passed
                status_code = response_data.get('StatusCode', response_data.get('status'))
                if expect_success and (status_code == 6000 or response.status_code in [200, 201]):
                    print(f"{Colors.GREEN}✓ PASSED{Colors.END}")
                    self.passed_tests += 1
                    return response_data
                elif not expect_success and status_code == 6001:
                    print(f"{Colors.GREEN}✓ PASSED (Expected failure){Colors.END}")
                    self.passed_tests += 1
                    return response_data
                else:
                    print(f"{Colors.RED}✗ FAILED{Colors.END}")
                    self.failed_tests.append(name)
                    return response_data
                    
            except json.JSONDecodeError:
                print(f"Response: {response.text}")
                if response.status_code in [200, 201, 204]:
                    print(f"{Colors.GREEN}✓ PASSED{Colors.END}")
                    self.passed_tests += 1
                else:
                    print(f"{Colors.RED}✗ FAILED{Colors.END}")
                    self.failed_tests.append(name)
                return None
                
        except Exception as e:
            print(f"{Colors.RED}✗ ERROR: {str(e)}{Colors.END}")
            self.failed_tests.append(name)
            return None
    
    def get_auth_headers(self):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def run_all_tests(self):
        """Run all API tests"""
        
        # 1. AUTHENTICATION TESTS
        self.print_header("1. AUTHENTICATION TESTS")
        
        # 1.1 Login
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = self.test_api("Login", "POST", "/auth/login/", data=login_data)
        
        if response and response.get('StatusCode') == 6000:
            self.access_token = response['data']['tokens']['access']
            self.refresh_token = response['data']['tokens']['refresh']
            print(f"\n{Colors.GREEN}✓ Authentication successful{Colors.END}")
            print(f"Access Token: {self.access_token[:50]}...")
        else:
            print(f"\n{Colors.RED}✗ Authentication failed. Cannot continue tests.{Colors.END}")
            return
        
        # 1.2 Verify Token
        self.test_api("Verify Token", "POST", "/auth/verify/", 
                     headers=self.get_auth_headers())
        
        # 1.3 Refresh Token
        self.test_api("Refresh Token", "POST", "/auth/refresh/",
                     data={"refresh": self.refresh_token})
        
        # 2. HOTEL TESTS
        self.print_header("2. HOTEL TESTS")
        
        # 2.1 List Hotels (Public)
        self.test_api("List Hotels (Public)", "GET", "/hotels/")
        
        # 2.2 Create Hotel (Admin)
        hotel_data = {
            "name": "Test Paradise Resort",
            "slug": "test-paradise-resort",
            "location": "Maldives",
            "description": "Luxury resort with ocean views",
            "rating": 5,
            "price_per_night": 25000.00,
            "amenities": "WiFi,Pool,Spa,Restaurant,Beach Access",
            "has_wifi": True,
            "has_pool": True,
            "has_spa": True,
            "is_featured": True,
            "is_trending": True
        }
        hotel_response = self.test_api("Create Hotel", "POST", "/hotels/",
                                      data=hotel_data, headers=self.get_auth_headers())
        
        # Get hotel ID
        hotel_id = None
        if hotel_response and hotel_response.get('StatusCode') == 6000:
            hotel_id = hotel_response['data']['id']
        
        # 2.3 Get Hotel Details
        if hotel_id:
            self.test_api("Get Hotel Details", "GET", f"/hotels/{hotel_id}/")
            
            # 2.4 Update Hotel
            self.test_api("Update Hotel", "PATCH", f"/hotels/{hotel_id}/",
                         data={"is_premium": True}, headers=self.get_auth_headers())
        
        # 2.5 Featured Hotels
        self.test_api("Get Featured Hotels", "GET", "/hotels/featured/")
        
        # 2.6 Trending Hotels
        self.test_api("Get Trending Hotels", "GET", "/hotels/trending/")
        
        # 3. PACKAGE TESTS
        self.print_header("3. PACKAGE TESTS")
        
        # 3.1 List Packages
        self.test_api("List Packages", "GET", "/packages/")
        
        # 3.2 Create Package
        package_data = {
            "title": "Maldives Paradise Getaway",
            "slug": "maldives-paradise-getaway",
            "location": "Maldives",
            "description": "5-star luxury resort experience",
            "duration": "5 Days / 4 Nights",
            "group_size": "2-6 Pax",
            "price": 89999.00,
            "original_price": 110000.00,
            "rating": 4.9,
            "reviews_count": 234,
            "category": "international",
            "type": "international",
            "is_featured": True,
            "is_international": True,
            "inclusions": "Flights,Accommodation,Meals,Transfers",
            "highlights": "Beach Resort,Water Sports,Spa"
        }
        self.test_api("Create Package", "POST", "/packages/",
                     data=package_data, headers=self.get_auth_headers())
        
        # 3.3 Kerala Packages
        self.test_api("Get Kerala Packages", "GET", "/packages/kerala/")
        
        # 3.4 International Packages
        self.test_api("Get International Packages", "GET", "/packages/international/")
        
        # 3.5 Featured Packages
        self.test_api("Get Featured Packages", "GET", "/packages/featured/")
        
        # 4. HOUSEBOAT TESTS
        self.print_header("4. HOUSEBOAT TESTS")
        
        # 4.1 List Houseboats
        self.test_api("List Houseboats", "GET", "/houseboats/")
        
        # 4.2 Create Houseboat
        houseboat_data = {
            "name": "Premium Deluxe Houseboat",
            "slug": "premium-deluxe-houseboat",
            "type": "deluxe",
            "capacity": "4-6 Guests",
            "bedrooms": 2,
            "route": "Alleppey - Kumarakom",
            "duration": "1 Night / 2 Days",
            "price": 18000.00,
            "features": "AC Bedrooms,Sundeck,All Meals,Private Chef",
            "description": "Luxury houseboat experience",
            "is_featured": True
        }
        self.test_api("Create Houseboat", "POST", "/houseboats/",
                     data=houseboat_data, headers=self.get_auth_headers())
        
        # 5. CRUISE TESTS
        self.print_header("5. CRUISE TESTS")
        
        # 5.1 List Cruises
        self.test_api("List Cruises", "GET", "/cruises/")
        
        # 5.2 Create Cruise
        cruise_data = {
            "name": "Mediterranean Discovery",
            "slug": "mediterranean-discovery",
            "cruise_line": "Royal Cruise Lines",
            "route": "Italy - Greece - Turkey",
            "duration": "7 Nights",
            "departures": "April - October",
            "price": 145000.00,
            "highlights": "Barcelona,Rome,Athens,Santorini,Istanbul",
            "description": "Explore the Mediterranean",
            "is_featured": True
        }
        self.test_api("Create Cruise", "POST", "/cruises/",
                     data=cruise_data, headers=self.get_auth_headers())
        
        # 6. ISLAND STAY TESTS
        self.print_header("6. ISLAND STAY TESTS")
        
        # 6.1 List Island Stays
        self.test_api("List Island Stays", "GET", "/island-stays/")
        
        # 6.2 Create Island Stay
        island_data = {
            "name": "Maldives Paradise Resort",
            "slug": "maldives-paradise-resort",
            "location": "Maldives",
            "rating": 5,
            "price": 85000.00,
            "duration": "4 Nights",
            "features": "Overwater Villa,All-Inclusive,Water Sports,Spa,Private Beach",
            "description": "Luxury island resort",
            "is_featured": True
        }
        self.test_api("Create Island Stay", "POST", "/island-stays/",
                     data=island_data, headers=self.get_auth_headers())
        
        # 7. FLIGHT ENQUIRY TESTS
        self.print_header("7. FLIGHT ENQUIRY TESTS")
        
        # 7.1 Create Flight Enquiry (Public)
        tomorrow = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        return_date = (datetime.now() + timedelta(days=40)).strftime("%Y-%m-%d")
        
        flight_enquiry_data = {
            "trip_type": "roundtrip",
            "from_location": "Mumbai",
            "to_location": "Dubai",
            "departure_date": tomorrow,
            "return_date": return_date,
            "adults": 2,
            "children": 1,
            "travel_class": "economy",
            "name": "John Doe",
            "phone": "+919876543210",
            "email": "john@example.com"
        }
        self.test_api("Create Flight Enquiry", "POST", "/flight-enquiries/",
                     data=flight_enquiry_data)
        
        # 7.2 List Flight Enquiries (Admin)
        self.test_api("List Flight Enquiries", "GET", "/flight-enquiries/",
                     headers=self.get_auth_headers())
        
        # 7.3 Pending Flight Enquiries
        self.test_api("Get Pending Flight Enquiries", "GET", "/flight-enquiries/pending/",
                     headers=self.get_auth_headers())
        
        # 8. GENERAL ENQUIRY TESTS
        self.print_header("8. GENERAL ENQUIRY TESTS")
        
        # 8.1 Create Enquiry (Public)
        enquiry_data = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "+919876543210",
            "service": "packages-kerala",
            "destination": "Munnar",
            "travel_date": tomorrow,
            "travelers": "2",
            "message": "Looking for a Kerala honeymoon package with houseboat stay and hill station visit"
        }
        self.test_api("Create General Enquiry", "POST", "/enquiries/",
                     data=enquiry_data)
        
        # 8.2 List Enquiries (Admin)
        self.test_api("List Enquiries", "GET", "/enquiries/",
                     headers=self.get_auth_headers())
        
        # 8.3 Pending Enquiries
        self.test_api("Get Pending Enquiries", "GET", "/enquiries/pending/",
                     headers=self.get_auth_headers())
        
        # 8.4 Enquiries by Service
        self.test_api("Get Enquiries by Service", "GET", 
                     "/enquiries/by_service/?service=packages-kerala",
                     headers=self.get_auth_headers())
        
        # 9. USER TESTS
        self.print_header("9. USER TESTS")
        
        # 9.1 Get Current User
        self.test_api("Get Current User Profile", "GET", "/users/me/",
                     headers=self.get_auth_headers())
        
        # 10. SEARCH & FILTER TESTS
        self.print_header("10. SEARCH & FILTER TESTS")
        
        # 10.1 Search Hotels
        self.test_api("Search Hotels by Location", "GET", "/hotels/?search=maldives")
        
        # 10.2 Filter Packages by Category
        self.test_api("Filter Packages by Category", "GET", 
                     "/packages/?category=international")
        
        # 10.3 Filter Hotels by Rating
        self.test_api("Filter Hotels by Rating", "GET", "/hotels/?rating=5")
        
        # 10.4 Order Packages by Price
        self.test_api("Order Packages by Price", "GET", "/packages/?ordering=price")
        
        # 11. LOGOUT TEST
        self.print_header("11. LOGOUT TEST")
        
        # 11.1 Logout
        self.test_api("Logout", "POST", "/auth/logout/",
                     data={"refresh": self.refresh_token},
                     headers=self.get_auth_headers())
        
        # Print Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")
        print(f"\nTotal Tests: {self.total_tests}")
        print(f"{Colors.GREEN}Passed: {self.passed_tests}{Colors.END}")
        print(f"{Colors.RED}Failed: {len(self.failed_tests)}{Colors.END}")
        
        if self.failed_tests:
            print(f"\n{Colors.RED}Failed Tests:{Colors.END}")
            for test in self.failed_tests:
                print(f"  - {test}")
        
        if self.passed_tests == self.total_tests:
            print(f"\n{Colors.GREEN}✓ All tests passed!{Colors.END}\n")
        else:
            print(f"\n{Colors.RED}✗ Some tests failed{Colors.END}\n")

if __name__ == "__main__":
    print(f"\n{Colors.BLUE}{'='*60}")
    print("Club Luxora Travel Platform - API Tests")
    print(f"{'='*60}{Colors.END}\n")
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    tester = APITester()
    tester.run_all_tests()
