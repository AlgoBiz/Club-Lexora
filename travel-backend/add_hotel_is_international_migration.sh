#!/bin/bash
# Migration script to add is_international field to Hotel model

cd "$(dirname "$0")"

echo "Creating migration for Hotel.is_international field..."
python manage.py makemigrations user_account --name add_hotel_is_international

echo ""
echo "Migration created successfully!"
echo "To apply the migration, run:"
echo "  python manage.py migrate"
