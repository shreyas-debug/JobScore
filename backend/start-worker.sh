#!/bin/bash
set -e

echo "Starting celery worker..."
# Start celery in the background
celery -A app.workers.celery_app worker --loglevel=info &

# Start a dummy python web server in the foreground on the port Render assigns
# This keeps the "Web Service" alive since Render requires it to bind to a port
PORT="${PORT:-8000}"
echo "Starting dummy web server on port $PORT to satisfy Render health checks..."
exec python -m http.server $PORT
