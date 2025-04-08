#!/bin/bash
# setup.sh - Install dependencies for the AI Politician scraper

# Exit on error
set -e

echo "===== Setting up AI Politician Scraper ====="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed. Please install pip3 first."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Install spaCy language model
echo "Installing spaCy language model..."
python3 -m spacy download en_core_web_sm

# Copy .env.example to .env if it doesn't exist
if [ ! -f "../.env" ]; then
    echo "Creating .env file from template..."
    cp ../.env.example ../.env
    echo "Please edit ../.env to add your API keys."
fi

echo ""
echo "===== Setup Complete ====="
echo "You can now run the scraper with: python3 run.py --politician \"Politician Name\""
echo ""
echo "Tip: First sign up for a NewsAPI key at https://newsapi.org/"
echo "and add it to your .env file in the project root directory." 