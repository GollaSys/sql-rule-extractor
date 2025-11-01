#!/bin/bash

# Setup script for SQL Rule Extractor

set -e

echo "======================================"
echo "SQL Rule Extractor - Setup"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Check if Python >= 3.10
required_version="3.10"
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "Error: Python 3.10 or higher is required"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d ".venv" ]; then
    echo "Virtual environment already exists"
else
    python3 -m venv .venv
    echo "Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "======================================"
echo "Setup complete!"
echo "======================================"
echo ""
echo "To activate the environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To run the tool on the sample repository:"
echo "  python -m src.cli analyze --repo sample_repos/sample_sql_app --out drd.xml --format all"
echo ""
echo "To run tests:"
echo "  pytest -v"
echo ""
