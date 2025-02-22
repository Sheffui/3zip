#!/bin/bash

VENV_DIR=".venv"

# Check if the virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
  echo "Virtual environment not found. Creating..."
  python3 -m venv "$VENV_DIR"
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
  echo "Installing requirements..."
  pip install -r requirements.txt
  echo "Running..."
  python main.py
  deactivate
else
  echo "requirements.txt not found. Aborting."
fi
