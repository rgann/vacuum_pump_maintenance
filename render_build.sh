#!/usr/bin/env bash
# This script runs during the build phase on Render
# It initializes the database with sample data

# Exit on error
set -o errexit

echo "Running database initialization script..."
python render_init_db.py

# Also run the regular init script as a backup
echo "Running standard initialization script..."
python init_db.py

echo "Build phase completed successfully!"
