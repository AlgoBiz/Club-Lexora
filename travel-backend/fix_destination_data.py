#!/usr/bin/env python
"""
Fix destination foreign key issue before migration
Run: python fix_destination_data.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

def fix_destination_issue():
    print("Fixing destination foreign key issue...")
    
    with connection.cursor() as cursor:
        # Check if destination table exists and has the problematic structure
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_account_destination'")
        if not cursor.fetchone():
            print("Destination table doesn't exist yet. Safe to migrate.")
            return
        
        # Check if package table has destination_id column
        cursor.execute("PRAGMA table_info(user_account_package)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'destination_id' not in columns:
            print("Package table doesn't have destination_id yet. Safe to migrate.")
            return
        
        # Get packages with invalid destination_id
        cursor.execute("""
            SELECT id, destination_id FROM user_account_package 
            WHERE destination_id IS NOT NULL
        """)
        packages = cursor.fetchall()
        
        if not packages:
            print("No packages found. Safe to migrate.")
            return
        
        print(f"Found {len(packages)} package(s) with destination references")
        
        # Create a default destination with the expected ID
        default_dest_id = '00000000000000000000000000000001'
        
        cursor.execute("""
            SELECT id FROM user_account_destination WHERE id = ?
        """, [default_dest_id])
        
        if not cursor.fetchone():
            print(f"Creating default destination with ID: {default_dest_id}")
            
            # Get current timestamp
            from django.utils import timezone
            now = timezone.now()
            
            cursor.execute("""
                INSERT INTO user_account_destination 
                (id, auto_id, name, slug, location, description, is_international, 
                 is_active, date_added, date_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                default_dest_id,
                'DEST001',
                'Default Destination',
                'default-destination',
                'To be updated',
                'Default destination created for existing packages. Please update.',
                0,  # is_international = False
                1,  # is_active = True
                now,
                now
            ])
            print("✓ Default destination created successfully")
        else:
            print("✓ Default destination already exists")
    
    print("\n" + "="*60)
    print("Fix completed! You can now run: python manage.py migrate")
    print("="*60)
    print("\nIMPORTANT: After migration:")
    print("1. Create proper destinations via admin or API")
    print("2. Update packages to reference correct destinations")
    print("3. Delete 'Default Destination' if no longer needed")

if __name__ == '__main__':
    try:
        fix_destination_issue()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
