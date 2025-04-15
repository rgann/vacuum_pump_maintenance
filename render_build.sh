#!/usr/bin/env bash
# This script runs during the build phase on Render
# It prepares the application for deployment

# Exit on error
set -o errexit

echo "Build phase started..."

# Print environment variables (without sensitive values)
echo "RENDER environment variable: $RENDER"
echo "DATABASE_URL exists: $(if [ -n "$DATABASE_URL" ]; then echo "yes"; else echo "no"; fi)"

# We don't initialize the database here anymore
# Database initialization happens in initialDeployHook in render.yaml
echo "Database will be initialized after deployment"

echo "Build phase completed successfully!"
