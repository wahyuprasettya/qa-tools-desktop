#!/bin/bash

# Simple launcher script for QA Tools Desktop

echo "Starting QA Tools Desktop..."

# Check if .venv exists, if not create it
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install/upgrade dependencies
echo "Checking Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Run the application
echo "Launching application..."
python -m app.main
