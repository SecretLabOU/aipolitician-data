#!/bin/bash
# Script to run the scraper in comprehensive mode for maximum data collection

# Display usage information
if [ "$1" == "" ]; then
    echo "Usage: ./comprehensive_scrape.sh \"Politician Name\""
    echo "Example: ./comprehensive_scrape.sh \"Donald Trump\""
    exit 1
fi

# Check for Python environment
echo "Checking Python environment..."
python3 --version || { echo "Python 3 not found. Please install Python 3."; exit 1; }

# Check for required packages
pip3 list | grep -q scrapy || { echo "scrapy not found. Please install with: pip3 install scrapy"; exit 1; }
pip3 list | grep -q "python-dotenv" || { echo "python-dotenv not found. Please install with: pip3 install python-dotenv"; exit 1; }

# Check for .env file
if [ ! -f ../.env ] && [ ! -f .env ]; then
    echo "Warning: No .env file found. NewsAPI functionality may be limited."
    echo "Create a .env file with your NewsAPI key for better results."
    echo "Example: NEWS_API_KEY=your_api_key_here"
fi

# Show the details of what will be run
echo "Running comprehensive data collection for: $1"
echo "This will use the following settings:"
echo "  - Maximum news pages (100)"
echo "  - Extended time span (10 years)"
echo "  - Following related Wikipedia links (10 max)"
echo "  - Comprehensive data collection mode"
echo ""
echo "This may take some time. Press Ctrl+C to cancel or any key to continue..."
read -n 1 -s

# Run the scraper with comprehensive settings
echo "Starting comprehensive data collection..."
python run.py --politician "$1" --comprehensive

# Make the output file executable
chmod +x comprehensive_scrape.sh

echo "Data collection complete!"
echo "Check the data directory for the results." 