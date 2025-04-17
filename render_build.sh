#!/usr/bin/env bash
# This script runs during the build phase on Render
# It prepares the application for deployment

# Exit on error
set -o errexit

echo "Build phase started..."

# Print environment variables (without sensitive values)
echo "RENDER environment variable: $RENDER"
echo "SUPABASE_URL exists: $(if [ -n "$SUPABASE_URL" ]; then echo "yes"; else echo "no"; fi)"
echo "SUPABASE_DB_HOST exists: $(if [ -n "$SUPABASE_DB_HOST" ]; then echo "yes"; else echo "no"; fi)"

# We're using Supabase for the database
# The database is already set up and populated
echo "Using Supabase database - no initialization needed during build"

echo "Build phase completed successfully!"
