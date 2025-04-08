#!/bin/bash

# Install required packages
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Create required directories if they don't exist
mkdir -p data/politicians
mkdir -p data/formatted

echo "Setup complete!" 