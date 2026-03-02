#!/usr/bin/env python
"""
Test script for Dashboard Analytics API
"""
import os
import django
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_backend.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

def test_analytics_api():
    """Test the dashboard analytics API endpoint"""
    client = Client()
    
    # Create or get a test user
    username = "testadmin"
    password = "testpass123"
    
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': 'testadmin@example.com',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    if created:
        user.set_password(password)
        user.save()
        print(f"✅ Created test user: {username}")
    else:
        print(f"✅ Using existing user: {username}")
    
    # Login
    print("\n🔐 Logging in...")
    response = client.post('/api/v1/auth/login/', {
        'username': username,
        'password': password
    }, content_type='application/json')
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(response.json())
        return
    
    token = response.json()['data']['tokens']['access']
    print("✅ Login successful")
    
    # Test analytics endpoint
    print("\n📊 Testing Dashboard Analytics API...")
    response = client.get('/api/v1/dashboard/analytics/', 
                         HTTP_AUTHORIZATION=f'Bearer {token}')
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ API Response:")
        print(f"Message: {data['message']}")
        
        analytics = data['data']
        print(f"\n📈 Total Enquiries: {analytics['total_enquiries']}")
        
        print(f"\n📅 Monthly Analytics ({len(analytics['monthly_analytics'])} months):")
        for month in analytics['monthly_analytics'][:5]:  # Show first 5 months
            print(f"  - {month['month']}: {month['count']} enquiries")
        if len(analytics['monthly_analytics']) > 5:
            print(f"  ... and {len(analytics['monthly_analytics']) - 5} more months")
        
        print(f"\n🏆 Top Services ({len(analytics['top_services'])} services):")
        for i, service in enumerate(analytics['top_services'][:5], 1):  # Show top 5
            print(f"  {i}. {service['service_name']}: {service['count']} enquiries")
        if len(analytics['top_services']) > 5:
            print(f"  ... and {len(analytics['top_services']) - 5} more services")
        
        print(f"\n🕐 Recent Enquiries ({len(analytics['recent_enquiries'])} shown):")
        for enquiry in analytics['recent_enquiries']:
            print(f"  - {enquiry['auto_id']}: {enquiry['name']} ({enquiry['service_name']})")
            print(f"    Status: {enquiry['status']}, Date: {enquiry['date_added']}")
        
        print("\n✅ Dashboard Analytics API test completed successfully!")
    else:
        print(f"\n❌ API request failed")
        print(response.json())

if __name__ == '__main__':
    print("=" * 60)
    print("Dashboard Analytics API Test")
    print("=" * 60)
    test_analytics_api()
    print("\n" + "=" * 60)
