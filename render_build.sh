#!/usr/bin/env bash
# This script runs during the build phase on Render
# It initializes the database with sample data

# Exit on error
set -o errexit

echo "Running direct database initialization script..."
python direct_db_init.py

# Also run the other initialization scripts as backups
echo "Running render initialization script..."
python render_init_db.py

echo "Running standard initialization script..."
python init_db.py

echo "Build phase completed successfully!"
