#!/bin/sh

# Exit on error
set -e

echo "Waiting for PostgreSQL..."
while ! nc -z $DBHOST $DBPORT; do
  sleep 0.1
done
echo "PostgreSQL started"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "Creating superuser..."
python create_superuser.py || true

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

exec "$@"
