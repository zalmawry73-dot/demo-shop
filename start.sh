#!/bin/bash

echo "Starting FastAPI application..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
