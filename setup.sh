#!/bin/bash

# Set Python version (choose one of your installed versions)
echo "Setting Python version..."
pyenv local 3.12.2

# Create virtual environment
echo "Creating virtual environment..."
python -m venv myenv

# Activate virtual environment
echo "Activating virtual environment..."
source myenv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Setup complete! To activate the environment, run:"
echo "source myenv/bin/activate"