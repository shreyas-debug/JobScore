#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting web server..."
# Use the PORT environment variable provided by Render, fallback to 8000
PORT="${PORT:-8000}"
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
