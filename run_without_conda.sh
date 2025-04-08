#!/bin/bash

# Simple wrapper script for Linux systems without Conda
# Uses Python virtual environment instead

# ===== CONFIGURATION =====
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON_CMD="python3"

# Check if Python 3 is installed
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3 before running this script."
    exit 1
fi

# Check if the argument was provided
if [ $# -lt 1 ]; then
    echo "Please provide a politician name. Usage: $0 \"Politician Name\""
    exit 1
fi

POLITICIAN_NAME="$1"
echo "Setting up data pipeline for politician: $POLITICIAN_NAME"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/requirements.txt"

# Download required models
echo "Downloading NLP models..."
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Create data directories
mkdir -p "$SCRIPT_DIR/data/politicians"
mkdir -p "$SCRIPT_DIR/data/formatted"
mkdir -p "$SCRIPT_DIR/data/chroma_db"

# Set up ChromaDB
echo "Setting up ChromaDB..."
python "$SCRIPT_DIR/scripts/chroma_setup.py"

# Scrape politician data
echo "Scraping data for $POLITICIAN_NAME..."
python "$SCRIPT_DIR/scraper/politician_scraper.py" "$POLITICIAN_NAME"

# Find the scraped file
SCRAPED_FILE=$(find "$SCRIPT_DIR/data/politicians" -name "*.json" -exec grep -l "$POLITICIAN_NAME" {} \; | head -n 1)
if [ -z "$SCRAPED_FILE" ]; then
    echo "No scraped data found for $POLITICIAN_NAME"
    exit 1
fi

# Format the data
echo "Formatting data..."
python "$SCRIPT_DIR/formatter/data_formatter.py" --single "$SCRAPED_FILE"

# Find the formatted file
FORMATTED_FILE=$(find "$SCRIPT_DIR/data/formatted" -name "formatted_*.json" -exec grep -l "$POLITICIAN_NAME" {} \; | head -n 1)
if [ -z "$FORMATTED_FILE" ]; then
    echo "No formatted data found for $POLITICIAN_NAME"
    exit 1
fi

# Load data into ChromaDB
echo "Loading data into ChromaDB..."
python "$SCRIPT_DIR/scripts/ingest_data_patched.py" "$FORMATTED_FILE"

# Test query
echo "Running test query..."
python "$SCRIPT_DIR/scripts/query_data_patched.py" --query "Tell me about $POLITICIAN_NAME" --politician "$POLITICIAN_NAME" --results 2

# Deactivate virtual environment
deactivate

echo "Pipeline completed successfully!"
echo "You can now query the data using:"
echo "source $VENV_DIR/bin/activate && python scripts/query_data_patched.py --query \"Your question?\" --politician \"$POLITICIAN_NAME\""

exit 0 