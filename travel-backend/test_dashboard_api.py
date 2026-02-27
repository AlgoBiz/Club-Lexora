#!/usr/bin/env python
"""
Test script for Dashboard API endpoint
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def test_dashboard_api():
    """Test the dashboard stats API endpoint"""
    
    # Create or get a test user
    user, created = User.objects.get_or_create(
        username='testadmin',
        defaults={
            'email': 'testadmin@example.com',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print("✓ Created test admin user")
    else:
        print("✓ Using existing test admin user")
    
    # Create API client
    client = APIClient()
    
    # Generate JWT token
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    
    # Set authentication header
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    
    # Test dashboard endpoint
    print("\n📊 Testing Dashboard Stats API...")
    response = client.get('/api/v1/dashboard/stats/')
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ Dashboard API is working!")
        print("\n📈 Dashboard Statistics:")
        print("-" * 50)
        
        data = response.json()
        
        if 'data' in data:
            stats = data['data']
            
            print(f"\n🏨 Hotels Count: {stats['hotels_count']}")
            print(f"📦 Packages Count: {stats['packages_count']}")
            print(f"✈️  Flight Enquiries Count: {stats['flight_enquiries_count']}")
            print(f"📧 General Enquiries Count: {stats['general_enquiries_count']}")
            print(f"⭐ Featured Hotels Count: {stats['featured_hotels_count']}")
            print(f"🔥 Trending Hotels Count: {stats['trending_hotels_count']}")
            
        print("\n" + "-" * 50)
        print("✅ All tests passed!")
    else:
        print(f"❌ Error: {response.json()}")
    
    return response.status_code == 200

if __name__ == '__main__':
    try:
        success = test_dashboard_api()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
