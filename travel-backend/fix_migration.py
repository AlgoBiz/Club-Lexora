#!/usr/bin/env python
"""
Script to fix the migration issue by creating destinations before adding foreign key
Run this script before running migrations
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.user_account.models import Package, Destination

def fix_migration():
    print("Starting migration fix...")
    
    # Get all packages
    packages = Package.objects.all()
    print(f"Found {packages.count()} packages")
    
    if packages.count() == 0:
        print("No packages found. Safe to run migrations.")
        return
    
    # Create a default destination for existing packages
    default_destination, created = Destination.objects.get_or_create(
        slug='default-destination',
        defaults={
            'name': 'Default Destination',
            'location': 'To be updated',
            'description': 'Default destination for existing packages. Please update.',
            'is_international': False,
        }
    )
    
    if created:
        print(f"Created default destination: {default_destination.name} (ID: {default_destination.id})")
    else:
        print(f"Using existing default destination: {default_destination.name} (ID: {default_destination.id})")
    
    print("\nNOTE: After migration completes, please:")
    print("1. Create proper destinations via admin or API")
    print("2. Update packages to reference the correct destinations")
    print("3. Optionally delete the 'Default Destination' if no longer needed")
    
    print("\nMigration fix completed successfully!")

if __name__ == '__main__':
    fix_migration()
