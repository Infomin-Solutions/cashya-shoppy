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

# Start the application with Gunicorn
echo "Starting Gunicorn server..."
gunicorn myproject.wsgi:application --bind 0.0.0.0:5025
