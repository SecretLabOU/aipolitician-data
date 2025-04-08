#!/bin/bash
# comprehensive_scrape.sh - Run a comprehensive scrape for a politician

# Check if a politician name was provided
if [ -z "$1" ]; then
    echo "Error: Politician name is required"
    echo "Usage: $0 \"Politician Name\""
    exit 1
fi

# Get the politician name from the first argument
POLITICIAN="$1"

# Check if python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Print a banner
echo "=================================="
echo " Comprehensive Political Scraper"
echo "=================================="
echo "Politician: $POLITICIAN"
echo "This will collect maximum data from:"
echo "- Wikipedia (with link following)"
echo "- News API (with extended time span)"
echo ""

# Run the scraper with comprehensive settings
python3 run.py --politician "$POLITICIAN" --comprehensive

# Check the exit code
if [ $? -ne 0 ]; then
    echo "Error running the scraper. Check the logs above for details."
    exit 1
fi

echo ""
echo "Comprehensive scraping completed!"
echo ""
echo "Next step: Run the ingestion script:"
echo "cd .. && python scripts/ingest_data.py data/*.json" 