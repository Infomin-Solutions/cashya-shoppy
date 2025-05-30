#!/bin/bash

python manage.py collectstatic --noinput
gunicorn myproject.wsgi:application --bind 0.0.0.0:8000
