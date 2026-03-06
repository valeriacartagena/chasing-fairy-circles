#!/bin/bash
# Script to run the backend API server
cd "$(dirname "$0")"
python3 -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
