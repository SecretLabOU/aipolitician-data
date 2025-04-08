#!/bin/bash
# Script to ensure scrapy runs in the correct conda environment

# Check if CONDA_PREFIX is set (we're in a conda environment)
if [ -z "$CONDA_PREFIX" ]; then
    echo "Error: Not running in a conda environment."
    echo "Please activate your conda environment first with:"
    echo "  conda activate your-env-name"
    exit 1
fi

echo "Running with conda Python: $CONDA_PREFIX/bin/python"
echo "Current conda environment: $CONDA_DEFAULT_ENV"

# Add the conda bin directory to the beginning of PATH to ensure we use conda executables
export PATH="$CONDA_PREFIX/bin:$PATH"

# Verify which Python and scrapy we're using
echo "Using Python: $(which python)"
echo "Python version: $(python --version)"
echo "Using scrapy: $(which scrapy)"
echo "Scrapy version: $(python -c 'import scrapy; print(scrapy.__version__)')"

# Check if spaCy is available
if python -c "import spacy" &> /dev/null; then
    echo "spaCy is available: $(python -c 'import spacy; print(spacy.__version__)')"
    # Check if the language model is loaded
    if python -c "import spacy; spacy.load('en_core_web_sm')" &> /dev/null; then
        echo "en_core_web_sm model is loaded correctly"
    else
        echo "Error: en_core_web_sm model is not available"
        echo "Install it with: python -m spacy download en_core_web_sm"
        exit 1
    fi
else
    echo "Error: spaCy is not available"
    echo "Install it with: pip install spacy"
    exit 1
fi

# Run the command with the explicit conda Python
$CONDA_PREFIX/bin/python -m scrapy $@ 