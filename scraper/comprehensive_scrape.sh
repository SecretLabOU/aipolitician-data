#!/bin/bash
# Script to run the scraper in comprehensive mode for maximum data collection

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
    # Try python command if python3 fails
    log "python3 not found, trying python..."
    python --version
    if [ $? -ne 0 ]; then
        log "ERROR: Python not found. Please install Python 3."
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi
log "Python found successfully"

# Detect if we're in a conda environment
if [ -n "$CONDA_PREFIX" ]; then
    log "Conda environment detected: $CONDA_PREFIX"
    # Use the conda environment's executables if available
    if [ -f "$CONDA_PREFIX/bin/pip" ]; then
        PIP_CMD="$CONDA_PREFIX/bin/pip"
    elif [ -f "$CONDA_PREFIX/bin/pip3" ]; then
        PIP_CMD="$CONDA_PREFIX/bin/pip3"
    else
        log "Using system pip as conda pip not found"
        PIP_CMD="pip"
    fi
    
    if [ -f "$CONDA_PREFIX/bin/python" ]; then
        PYTHON_CMD="$CONDA_PREFIX/bin/python"
    elif [ -f "$CONDA_PREFIX/bin/python3" ]; then
        PYTHON_CMD="$CONDA_PREFIX/bin/python3"
    fi
    
    log "Using Python: $PYTHON_CMD"
    log "Using Pip: $PIP_CMD"
else
    # Use system commands
    log "No conda environment detected, using system Python/pip"
    PIP_CMD="pip3"
    # PYTHON_CMD already set above
fi

# More robust check for required packages
log "Checking for required packages..."

# Define a function to check if a package is installed
check_package() {
    PACKAGE_NAME=$1
    IMPORT_NAME=$2
    
    log "Checking if $PACKAGE_NAME is installed..."
    
    # Try multiple methods
    # 1. Try to import the package
    $PYTHON_CMD -c "import $IMPORT_NAME" 2>/dev/null
    IMPORT_RESULT=$?
    
    # 2. Try to find it with pip
    $PIP_CMD list | grep -i "$PACKAGE_NAME" >/dev/null 2>&1
    PIP_RESULT=$?
    
    # 3. Try to find it with conda list if in a conda environment
    CONDA_RESULT=1
    if [ -n "$CONDA_PREFIX" ]; then
        conda list | grep -i "$PACKAGE_NAME" >/dev/null 2>&1
        CONDA_RESULT=$?
    fi
    
    # Package is considered installed if any method succeeds
    if [ $IMPORT_RESULT -eq 0 ] || [ $PIP_RESULT -eq 0 ] || [ $CONDA_RESULT -eq 0 ]; then
        log "$PACKAGE_NAME found successfully"
        return 0
    else
        log "WARNING: $PACKAGE_NAME not found"
        return 1
    fi
}

# Check for required packages
check_package "scrapy" "scrapy"
if [ $? -ne 0 ]; then
    log "ERROR: scrapy not found. Please install with: $PIP_CMD install scrapy"
    log "If you're using conda, make sure to activate your environment first:"
    log "conda activate yourenvname"
    exit 1
fi

check_package "python-dotenv" "dotenv"
if [ $? -ne 0 ]; then
    log "ERROR: python-dotenv not found. Please install with: $PIP_CMD install python-dotenv"
    exit 1
fi

# Check for spaCy (optional)
check_package "spacy" "spacy"
if [ $? -eq 0 ]; then
    log "Checking for spaCy language model..."
    $PYTHON_CMD -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null
    if [ $? -eq 0 ]; then
        log "spaCy language model found successfully"
    else
        log "WARNING: spaCy is installed but en_core_web_sm model is missing"
        log "Text processing will be limited. To install the model:"
        log "$PYTHON_CMD -m spacy download en_core_web_sm"
    fi
else
    log "WARNING: spaCy is not installed. Text processing will be limited."
    log "Consider installing: $PIP_CMD install spacy"
fi

# Check for .env file using more portable commands
log "Checking for .env file..."
if [ -f "../.env" ]; then
    log "Found .env file in parent directory"
    log "Contents (with sensitive info masked):"
    grep -i "api_key\\|key\\|token" "../.env" | sed 's/=.*/=********/' || log "No API keys found"
elif [ -f ".env" ]; then
    log "Found .env file in current directory"
    log "Contents (with sensitive info masked):"
    grep -i "api_key\\|key\\|token" ".env" | sed 's/=.*/=********/' || log "No API keys found"
else
    log "WARNING: No .env file found. NewsAPI functionality may be limited."
    log "Create a .env file with your NewsAPI key for better results."
    log "Example: NEWS_API_KEY=your_api_key_here"
fi

# Check data directory using portable commands
log "Checking data directory..."
if [ -d "../data" ]; then
    FILE_COUNT=$(find ../data -name "*.json" | wc -l)
    log "Data directory exists with $FILE_COUNT JSON files"
else
    log "WARNING: No data directory found at ../data"
    log "Creating data directory..."
    mkdir -p "../data"
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
LAST_MODIFIED_TIME=$START_TIME
LAST_FILE_COUNT=0

# Check if run.py accepts the verbose flag - more carefully
$PYTHON_CMD run.py --help 2>&1 | grep -q "\-\-verbose"
if [ $? -eq 0 ]; then
    log "Running scraper with verbose output enabled"
    VERBOSE_FLAG="--verbose"
else
    log "Verbose flag not supported, running with standard output"
    VERBOSE_FLAG=""
fi

# Run script with progress monitoring
log "Executing: $PYTHON_CMD run.py --politician \"$1\" --comprehensive $VERBOSE_FLAG"

# Run in foreground with timeout monitoring
$PYTHON_CMD run.py --politician "$1" --comprehensive $VERBOSE_FLAG &
SCRAPY_PID=$!

# Monitor the scraper process
log "Scraper running with PID: $SCRAPY_PID"
STUCK_COUNTER=0
STUCK_THRESHOLD=10  # Consider stuck after 10 minutes with no new files

while kill -0 $SCRAPY_PID 2>/dev/null; do
    # Get process stats (more portable version)
    if command -v ps >/dev/null 2>&1; then
        # System has ps command
        CPU_USAGE=$(ps -p $SCRAPY_PID -o %cpu= 2>/dev/null | tr -d ' ' || echo "N/A")
        MEM_USAGE=$(ps -p $SCRAPY_PID -o %mem= 2>/dev/null | tr -d ' ' || echo "N/A")
        RUNTIME=$(ps -p $SCRAPY_PID -o etimes= 2>/dev/null | tr -d ' ' || echo "0")
    else
        # Fallback if ps not available or doesn't support these options
        CPU_USAGE="N/A"
        MEM_USAGE="N/A"
        RUNTIME=$(($(date +%s) - START_TIME))
    fi
    
    # Handle non-numeric runtime gracefully
    if ! [[ "$RUNTIME" =~ ^[0-9]+$ ]]; then
        RUNTIME=$(($(date +%s) - START_TIME))
    fi
    
    # Format runtime as hours:minutes:seconds
    RUNTIME_HOURS=$((RUNTIME / 3600))
    RUNTIME_MINUTES=$(( (RUNTIME % 3600) / 60 ))
    RUNTIME_SECONDS=$((RUNTIME % 60))
    RUNTIME_FORMATTED="${RUNTIME_HOURS}h ${RUNTIME_MINUTES}m ${RUNTIME_SECONDS}s"
    
    # Check for new files using portable commands
    CURRENT_FILES=$(find ../data -type f -name "*.json" 2>/dev/null | sort)
    CURRENT_FILE_COUNT=$(echo "$CURRENT_FILES" | grep -v "^$" | wc -l)
    
    # Portable way to find newest file and its timestamp
    NEWEST_FILE=""
    NEWEST_FILE_TIME=0
    for file in $CURRENT_FILES; do
        if [ -f "$file" ]; then
            # Get file modification time in seconds since epoch
            if command -v stat >/dev/null 2>&1; then
                # Try stat command, which works differently on Linux vs Mac
                if stat --version 2>/dev/null | grep -q GNU; then
                    # GNU stat (Linux)
                    FILE_MTIME=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null || date +%s)
                else
                    # BSD stat (Mac)
                    FILE_MTIME=$(stat -f %m "$file" 2>/dev/null || date +%s)
                fi
            else
                # Fallback to ls
                FILE_MTIME=$(ls -l --time-style=+%s "$file" 2>/dev/null | awk '{print $6}')
                if [ -z "$FILE_MTIME" ]; then
                    FILE_MTIME=$START_TIME
                fi
            fi
            
            if [ "$FILE_MTIME" -gt "$NEWEST_FILE_TIME" ]; then
                NEWEST_FILE="$file"
                NEWEST_FILE_TIME="$FILE_MTIME"
            fi
        fi
    done
    
    # Calculate file age
    if [ -n "$NEWEST_FILE" ] && [ "$NEWEST_FILE_TIME" -gt 0 ]; then
        NEWEST_FILE_AGE=$(($(date +%s) - NEWEST_FILE_TIME))
        NEWEST_FILE_AGE_MIN=$((NEWEST_FILE_AGE / 60))
        NEWEST_FILE_NAME=$(basename "$NEWEST_FILE")
        
        # Check if new files have been created
        if [ "$CURRENT_FILE_COUNT" -gt "$LAST_FILE_COUNT" ]; then
            log "Progress: $CURRENT_FILE_COUNT files found ($((CURRENT_FILE_COUNT - LAST_FILE_COUNT)) new). Latest: $NEWEST_FILE_NAME (${NEWEST_FILE_AGE_MIN}m ago)"
            LAST_FILE_COUNT=$CURRENT_FILE_COUNT
            STUCK_COUNTER=0
        elif [ "$NEWEST_FILE_TIME" -gt "$LAST_MODIFIED_TIME" ]; then
            log "Progress: Files updated. Latest modification: $NEWEST_FILE_NAME (${NEWEST_FILE_AGE_MIN}m ago)"
            LAST_MODIFIED_TIME=$NEWEST_FILE_TIME
            STUCK_COUNTER=0
        else
            STUCK_COUNTER=$((STUCK_COUNTER + 1))
            if [ "$STUCK_COUNTER" -ge "$STUCK_THRESHOLD" ]; then
                log "WARNING: No new files or updates in $STUCK_COUNTER minutes. Process might be stuck."
                log "CPU: ${CPU_USAGE}%, Memory: ${MEM_USAGE}%, Runtime: ${RUNTIME_FORMATTED}"
                log "Last file: $NEWEST_FILE_NAME (${NEWEST_FILE_AGE_MIN}m ago)"
                log "Process is still running. If you think it's stuck, press Ctrl+C to abort."
            fi
        fi
    else
        log "No data files found yet. Runtime: ${RUNTIME_FORMATTED}"
    fi
    
    # Every 5 minutes, show process stats regardless of file changes
    if [ "$((RUNTIME % 300))" -lt 60 ]; then
        log "Process stats - CPU: ${CPU_USAGE}%, Memory: ${MEM_USAGE}%, Runtime: ${RUNTIME_FORMATTED}"
    fi
    
    # Sleep for one minute
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