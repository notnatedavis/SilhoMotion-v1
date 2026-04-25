# scripts/setup.sh

#!/bin/bash

echo "Checking Python version..."
python3 --version

echo "Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "Installing requirements..."
pip install -r requirements.txt

echo "Setup complete. Run 'source .venv/bin/activate' to start."