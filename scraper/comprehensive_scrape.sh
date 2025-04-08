#!/bin/bash
# Script to run the scraper in comprehensive mode for maximum data collection

# Enable more verbose output
set -x

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Create a log file
LOG_FILE="/tmp/scraper_log_$(date '+%Y%m%d_%H%M%S').txt"
log "Starting scraper session. Log file: $LOG_FILE"

# Tee all output to the log file as well as the terminal
exec > >(tee -a "$LOG_FILE") 2>&1

# Display usage information
if [ "$1" == "" ]; then
    log "ERROR: No politician name provided"
    log "Usage: ./comprehensive_scrape.sh \"Politician Name\""
    log "Example: ./comprehensive_scrape.sh \"Donald Trump\""
    exit 1
fi

# Check for Python environment
log "Checking Python environment..."
python3 --version
if [ $? -ne 0 ]; then
    log "ERROR: Python 3 not found. Please install Python 3."
    exit 1
else
    log "Python 3 found successfully"
fi

# Detect if we're in a conda environment
if [ -n "$CONDA_PREFIX" ]; then
    log "Conda environment detected: $CONDA_PREFIX"
    # Use the conda environment's pip
    PIP_CMD="$CONDA_PREFIX/bin/pip"
    PYTHON_CMD="$CONDA_PREFIX/bin/python"
else
    log "Using system Python/pip"
    # Use system pip
    PIP_CMD="pip3"
    PYTHON_CMD="python3"
fi

# Check for required packages using the appropriate Python
log "Checking for required packages..."

log "Testing scrapy import..."
$PYTHON_CMD -c "import scrapy; print(f'Scrapy version: {scrapy.__version__}')" 2>/dev/null
if [ $? -ne 0 ]; then
    log "ERROR: scrapy not found. Please install with: $PIP_CMD install scrapy"
    log "If you're using conda, make sure to activate your environment first:"
    log "conda activate yourenvname"
    exit 1
else
    log "Scrapy package found successfully"
fi

log "Testing dotenv import..."
$PYTHON_CMD -c "import dotenv; print(f'python-dotenv version: {dotenv.__version__}')" 2>/dev/null
if [ $? -ne 0 ]; then
    log "ERROR: python-dotenv not found. Please install with: $PIP_CMD install python-dotenv"
    exit 1
else
    log "python-dotenv package found successfully"
fi

# Check for .env file
log "Checking for .env file..."
if [ -f ../.env ]; then
    log "Found .env file in parent directory"
    log "Contents (with sensitive info masked):"
    grep -v "KEY" ../.env | grep -v "SECRET" | grep -v "PASSWORD" || log "No non-sensitive entries in .env"
    grep "KEY\\|SECRET\\|PASSWORD" ../.env | sed 's/=.*/=********/' || log "No API keys found in .env"
elif [ -f .env ]; then
    log "Found .env file in current directory"
    log "Contents (with sensitive info masked):"
    grep -v "KEY" .env | grep -v "SECRET" | grep -v "PASSWORD" || log "No non-sensitive entries in .env"
    grep "KEY\\|SECRET\\|PASSWORD" .env | sed 's/=.*/=********/' || log "No API keys found in .env"
else
    log "WARNING: No .env file found. NewsAPI functionality may be limited."
    log "Create a .env file with your NewsAPI key for better results."
    log "Example: NEWS_API_KEY=your_api_key_here"
fi

# Check data directory
log "Checking data directory..."
if [ -d "../data" ]; then
    FILE_COUNT=$(find ../data -name "*.json" | wc -l)
    log "Data directory exists with $FILE_COUNT JSON files"
else
    log "WARNING: No data directory found at ../data"
    log "Creating data directory..."
    mkdir -p ../data
    log "Data directory created"
fi

# Show the details of what will be run
log "Running comprehensive data collection for: $1"
log "This will use the following settings:"
log "  - Maximum news pages (100)"
log "  - Extended time span (10 years)"
log "  - Following related Wikipedia links (10 max)"
log "  - Comprehensive data collection mode"
log ""
log "This may take some time. Press Ctrl+C to cancel or any key to continue..."
read -n 1 -s
log "Starting scraper execution..."

# Run the scraper with comprehensive settings with detailed timing
log "Starting comprehensive data collection at $(date)..."
START_TIME=$(date +%s)

# Run script with progress monitoring
$PYTHON_CMD run.py --politician "$1" --comprehensive --verbose &
SCRAPY_PID=$!

# Monitor the scraper process
log "Scraper running with PID: $SCRAPY_PID"
while kill -0 $SCRAPY_PID 2>/dev/null; do
    log "Scraper still running ($(ps -p $SCRAPY_PID -o %cpu= -o %mem= -o etimes=) seconds elapsed)"
    # Check for new files every minute
    CURRENT_FILES=$(find ../data -type f -name "*.json" | sort)
    log "Current data files: $(echo "$CURRENT_FILES" | wc -l)"
    sleep 60
done

# Calculate runtime
END_TIME=$(date +%s)
RUNTIME=$((END_TIME - START_TIME))
HOURS=$((RUNTIME / 3600))
MINUTES=$(( (RUNTIME % 3600) / 60 ))
SECONDS=$((RUNTIME % 60))

log "Data collection completed at $(date)!"
log "Total runtime: ${HOURS}h ${MINUTES}m ${SECONDS}s"
log "Check the data directory for the results."
log "Log file available at: $LOG_FILE" 