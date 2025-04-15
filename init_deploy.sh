#!/usr/bin/env bash
# This script runs during the initial deploy hook on Render
# It initializes the database with sample data

# Don't exit on error so we can see all errors
set +o errexit

echo "=== INITIAL DEPLOY HOOK STARTED ==="
echo "Current directory: $(pwd)"
echo "Files in current directory: $(ls -la)"

echo "=== CHECKING ENVIRONMENT ==="
echo "RENDER environment variable: $RENDER"
echo "DATABASE_URL exists: $(if [ -n "$DATABASE_URL" ]; then echo "yes"; else echo "no"; fi)"
echo "Python version: $(python --version)"

echo "=== RUNNING DATABASE INITIALIZATION ==="
echo "Running db_init.py..."
python db_init.py

echo "=== VERIFYING DATABASE ==="
echo "Checking database status..."
python -c "from app import db, Equipment;
try:
    count = Equipment.query.count()
    print(f'Equipment count: {count}')
except Exception as e:
    print(f'Error checking equipment count: {e}')
"

echo "=== INITIAL DEPLOY HOOK COMPLETED SUCCESSFULLY ==="
