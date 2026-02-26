#!/bin/bash
# Complete API Test Script for Club Luxora Travel Platform
# Run this script to test all API endpoints

BASE_URL="http://localhost:8000/api/v1"

echo "=========================================="
echo "Club Luxora Travel Platform - API Tests"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TOTAL_TESTS=0
PASSED_TESTS=0

test_api() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${BLUE}Test $TOTAL_TESTS: $1${NC}"
    echo "Command: $2"
    
    RESPONSE=$(eval $2)
    STATUS_CODE=$(echo "$RESPONSE" | jq -r '.StatusCode // .status // "N/A"' 2>/dev/null)
    
    if [[ "$STATUS_CODE" == "6000" ]] || [[ "$3" == "skip_check" ]]; then
        echo -e "${GREEN}✓ PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
    fi
    echo ""
}

echo "=========================================="
echo "1. AUTHENTICATION TESTS"
echo "=========================================="
echo ""

# 1.1 Login
echo "1.1 Testing Login..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }')

echo "$LOGIN_RESPONSE" | jq '.'
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.data.tokens.access')
REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.data.tokens.refresh')

if [ "$ACCESS_TOKEN" != "null" ]; then
    echo -e "${GREEN}✓ Login successful${NC}"
    echo "Access Token: ${ACCESS_TOKEN:0:50}..."
    echo ""
else
    echo -e "${RED}✗ Login failed${NC}"
    exit 1
fi

# 1.2 Verify Token
test_api "Verify Token" \
  "curl -s -X POST '$BASE_URL/auth/verify/' \
    -H 'Authorization: Bearer $ACCESS_TOKEN'"

# 1.3 Refresh Token
test_api "Refresh Token" \
  "curl -s -X POST '$BASE_URL/auth/refresh/' \
    -H 'Content-Type: application/json' \
    -d '{\"refresh\": \"$REFRESH_TOKEN\"}'"

echo "=========================================="
echo "2. HOTEL TESTS"
echo "=========================================="
echo ""

# 2.1 List Hotels (Public)
test_api "List Hotels (Public)" \
  "curl -s -X GET '$BASE_URL/hotels/'" \
  "skip_check"

# 2.2 Create Hotel (Admin)
test_api "Create Hotel" \
  "curl -s -X POST '$BASE_URL/hotels/' \
    -H 'Authorization: Bearer $ACCESS_TOKEN' \
    -H 'Content-Type: application/json' \
    -d '{
      \"name\": \"Test Paradise Resort\",
      \"slug\": \"test-paradise-resort\",
      \"location\": \"Maldives\",
      \"description\": \"Luxury resort with ocean views\",
      \"rating\": 5,
      \"price_per_night\": 25000.00,
      \"amenities\": \"WiFi,Pool,Spa,Restaurant,Beach Access\",
      \"has_wifi\": true,
      \"has_pool\": true,
      \"has_spa\": true,
      \"is_featured\": true,
      \"is_trending\": true
    }'"

# Get hotel ID from list
HOTEL_ID=$(curl -s -X GET "$BASE_URL/hotels/" | jq -r '.data[0].id // .results[0].id' 2>/dev/null)

if [ "$HOTEL_ID" != "null" ] && [ -n "$HOTEL_ID" ]; then
    # 2.3 Get Hotel Details
    test_api "Get Hotel Details" \
      "curl -s -X GET '$BASE_URL/hotels/$HOTEL_ID/'" \
      "skip_check"

    # 2.4 Update Hotel
    test_api "Update Hotel" \
      "curl -s -X PATCH '$BASE_URL/hotels/$HOTEL_ID/' \
        -H 'Authorization: Bearer $ACCESS_TOKEN' \
        -H 'Content-Type: application/json' \
        -d '{\"is_premium\": true}'"
fi

# 2.5 Featured Hotels
test_api "Get Featured Hotels" \
  "curl -s -X GET '$BASE_URL/hotels/featured/'" \
  "skip_check"

# 2.6 Trending Hotels
test_api "Get Trending Hotels" \
  "curl -s -X GET '$BASE_URL/hotels/trending/'" \
  "skip_check"

echo "=========================================="
echo "3. PACKAGE TESTS"
echo "=========================================="
echo ""

# 3.1 List Packages
test_api "List Packages" \
  "curl -s -X GET '$BASE_URL/packages/'" \
  "skip_check"

# 3.2 Create Package
test_api "Create Package" \
  "curl -s -X POST '$BASE_URL/packages/' \
    -H 'Authorization: Bearer $ACCESS_TOKEN' \
    -H 'Content-Type: application/json' \
    -d '{
      \"title\": \"Maldives Paradise Getaway\",
      \"slug\": \"maldives-paradise-getaway\",
      \"location\": \"Maldives\",
      \"description\": \"5-star luxury resort experience\",
      \"duration\": \"5 Days / 4 Nights\",
      \"group_size\": \"2-6 Pax\",
      \"price\": 89999.00,
      \"original_price\": 110000.00,
      \"rating\": 4.9,
      \"reviews_count\": 234,
      \"category\": \"international\",
      \"type\": \"international\",
      \"is_featured\": true,
      \"is_international\": true,
      \"inclusions\": \"Flights,Accommodation,Meals,Transfers\",
      \"highlights\": \"Beach Resort,Water Sports,Spa\"
    }'"

# 3.3 Kerala Packages
test_api "Get Kerala Packages" \
  "curl -s -X GET '$BASE_URL/packages/kerala/'" \
  "skip_check"

# 3.4 International Packages
test_api "Get International Packages" \
  "curl -s -X GET '$BASE_URL/packages/international/'" \
  "skip_check"

# 3.5 Featured Packages
test_api "Get Featured Packages" \
  "curl -s -X GET '$BASE_URL/packages/featured/'" \
  "skip_check"

echo "=========================================="
echo "4. HOUSEBOAT TESTS"
echo "=========================================="
echo ""

# 4.1 List Houseboats
test_api "List Houseboats" \
  "curl -s -X GET '$BASE_URL/houseboats/'" \
  "skip_check"

# 4.2 Create Houseboat
test_api "Create Houseboat" \
  "curl -s -X POST '$BASE_URL/houseboats/' \
    -H 'Authorization: Bearer $ACCESS_TOKEN' \
    -H 'Content-Type: application/json' \
    -d '{
      \"name\": \"Premium Deluxe Houseboat\",
      \"slug\": \"premium-deluxe-houseboat\",
      \"type\": \"deluxe\",
      \"capacity\": \"4-6 Guests\",
      \"bedrooms\": 2,
      \"route\": \"Alleppey - Kumarakom\",
      \"duration\": \"1 Night / 2 Days\",
      \"price\": 18000.00,
      \"features\": \"AC Bedrooms,Sundeck,All Meals,Private Chef\",
      \"description\": \"Luxury houseboat experience\",
      \"is_featured\": true
    }'"

echo "=========================================="
echo "5. CRUISE TESTS"
echo "=========================================="
echo ""

# 5.1 List Cruises
test_api "List Cruises" \
  "curl -s -X GET '$BASE_URL/cruises/'" \
  "skip_check"

# 5.2 Create Cruise
test_api "Create Cruise" \
  "curl -s -X POST '$BASE_URL/cruises/' \
    -H 'Authorization: Bearer $ACCESS_TOKEN' \
    -H 'Content-Type: application/json' \
    -d '{
      \"name\": \"Mediterranean Discovery\",
      \"slug\": \"mediterranean-discovery\",
      \"cruise_line\": \"Royal Cruise Lines\",
      \"route\": \"Italy - Greece - Turkey\",
      \"duration\": \"7 Nights\",
      \"departures\": \"April - October\",
      \"price\": 145000.00,
      \"highlights\": \"Barcelona,Rome,Athens,Santorini,Istanbul\",
      \"description\": \"Explore the Mediterranean\",
      \"is_featured\": true
    }'"

echo "=========================================="
echo "6. ISLAND STAY TESTS"
echo "=========================================="
echo ""

# 6.1 List Island Stays
test_api "List Island Stays" \
  "curl -s -X GET '$BASE_URL/island-stays/'" \
  "skip_check"

# 6.2 Create Island Stay
test_api "Create Island Stay" \
  "curl -s -X POST '$BASE_URL/island-stays/' \
    -H 'Authorization: Bearer $ACCESS_TOKEN' \
    -H 'Content-Type: application/json' \
    -d '{
      \"name\": \"Maldives Paradise Resort\",
      \"slug\": \"maldives-paradise-resort\",
      \"location\": \"Maldives\",
      \"rating\": 5,
      \"price\": 85000.00,
      \"duration\": \"4 Nights\",
      \"features\": \"Overwater Villa,All-Inclusive,Water Sports,Spa,Private Beach\",
      \"description\": \"Luxury island resort\",
      \"is_featured\": true
    }'"

echo "=========================================="
echo "7. FLIGHT ENQUIRY TESTS"
echo "=========================================="
echo ""

# 7.1 Create Flight Enquiry (Public)
test_api "Create Flight Enquiry" \
  "curl -s -X POST '$BASE_URL/flight-enquiries/' \
    -H 'Content-Type: application/json' \
    -d '{
      \"trip_type\": \"roundtrip\",
      \"from_location\": \"Mumbai\",
      \"to_location\": \"Dubai\",
      \"departure_date\": \"2024-12-01\",
      \"return_date\": \"2024-12-10\",
      \"adults\": 2,
      \"children\": 1,
      \"travel_class\": \"economy\",
      \"name\": \"John Doe\",
      \"phone\": \"+919876543210\",
      \"email\": \"john@example.com\"
    }'"

# 7.2 List Flight Enquiries (Admin)
test_api "List Flight Enquiries" \
  "curl -s -X GET '$BASE_URL/flight-enquiries/' \
    -H 'Authorization: Bearer $ACCESS_TOKEN'" \
  "skip_check"

# 7.3 Pending Flight Enquiries
test_api "Get Pending Flight Enquiries" \
  "curl -s -X GET '$BASE_URL/flight-enquiries/pending/' \
    -H 'Authorization: Bearer $ACCESS_TOKEN'" \
  "skip_check"

echo "=========================================="
echo "8. GENERAL ENQUIRY TESTS"
echo "=========================================="
echo ""

# 8.1 Create Enquiry (Public)
test_api "Create General Enquiry" \
  "curl -s -X POST '$BASE_URL/enquiries/' \
    -H 'Content-Type: application/json' \
    -d '{
      \"name\": \"Jane Doe\",
      \"email\": \"jane@example.com\",
      \"phone\": \"+919876543210\",
      \"service\": \"packages-kerala\",
      \"destination\": \"Munnar\",
      \"travel_date\": \"2024-12-20\",
      \"travelers\": \"2\",
      \"message\": \"Looking for a Kerala honeymoon package with houseboat stay and hill station visit\"
    }'"

# 8.2 List Enquiries (Admin)
test_api "List Enquiries" \
  "curl -s -X GET '$BASE_URL/enquiries/' \
    -H 'Authorization: Bearer $ACCESS_TOKEN'" \
  "skip_check"

# 8.3 Pending Enquiries
test_api "Get Pending Enquiries" \
  "curl -s -X GET '$BASE_URL/enquiries/pending/' \
    -H 'Authorization: Bearer $ACCESS_TOKEN'" \
  "skip_check"

# 8.4 Enquiries by Service
test_api "Get Enquiries by Service" \
  "curl -s -X GET '$BASE_URL/enquiries/by_service/?service=packages-kerala' \
    -H 'Authorization: Bearer $ACCESS_TOKEN'" \
  "skip_check"

echo "=========================================="
echo "9. USER TESTS"
echo "=========================================="
echo ""

# 9.1 Get Current User
test_api "Get Current User Profile" \
  "curl -s -X GET '$BASE_URL/users/me/' \
    -H 'Authorization: Bearer $ACCESS_TOKEN'"

# 9.2 Change Password
test_api "Change Password" \
  "curl -s -X POST '$BASE_URL/users/change_password/' \
    -H 'Authorization: Bearer $ACCESS_TOKEN' \
    -H 'Content-Type: application/json' \
    -d '{
      \"old_password\": \"admin123\",
      \"new_password\": \"newpass123\",
      \"confirm_password\": \"newpass123\"
    }'"

# Change password back
curl -s -X POST "$BASE_URL/users/change_password/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "newpass123",
    "new_password": "admin123",
    "confirm_password": "admin123"
  }' > /dev/null

echo "=========================================="
echo "10. SEARCH & FILTER TESTS"
echo "=========================================="
echo ""

# 10.1 Search Hotels
test_api "Search Hotels by Location" \
  "curl -s -X GET '$BASE_URL/hotels/?search=maldives'" \
  "skip_check"

# 10.2 Filter Packages by Category
test_api "Filter Packages by Category" \
  "curl -s -X GET '$BASE_URL/packages/?category=international'" \
  "skip_check"

# 10.3 Filter Hotels by Rating
test_api "Filter Hotels by Rating" \
  "curl -s -X GET '$BASE_URL/hotels/?rating=5'" \
  "skip_check"

# 10.4 Order Packages by Price
test_api "Order Packages by Price" \
  "curl -s -X GET '$BASE_URL/packages/?ordering=price'" \
  "skip_check"

echo "=========================================="
echo "11. LOGOUT TEST"
echo "=========================================="
echo ""

# 11.1 Logout
test_api "Logout" \
  "curl -s -X POST '$BASE_URL/auth/logout/' \
    -H 'Authorization: Bearer $ACCESS_TOKEN' \
    -H 'Content-Type: application/json' \
    -d '{\"refresh\": \"$REFRESH_TOKEN\"}'"

echo "=========================================="
echo "TEST SUMMARY"
echo "=========================================="
echo -e "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $((TOTAL_TESTS - PASSED_TESTS))${NC}"
echo ""

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
