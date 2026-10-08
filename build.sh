#!/usr/bin/env bash
# Render build script: install, collect static files, migrate, create admin (first deploy only)
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
# Creates the admin account from DJANGO_SUPERUSER_EMAIL / DJANGO_SUPERUSER_PASSWORD; ignored if it already exists
python manage.py createsuperuser --noinput || true
# Optional: set SEED_DEMO=1 once to load demo products, then remove it
if [ "${SEED_DEMO:-0}" = "1" ]; then python manage.py seed_demo; fi
if [ "${LOAD_DATA:-0}" = "1" ] && [ -f data.json ]; then
  python manage.py loaddata data.json
fi