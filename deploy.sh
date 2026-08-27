#!/bin/bash
set -e

APP_DIR="/var/www/flask_app"

echo "=== Pulling latest changes from git ==="
cd $APP_DIR
git pull origin main

echo "=== Activating virtual environment ==="
source venv/bin/activate

echo "=== Installing dependencies ==="
pip install -r requirements.txt

echo "=== Running Database Migrations ==="
flask db upgrade || echo "No new migrations to apply."

echo "=== Restarting Gunicorn Service ==="
sudo systemctl restart flaskapp

echo "=== Deployment Completed Successfully! ==="
