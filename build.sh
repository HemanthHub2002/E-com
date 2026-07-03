#!/usr/bin/env bash
# exit on error
set -o errexit

# Set Cargo home to a writable directory to prevent read-only filesystem errors during Rust builds
export CARGO_HOME=/tmp/cargo

# Install dependencies
pip install -r requirements.txt

# Gather all static assets into STATIC_ROOT
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate
