#!/bin/bash

# Install formatter-specific requirements
pip install -r formatter/requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Download NLTK resources
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Create necessary directories if they don't exist
mkdir -p data/formatted

echo "Formatter setup complete!" 