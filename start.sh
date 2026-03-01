#!/bin/bash
echo "================================================"
echo "  ZOMATHON KPT Prediction System"
echo "================================================"
echo ""

# Check python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found. Please install Python 3.8+"
    exit 1
fi

# Install deps
echo "Installing dependencies..."
cd backend
pip install -r requirements.txt -q

echo ""
echo "Starting backend on http://localhost:8000 ..."
echo "Open frontend/index.html in your browser."
echo ""
echo "Press Ctrl+C to stop."
echo "================================================"
echo ""

uvicorn main:app --reload --port 8000
