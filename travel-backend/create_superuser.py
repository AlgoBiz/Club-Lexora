#!/usr/bin/env python
"""
Script to create a superuser for the travel backend
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Check if superuser already exists
if User.objects.filter(username='admin').exists():
    print("✅ Superuser 'admin' already exists!")
    user = User.objects.get(username='admin')
    print(f"   Username: {user.username}")
    print(f"   Email: {user.email}")
else:
    # Create superuser
    user = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123'
    )
    print("✅ Superuser created successfully!")
    print(f"   Username: admin")
    print(f"   Password: admin123")
    print(f"   Email: admin@example.com")
    print("\n⚠️  Please change the password after first login!")
