#!/bin/bash
# Amadeus Ramp-Up Dashboard — Quick Setup
# Run: bash setup.sh

set -e

echo ""
echo "============================================"
echo "  Amadeus Ramp-Up Dashboard — Setup"
echo "============================================"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[1/3] Creating virtual environment..."
    python3 -m venv venv
else
    echo "[1/3] Virtual environment already exists."
fi

# Activate and install dependencies
echo "[2/3] Installing dependencies..."
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo "[3/3] Ready!"
echo ""
echo "============================================"
echo "  To start the dashboard:"
echo ""
echo "    source venv/bin/activate"
echo "    python run.py"
echo ""
echo "  Then open http://localhost:8050"
echo ""
echo "  To use your own Excel file:"
echo "    RAMPUP_EXCEL_PATH=/path/to/file.xlsx python run.py"
echo "============================================"
echo ""
