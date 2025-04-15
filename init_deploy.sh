#!/usr/bin/env bash
# This script runs during the initial deploy hook on Render
# It initializes the database with sample data

# Exit on error
set -o errexit

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
python -c "from app import db, Equipment; print(f'Equipment count: {Equipment.query.count()}')"

echo "=== INITIAL DEPLOY HOOK COMPLETED SUCCESSFULLY ==="
