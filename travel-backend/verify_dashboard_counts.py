#!/usr/bin/env python
"""
Verify Dashboard Counts - Check if the API returns correct counts
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from apps.user_account.models import Hotel, Package, FlightEnquiry, Enquiry

def verify_counts():
    """Verify all counts match the database"""
    
    print("🔍 Verifying Dashboard Counts")
    print("=" * 60)
    print()
    
    # Get actual counts from database
    hotels_count = Hotel.objects.filter(is_active=True).count()
    packages_count = Package.objects.filter(is_active=True).count()
    flight_enquiries_count = FlightEnquiry.objects.filter(is_active=True).count()
    general_enquiries_count = Enquiry.objects.filter(is_active=True).count()
    featured_hotels_count = Hotel.objects.filter(is_active=True, is_featured=True).count()
    trending_hotels_count = Hotel.objects.filter(is_active=True, is_trending=True).count()
    
    print("📊 Database Counts:")
    print("-" * 60)
    print(f"🏨 Hotels (is_active=True): {hotels_count}")
    print(f"📦 Packages (is_active=True): {packages_count}")
    print(f"✈️  Flight Enquiries (is_active=True): {flight_enquiries_count}")
    print(f"📧 General Enquiries (is_active=True): {general_enquiries_count}")
    print(f"⭐ Featured Hotels (is_active=True, is_featured=True): {featured_hotels_count}")
    print(f"🔥 Trending Hotels (is_active=True, is_trending=True): {trending_hotels_count}")
    print()
    
    # Show details of general enquiries
    if general_enquiries_count > 0:
        print("📋 General Enquiries Details:")
        print("-" * 60)
        enquiries = Enquiry.objects.filter(is_active=True)
        for i, enq in enumerate(enquiries, 1):
            print(f"{i}. Name: {enq.name}")
            print(f"   Email: {enq.email}")
            print(f"   Service: {enq.service}")
            print(f"   Status: {enq.status}")
            print(f"   Date: {enq.date_added.strftime('%Y-%m-%d %H:%M')}")
            print()
    
    # Check for inactive items
    print("🔍 Checking for Inactive Items:")
    print("-" * 60)
    inactive_hotels = Hotel.objects.filter(is_active=False).count()
    inactive_packages = Package.objects.filter(is_active=False).count()
    inactive_flight_enq = FlightEnquiry.objects.filter(is_active=False).count()
    inactive_general_enq = Enquiry.objects.filter(is_active=False).count()
    
    print(f"Inactive Hotels: {inactive_hotels}")
    print(f"Inactive Packages: {inactive_packages}")
    print(f"Inactive Flight Enquiries: {inactive_flight_enq}")
    print(f"Inactive General Enquiries: {inactive_general_enq}")
    print()
    
    # Summary
    print("=" * 60)
    print("✅ Verification Complete!")
    print()
    print("Expected API Response:")
    print("-" * 60)
    print(f'{{"message": "Dashboard statistics retrieved successfully.",')
    print(f' "data": {{')
    print(f'   "hotels_count": {hotels_count},')
    print(f'   "packages_count": {packages_count},')
    print(f'   "flight_enquiries_count": {flight_enquiries_count},')
    print(f'   "general_enquiries_count": {general_enquiries_count},')
    print(f'   "featured_hotels_count": {featured_hotels_count},')
    print(f'   "trending_hotels_count": {trending_hotels_count}')
    print(f' }}}}')
    print()
    
    # Check if database is empty
    if all([hotels_count == 0, packages_count == 0, flight_enquiries_count == 0]):
        print("💡 TIP: Your database appears to be mostly empty.")
        print("   To add test data, you can:")
        print("   1. Use Django Admin: python manage.py runserver")
        print("      Then visit: http://localhost:8000/admin/")
        print("   2. Create items via API endpoints")
        print("   3. Load fixtures if available")
        print()

if __name__ == '__main__':
    try:
        verify_counts()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
