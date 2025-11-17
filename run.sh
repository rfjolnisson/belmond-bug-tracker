#!/bin/bash
# Run Belmond Bug Tracker

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Running setup first..."
    ./setup.sh
fi

# Activate virtual environment
source venv/bin/activate

# Run Streamlit on port 8502
echo "🚀 Starting Belmond Bug Tracker on http://localhost:8502..."
streamlit run app.py --server.port 8502

