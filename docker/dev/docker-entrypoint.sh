#!/bin/bash

# Exit on any error
set -e

echo "Starting Django application..."

# Run database migrations
echo "Running migrations..."
python manage.py migrate

# Create cache table
echo "Creating cache table..."
python manage.py createcachetable

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the application with runserver
echo "Starting Python server..."

echo "Starting with debugpy for remote debugging..."
PYDEVD_DISABLE_FILE_VALIDATION=1 python -Xfrozen_modules=off -m debugpy --listen 0.0.0.0:5678 --wait-for-client manage.py runserver 0.0.0.0:8000
