#!/bin/bash

# Chinese Switch Parser Installation Script

echo "=========================================="
echo "Chinese Switch Parser Installation"
echo "=========================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    echo "Please install Python 3.8 or higher and try again."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Error: Python 3.8 or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION found"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Make scripts executable
echo "Making scripts executable..."
chmod +x chinese_switch_parser.py
chmod +x advanced_parser.py
chmod +x cli_tool.py
chmod +x web_interface.py
chmod +x test_parser.py
chmod +x demo.py

# Create exports directory
echo "Creating exports directory..."
mkdir -p exports

# Run tests
echo "Running tests..."
python test_parser.py

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "To get started:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the demo: python demo.py"
echo "3. Try the CLI: python cli_tool.py connect --url http://10.41.8.33"
echo "4. Start web interface: python cli_tool.py web"
echo ""
echo "For more information, see README.md"
echo "=========================================="

