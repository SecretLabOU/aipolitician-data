#!/bin/bash
# Setup script for the AI Politician Scraper

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Downloading spaCy language model..."
python -m spacy download en_core_web_sm

echo "Setup complete! You can now run the scraper with:"
echo "python run.py --politician \"Politician Name\"" 