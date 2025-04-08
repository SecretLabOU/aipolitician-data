#!/bin/bash
# Wrapper script to run the AI Politician Scraper with the correct environment

# Determine the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if running inside a conda environment
if [[ -z "$CONDA_DEFAULT_ENV" ]]; then
  echo "Error: This script should be run inside a conda environment."
  echo "Please activate your conda environment first with:"
  echo "  conda activate YOUR_ENV_NAME"
  exit 1
fi

# Check if the Python environment is set up correctly
echo "Checking environment..."
python env_check.py
if [ $? -ne 0 ]; then
  echo "Environment check failed. Please fix the issues above before continuing."
  exit 1
fi

# Make sure all required dependencies are installed
echo "Making sure all dependencies are installed..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
  echo "Failed to install dependencies."
  exit 1
fi

# Make sure the spaCy language model is installed
echo "Making sure spaCy language model is installed..."
python -m spacy download en_core_web_sm
if [ $? -ne 0 ]; then
  echo "Failed to download spaCy language model."
  exit 1
fi

# Run the scraper
echo "Running scraper..."
python run.py "$@" 