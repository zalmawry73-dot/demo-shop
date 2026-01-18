#!/bin/bash

echo "Seeding database with default data..."
python seed_data.py || echo "Seed data already exists or failed (continuing anyway)"

echo "Starting FastAPI application..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
