#!/bin/bash

# Dashboard API Test Script
# This script tests the dashboard API endpoint

echo "🧪 Testing Dashboard API"
echo "========================"
echo ""

# Base URL
BASE_URL="http://localhost:8000/api/v1"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Login
echo "📝 Step 1: Login to get access token..."
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }')

# Extract token (requires jq - install with: apt-get install jq or brew install jq)
if command -v jq &> /dev/null; then
    TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.data.tokens.access')
    
    if [ "$TOKEN" != "null" ] && [ ! -z "$TOKEN" ]; then
        echo -e "${GREEN}✓ Login successful${NC}"
        echo "Token: ${TOKEN:0:20}..."
        echo ""
        
        # Step 2: Get Dashboard Stats
        echo "📊 Step 2: Fetching dashboard statistics..."
        STATS_RESPONSE=$(curl -s -X GET "${BASE_URL}/dashboard/stats/" \
          -H "Authorization: Bearer ${TOKEN}")
        
        echo ""
        echo "Response:"
        echo "--------"
        echo $STATS_RESPONSE | jq '.'
        echo ""
        
        # Check if successful
        if echo $STATS_RESPONSE | jq -e '.data' > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Dashboard API is working!${NC}"
            echo ""
            echo "📈 Statistics:"
            echo "-------------"
            echo "🏨 Hotels: $(echo $STATS_RESPONSE | jq -r '.data.hotels_count')"
            echo "📦 Packages: $(echo $STATS_RESPONSE | jq -r '.data.packages_count')"
            echo "✈️  Flight Enquiries: $(echo $STATS_RESPONSE | jq -r '.data.flight_enquiries_count')"
            echo "📧 General Enquiries: $(echo $STATS_RESPONSE | jq -r '.data.general_enquiries_count')"
            echo "⭐ Featured Hotels: $(echo $STATS_RESPONSE | jq -r '.data.featured_hotels_count')"
            echo "🔥 Trending Hotels: $(echo $STATS_RESPONSE | jq -r '.data.trending_hotels_count')"
        else
            echo -e "${RED}❌ Error fetching dashboard stats${NC}"
        fi
    else
        echo -e "${RED}❌ Login failed${NC}"
        echo "Response: $LOGIN_RESPONSE"
    fi
else
    echo -e "${YELLOW}⚠️  jq is not installed. Showing raw responses...${NC}"
    echo ""
    echo "Login Response:"
    echo "$LOGIN_RESPONSE"
    echo ""
    echo "Please install jq for better output formatting:"
    echo "  Ubuntu/Debian: sudo apt-get install jq"
    echo "  macOS: brew install jq"
    echo ""
    echo "Or manually extract the token and run:"
    echo "curl -X GET '${BASE_URL}/dashboard/stats/' \\"
    echo "  -H 'Authorization: Bearer YOUR_TOKEN'"
fi

echo ""
echo "========================"
echo "✅ Test complete"
