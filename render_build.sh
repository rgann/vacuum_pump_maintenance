#!/usr/bin/env bash
# This script runs during the build phase on Render
# It initializes the database with sample data

# Exit on error
set -o errexit

echo "Running database initialization script..."
python db_init.py

echo "Build phase completed successfully!"
