 #!/bin/bash

# Setup script for SQL Rule Extractor

set -e

echo "======================================"
echo "SQL Rule Extractor - Setup"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."

# Function to check if a Python version meets requirements
check_python_version() {
    local python_cmd=$1
    if command -v "$python_cmd" &> /dev/null; then
        if "$python_cmd" -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
            echo "$python_cmd"
            return 0
        fi
    fi
    return 1
}

# Try to find Python 3.10+ (prefer python3.11, python3.10, then python3)
PYTHON_CMD=""
for cmd in python3.11 python3.10 python3; do
    if check_python_version "$cmd"; then
        PYTHON_CMD="$cmd"
        break
    fi
done

# If no suitable Python found, try to install via Homebrew
if [ -z "$PYTHON_CMD" ]; then
    echo "Python 3.10+ not found. Checking for Homebrew..."
    if command -v brew &> /dev/null; then
        echo "Installing Python 3.11 via Homebrew..."
        brew install python@3.11
        # Try python3.11 after installation
        if check_python_version python3.11; then
            PYTHON_CMD="python3.11"
        elif check_python_version python3; then
            PYTHON_CMD="python3"
        fi
    fi
fi

# Final check
if [ -z "$PYTHON_CMD" ]; then
    echo "Error: Python 3.10 or higher is required but not found."
    echo "Please install Python 3.10+ manually:"
    echo "  - macOS: brew install python@3.11"
    echo "  - Linux: Use your distribution's package manager"
    echo "  - Windows: Download from https://www.python.org/downloads/"
    exit 1
fi

python_version=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version using $PYTHON_CMD"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d ".venv" ]; then
    echo "Virtual environment already exists"
else
    $PYTHON_CMD -m venv .venv
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
