#!/bin/bash
# Production startup script for AI Investment Tool

echo "🚀 Starting AI Investment Tool in Production Mode"
echo "=================================================="

# Set production environment
export ENVIRONMENT=production

# Kill any existing process on port 8081
echo "Stopping any existing server on port 8081..."
lsof -ti:8081 | xargs kill -9 2>/dev/null || true

# Start production server
echo "Starting production server with optimized threading..."
pipenv run python start_production.py 