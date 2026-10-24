#!/usr/bin/env bash
# Render corre este script en cada deploy.
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py poblar_demo
