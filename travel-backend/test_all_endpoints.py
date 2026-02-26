#!/usr/bin/env python
"""
Comprehensive API Endpoint Tester
Tests all registered API endpoints to verify they're working
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.test')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.user_account.models import (
    Hotel, Package, Houseboat, Cruise, IslandStay,
    FlightEnquiry, Enquiry
)

User = get_user_model()

def test_all_endpoints():
    """Test all API endpoints"""
    client = APIClient()
    
    # Create test users
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@test.com',
        password='admin123'
    )
    
    user = User.objects.create_user(
        username='testuser',
        email='user@test.com',
        password='user123'
    )
    
    print("=" * 60)
    print("TESTING ALL API ENDPOINTS")
    print("=" * 60)
    
    results = {
        'passed': [],
        'failed': []
    }
    
    # Test Authentication Endpoints
    print("\n📝 AUTHENTICATION ENDPOINTS")
    print("-" * 60)
    
    endpoints = [
        ('POST', '/api/v1/auth/login/', {'username': 'testuser', 'password': 'user123'}, None, 'Login'),
        ('POST', '/api/v1/auth/verify/', {}, user, 'Verify Token'),
    ]
    
    for method, url, data, auth_user, name in endpoints:
        if auth_user:
            client.force_authenticate(user=auth_user)
        else:
            client.force_authenticate(user=None)
            
        try:
            if method == 'GET':
                response = client.get(url)
            elif method == 'POST':
                response = client.post(url, data)
            
            status = '✅' if response.status_code in [200, 201] else '❌'
            print(f"{status} {method:6} {url:40} [{response.status_code}] {name}")
            
            if response.status_code in [200, 201]:
                results['passed'].append(name)
            else:
                results['failed'].append(f"{name} ({response.status_code})")
        except Exception as e:
            print(f"❌ {method:6} {url:40} [ERROR] {name}: {str(e)}")
            results['failed'].append(f"{name} (Exception)")
    
    # Create test data
    hotel = Hotel.objects.create(
        name='Test Hotel',
        slug='test-hotel',
        location='Mumbai',
        rating=5,
        price_per_night=5000.00
    )
    
    package = Package.objects.create(
        title='Test Package',
        slug='test-package',
        location='Kerala',
        duration='5 Days',
        price=50000.00,
        category='kerala',
        type='kerala',
        is_kerala=True
    )
    
    houseboat = Houseboat.objects.create(
        name='Test Houseboat',
        slug='test-houseboat',
        type='deluxe',
        capacity=4,
        bedrooms=2,
        route='Alleppey',
        duration='1 Day',
        price=15000.00
    )
    
    cruise = Cruise.objects.create(
        name='Test Cruise',
        slug='test-cruise',
        cruise_line='Test Line',
        route='Mumbai-Goa',
        duration='3 Days',
        price=25000.00
    )
    
    island_stay = IslandStay.objects.create(
        name='Test Island',
        slug='test-island',
        location='Maldives',
        rating=5,
        price=80000.00,
        duration='4 Days'
    )
    
    # Test Hotel Endpoints
    print("\n🏨 HOTEL ENDPOINTS")
    print("-" * 60)
    
    endpoints = [
        ('GET', '/api/v1/hotels/', {}, None, 'List Hotels'),
        ('GET', f'/api/v1/hotels/{hotel.id}/', {}, None, 'Get Hotel Detail'),
        ('GET', '/api/v1/hotels/featured/', {}, None, 'Featured Hotels'),
        ('GET', '/api/v1/hotels/trending/', {}, None, 'Trending Hotels'),
        ('POST', '/api/v1/hotels/', {'name': 'New Hotel', 'slug': 'new-hotel', 'location': 'Delhi', 'rating': 4, 'price_per_night': 3000}, admin, 'Create Hotel'),
    ]
    
    for method, url, data, auth_user, name in endpoints:
        if auth_user:
            client.force_authenticate(user=auth_user)
        else:
            client.force_authenticate(user=None)
            
        try:
            if method == 'GET':
                response = client.get(url)
            elif method == 'POST':
                response = client.post(url, data)
            
            status = '✅' if response.status_code in [200, 201] else '❌'
            print(f"{status} {method:6} {url:40} [{response.status_code}] {name}")
            
            if response.status_code in [200, 201]:
                results['passed'].append(name)
            else:
                results['failed'].append(f"{name} ({response.status_code})")
        except Exception as e:
            print(f"❌ {method:6} {url:40} [ERROR] {name}: {str(e)}")
            results['failed'].append(f"{name} (Exception)")
    
    # Test Package Endpoints
    print("\n📦 PACKAGE ENDPOINTS")
    print("-" * 60)
    
    endpoints = [
        ('GET', '/api/v1/packages/', {}, None, 'List Packages'),
        ('GET', f'/api/v1/packages/{package.id}/', {}, None, 'Get Package Detail'),
        ('GET', '/api/v1/packages/featured/', {}, None, 'Featured Packages'),
        ('GET', '/api/v1/packages/trending/', {}, None, 'Trending Packages'),
        ('GET', '/api/v1/packages/kerala/', {}, None, 'Kerala Packages'),
        ('GET', '/api/v1/packages/international/', {}, None, 'International Packages'),
    ]
    
    for method, url, data, auth_user, name in endpoints:
        if auth_user:
            client.force_authenticate(user=auth_user)
        else:
            client.force_authenticate(user=None)
            
        try:
            response = client.get(url)
            status = '✅' if response.status_code == 200 else '❌'
            print(f"{status} {method:6} {url:40} [{response.status_code}] {name}")
            
            if response.status_code == 200:
                results['passed'].append(name)
            else:
                results['failed'].append(f"{name} ({response.status_code})")
        except Exception as e:
            print(f"❌ {method:6} {url:40} [ERROR] {name}: {str(e)}")
            results['failed'].append(f"{name} (Exception)")
    
    # Test Houseboat Endpoints
    print("\n🚤 HOUSEBOAT ENDPOINTS")
    print("-" * 60)
    
    endpoints = [
        ('GET', '/api/v1/houseboats/', {}, None, 'List Houseboats'),
        ('GET', f'/api/v1/houseboats/{houseboat.id}/', {}, None, 'Get Houseboat Detail'),
        ('GET', '/api/v1/houseboats/featured/', {}, None, 'Featured Houseboats'),
        ('GET', '/api/v1/houseboats/trending/', {}, None, 'Trending Houseboats'),
    ]
    
    for method, url, data, auth_user, name in endpoints:
        try:
            response = client.get(url)
            status = '✅' if response.status_code == 200 else '❌'
            print(f"{status} {method:6} {url:40} [{response.status_code}] {name}")
            
            if response.status_code == 200:
                results['passed'].append(name)
            else:
                results['failed'].append(f"{name} ({response.status_code})")
        except Exception as e:
            print(f"❌ {method:6} {url:40} [ERROR] {name}: {str(e)}")
            results['failed'].append(f"{name} (Exception)")
    
    # Test Cruise Endpoints
    print("\n🚢 CRUISE ENDPOINTS")
    print("-" * 60)
    
    endpoints = [
        ('GET', '/api/v1/cruises/', {}, None, 'List Cruises'),
        ('GET', f'/api/v1/cruises/{cruise.id}/', {}, None, 'Get Cruise Detail'),
        ('GET', '/api/v1/cruises/featured/', {}, None, 'Featured Cruises'),
        ('GET', '/api/v1/cruises/trending/', {}, None, 'Trending Cruises'),
    ]
    
    for method, url, data, auth_user, name in endpoints:
        try:
            response = client.get(url)
            status = '✅' if response.status_code == 200 else '❌'
            print(f"{status} {method:6} {url:40} [{response.status_code}] {name}")
            
            if response.status_code == 200:
                results['passed'].append(name)
            else:
                results['failed'].append(f"{name} ({response.status_code})")
        except Exception as e:
            print(f"❌ {method:6} {url:40} [ERROR] {name}: {str(e)}")
            results['failed'].append(f"{name} (Exception)")
    
    # Test Island Stay Endpoints
    print("\n🏝️  ISLAND STAY ENDPOINTS")
    print("-" * 60)
    
    endpoints = [
        ('GET', '/api/v1/island-stays/', {}, None, 'List Island Stays'),
        ('GET', f'/api/v1/island-stays/{island_stay.id}/', {}, None, 'Get Island Stay Detail'),
        ('GET', '/api/v1/island-stays/featured/', {}, None, 'Featured Island Stays'),
        ('GET', '/api/v1/island-stays/trending/', {}, None, 'Trending Island Stays'),
    ]
    
    for method, url, data, auth_user, name in endpoints:
        try:
            response = client.get(url)
            status = '✅' if response.status_code == 200 else '❌'
            print(f"{status} {method:6} {url:40} [{response.status_code}] {name}")
            
            if response.status_code == 200:
                results['passed'].append(name)
            else:
                results['failed'].append(f"{name} ({response.status_code})")
        except Exception as e:
            print(f"❌ {method:6} {url:40} [ERROR] {name}: {str(e)}")
            results['failed'].append(f"{name} (Exception)")
    
    # Test Flight Enquiry Endpoints
    print("\n✈️  FLIGHT ENQUIRY ENDPOINTS")
    print("-" * 60)
    
    client.force_authenticate(user=None)
    response = client.post('/api/v1/flight-enquiries/', {
        'trip_type': 'oneway',
        'from_location': 'Mumbai',
        'to_location': 'Dubai',
        'departure_date': '2024-12-01',
        'adults': 2,
        'travel_class': 'economy',
        'name': 'Test User',
        'phone': '+919876543210',
        'email': 'test@example.com'
    })
    status = '✅' if response.status_code == 201 else '❌'
    print(f"{status} POST   /api/v1/flight-enquiries/              [{response.status_code}] Create Flight Enquiry")
    if response.status_code == 201:
        results['passed'].append('Create Flight Enquiry')
    else:
        results['failed'].append(f'Create Flight Enquiry ({response.status_code})')
    
    client.force_authenticate(user=admin)
    response = client.get('/api/v1/flight-enquiries/')
    status = '✅' if response.status_code == 200 else '❌'
    print(f"{status} GET    /api/v1/flight-enquiries/              [{response.status_code}] List Flight Enquiries")
    if response.status_code == 200:
        results['passed'].append('List Flight Enquiries')
    else:
        results['failed'].append(f'List Flight Enquiries ({response.status_code})')
    
    # Test General Enquiry Endpoints
    print("\n📧 GENERAL ENQUIRY ENDPOINTS")
    print("-" * 60)
    
    client.force_authenticate(user=None)
    response = client.post('/api/v1/enquiries/', {
        'name': 'Test User',
        'email': 'test@example.com',
        'phone': '+919876543210',
        'service': 'hotels',
        'message': 'Looking for hotels in Goa for vacation'
    })
    status = '✅' if response.status_code == 201 else '❌'
    print(f"{status} POST   /api/v1/enquiries/                     [{response.status_code}] Create Enquiry")
    if response.status_code == 201:
        results['passed'].append('Create Enquiry')
    else:
        results['failed'].append(f'Create Enquiry ({response.status_code})')
    
    client.force_authenticate(user=admin)
    response = client.get('/api/v1/enquiries/')
    status = '✅' if response.status_code == 200 else '❌'
    print(f"{status} GET    /api/v1/enquiries/                     [{response.status_code}] List Enquiries")
    if response.status_code == 200:
        results['passed'].append('List Enquiries')
    else:
        results['failed'].append(f'List Enquiries ({response.status_code})')
    
    # Test User Endpoints
    print("\n👤 USER ENDPOINTS")
    print("-" * 60)
    
    client.force_authenticate(user=user)
    response = client.get('/api/v1/users/me/')
    status = '✅' if response.status_code == 200 else '❌'
    print(f"{status} GET    /api/v1/users/me/                      [{response.status_code}] Get Current User")
    if response.status_code == 200:
        results['passed'].append('Get Current User')
    else:
        results['failed'].append(f'Get Current User ({response.status_code})')
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {len(results['passed'])}")
    print(f"❌ Failed: {len(results['failed'])}")
    print(f"📊 Success Rate: {len(results['passed']) / (len(results['passed']) + len(results['failed'])) * 100:.1f}%")
    
    if results['failed']:
        print("\n❌ Failed Tests:")
        for test in results['failed']:
            print(f"   - {test}")
    
    print("\n" + "=" * 60)
    
    return len(results['failed']) == 0

if __name__ == '__main__':
    success = test_all_endpoints()
    sys.exit(0 if success else 1)
