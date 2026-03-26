#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo "Starting Builder's OS on http://localhost:8100"
uvicorn main:app --host 0.0.0.0 --port 8100 --reload
