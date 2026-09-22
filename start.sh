#!/bin/bash
cd "$(dirname "$0")"
echo "Starting Stock Predictor..."
echo "Open http://localhost:3001"
python3 -m uvicorn main:app --host 0.0.0.0 --port 3001 --reload
