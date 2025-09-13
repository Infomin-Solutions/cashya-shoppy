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
python manage.py runserver 0.0.0.0:8000
