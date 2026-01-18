#!/bin/bash

# Run database migrations
echo "Running database migrations..."
flask db upgrade

# Start the application
echo "Starting application..."
exec gunicorn run:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
