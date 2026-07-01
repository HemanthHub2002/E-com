#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Gather all static assets into STATIC_ROOT
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate
