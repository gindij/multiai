#!/bin/bash

# Create and activate virtual environment
python3 -m venv multiai_env

# Activation command instructions
echo "Virtual environment created. To activate, run:"
echo ""
echo "source multiai_env/bin/activate  # On Linux/Mac"
echo "multiai_env\\Scripts\\activate  # On Windows"
echo ""

# Prompt to activate and install requirements
echo "After activating the environment, install dependencies with:"
echo "pip install -r requirements.txt"
echo ""
echo "Then set up your API keys with:"
echo "python cli.py setup"