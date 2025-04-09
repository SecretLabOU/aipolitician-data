#!/bin/bash

# ============================================================================
# Politician Data Pipeline Setup Script
# ============================================================================

# ===== COLORS FOR TERMINAL OUTPUT =====
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ===== SYMBOLS =====
CHECK="✅"
CROSS="❌"
ARROW="➤"
INFO="ℹ️"
WARN="⚠️"
STAR="⭐"

# ===== CONFIGURATION =====
# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
CONDA_ENV_NAME="aipolitician"
PYTHON_VERSION="3.10"
DB_DIR="/opt/chroma_db"

# ===== HELPER FUNCTIONS =====
print_header() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}${STAR} $1${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

print_step() {
    echo ""
    echo -e "${CYAN}${ARROW} $1${NC}"
}

print_success() {
    echo -e "${GREEN}${CHECK} $1${NC}"
}

print_error() {
    echo -e "${RED}${CROSS} $1${NC}"
    if [ "$2" == "exit" ]; then
        exit 1
    fi
}

print_warning() {
    echo -e "${YELLOW}${WARN} $1${NC}"
}

print_info() {
    echo -e "${PURPLE}${INFO} $1${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    case "$(uname -s)" in
        Linux*)     echo "linux";;
        Darwin*)    echo "macos";;
        CYGWIN*)    echo "windows";;
        MINGW*)     echo "windows";;
        *)          echo "unknown";;
    esac
}

# Check for Chrome/Chromium on Linux
check_chrome_linux() {
    local os_type=$(detect_os)
    
    if [ "$os_type" == "linux" ]; then
        print_step "Checking for Chrome/Chromium (required for Selenium)"
        
        if command_exists google-chrome || command_exists chromium-browser || command_exists chromium; then
            print_success "Chrome/Chromium is installed"
        else
            print_warning "Chrome/Chromium not found. Selenium will need a browser to work properly."
            print_info "On Ubuntu/Debian: sudo apt install chromium-browser"
            print_info "On CentOS/RHEL: sudo yum install chromium"
            print_info "On Arch Linux: sudo pacman -S chromium"
            print_info "You can also download Chrome from https://www.google.com/chrome/"
        fi
    fi
}

# ===== ARGUMENT CHECKING =====
if [ $# -lt 1 ]; then
    print_error "Please provide a politician name. Usage: $0 \"Politician Name\"" "exit"
fi

POLITICIAN_NAME="$1"
print_header "Setting up data pipeline for politician: $POLITICIAN_NAME"

# ===== CHECK CONDA INSTALLATION =====
print_step "Checking for Conda installation"

if command_exists conda; then
    print_success "Conda is installed"
else
    print_error "Conda is not installed. Please install Conda before running this script." "exit"
fi

# ===== CONDA ENVIRONMENT SETUP =====
print_step "Setting up Conda environment '$CONDA_ENV_NAME'"

# Check if environment exists
if conda env list | grep -q "$CONDA_ENV_NAME"; then
    print_info "Conda environment '$CONDA_ENV_NAME' already exists"
else
    # Check if environment.yml exists and use it, otherwise create with Python version only
    if [ -f "$SCRIPT_DIR/environment.yml" ]; then
        print_info "Creating Conda environment from environment.yml"
        conda env create -f "$SCRIPT_DIR/environment.yml"
    else
        print_info "Creating new Conda environment with Python $PYTHON_VERSION"
        conda create -y -n "$CONDA_ENV_NAME" python=$PYTHON_VERSION
    fi
    
    if [ $? -ne 0 ]; then
        print_error "Failed to create Conda environment" "exit"
    fi
    print_success "Created Conda environment '$CONDA_ENV_NAME'"
fi

# ===== ACTIVATE CONDA ENVIRONMENT =====
print_step "Activating Conda environment"
# shellcheck disable=SC1091
eval "$(conda shell.bash hook)"
conda activate "$CONDA_ENV_NAME"

if [ $? -ne 0 ]; then
    print_error "Failed to activate Conda environment" "exit"
fi
print_success "Activated Conda environment '$CONDA_ENV_NAME'"

# Check for Chrome/Chromium on Linux
check_chrome_linux

# ===== INSTALL DEPENDENCIES =====
print_step "Installing required dependencies"

# Create temporary folder for logs
mkdir -p "$SCRIPT_DIR/logs"
LOG_FILE="$SCRIPT_DIR/logs/dependencies_$(date +%Y%m%d_%H%M%S).log"

print_info "Installing core dependencies (details logged to $LOG_FILE)"
python -m pip install --upgrade pip >> "$LOG_FILE" 2>&1

# If environment.yml was not used, install from requirements.txt
if [ ! -f "$SCRIPT_DIR/environment.yml" ] || [ "$2" == "--force-requirements" ]; then
    print_info "Installing from requirements.txt"
    pip install -r "$SCRIPT_DIR/requirements.txt" >> "$LOG_FILE" 2>&1
fi

if [ $? -ne 0 ]; then
    print_error "Failed to install dependencies. Check $LOG_FILE for details" "exit"
fi
print_success "Core dependencies installed successfully"

# Download nltk data
print_info "Downloading NLTK resources"
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')" >> "$LOG_FILE" 2>&1

# Download spaCy model
print_info "Downloading spaCy model"
python -m spacy download en_core_web_sm >> "$LOG_FILE" 2>&1

print_success "All dependencies installed successfully"

# ===== PREPARE DATABASE =====
print_step "Setting up Chroma database"

# Check if database directory exists
if [ -d "$DB_DIR" ]; then
    print_info "Database directory already exists at $DB_DIR"
else
    print_info "Attempting to create database directory at $DB_DIR"
    # Try to create the directory (might need sudo)
    if mkdir -p "$DB_DIR" 2>/dev/null; then
        print_success "Created database directory at $DB_DIR"
    else
        print_error "Could not create $DB_DIR. You may need sudo privileges."
        print_info "Please run: sudo mkdir -p $DB_DIR && sudo chown $USER:$USER $DB_DIR"
        print_warning "Continuing with setup, but Chroma database operations may fail"
    fi
fi

# Check permissions on database directory
if [ -d "$DB_DIR" ]; then
    if [ ! -w "$DB_DIR" ] || [ ! -r "$DB_DIR" ]; then
        print_error "Missing permissions on $DB_DIR"
        print_info "Please run: sudo chown $USER:$USER $DB_DIR"
        print_info "And: sudo chmod 755 $DB_DIR"
        print_warning "Continuing with setup, but Chroma database operations may fail"
    fi
fi

# Run Chroma setup
print_info "Running Chroma database setup script"
python "$SCRIPT_DIR/scripts/chroma_setup.py"

if [ $? -ne 0 ]; then
    print_error "Failed to setup Chroma database"
    print_warning "Continuing anyway, but there may be issues later"
else
    print_success "Chroma database setup complete"
fi

# ===== SCRAPE POLITICIAN DATA =====
print_step "Scraping data for $POLITICIAN_NAME"

# Create data directories if they don't exist
mkdir -p "$SCRIPT_DIR/data/politicians"
mkdir -p "$SCRIPT_DIR/data/formatted"

# Check if the politician data already exists
EXISTING_FILE=$(find "$SCRIPT_DIR/data/politicians" -name "*.json" -exec grep -l "$POLITICIAN_NAME" {} \; | head -n 1)

if [ -n "$EXISTING_FILE" ] && [ "$2" != "--force-scrape" ]; then
    print_info "Found existing data for $POLITICIAN_NAME at: $EXISTING_FILE"
    print_info "Skipping scraping step. Use --force-scrape to scrape anyway."
    SCRAPED_FILE="$EXISTING_FILE"
else
    print_info "Running scraper for $POLITICIAN_NAME (this may take a while)"
    python "$SCRIPT_DIR/scraper/politician_scraper.py" "$POLITICIAN_NAME"

    if [ $? -ne 0 ]; then
        print_error "Failed to scrape data for $POLITICIAN_NAME"
        print_warning "Continuing with data formatting in case partial data was collected"
    else
        print_success "Successfully scraped data for $POLITICIAN_NAME"
    fi

    # Find the scraped file
    SCRAPED_FILE=$(find "$SCRIPT_DIR/data/politicians" -name "*.json" -exec grep -l "$POLITICIAN_NAME" {} \; | head -n 1)

    if [ -z "$SCRAPED_FILE" ]; then
        print_error "No scraped data found for $POLITICIAN_NAME" "exit"
    fi
fi

print_info "Using scraped data from: $SCRAPED_FILE"

# ===== FORMAT DATA =====
print_step "Formatting scraped data"

# Check if formatted data already exists
EXISTING_FORMATTED=$(find "$SCRIPT_DIR/data/formatted" -name "formatted_*.json" -exec grep -l "$POLITICIAN_NAME" {} \; | head -n 1)

if [ -n "$EXISTING_FORMATTED" ] && [ "$2" != "--force-format" ]; then
    print_info "Found existing formatted data for $POLITICIAN_NAME at: $EXISTING_FORMATTED"
    print_info "Skipping formatting step. Use --force-format to reformat anyway."
    FORMATTED_FILE="$EXISTING_FORMATTED"
else
    print_info "Running data formatter"
    python "$SCRIPT_DIR/formatter/data_formatter.py" --single "$SCRAPED_FILE"

    if [ $? -ne 0 ]; then
        print_error "Failed to format data" "exit"
    fi

    # Find formatted file
    FORMATTED_FILE=$(find "$SCRIPT_DIR/data/formatted" -name "formatted_*.json" -exec grep -l "$POLITICIAN_NAME" {} \; | head -n 1)

    if [ -z "$FORMATTED_FILE" ]; then
        print_error "No formatted data found for $POLITICIAN_NAME" "exit"
    fi
    
    print_success "Successfully formatted data for $POLITICIAN_NAME"
fi

print_info "Using formatted data from: $FORMATTED_FILE"

# ===== LOAD DATA INTO CHROMA =====
print_step "Loading data into Chroma database"

print_info "Running data ingestion script"
python "$SCRIPT_DIR/scripts/ingest_data_patched.py" "$FORMATTED_FILE"

if [ $? -ne 0 ]; then
    print_error "Failed to ingest data into Chroma database" "exit"
fi

print_success "Successfully loaded $POLITICIAN_NAME data into Chroma database"

# ===== VERIFY WITH SIMPLE QUERY =====
print_step "Verifying data with a simple query"

print_info "Running test query..."
python "$SCRIPT_DIR/scripts/query_data_patched.py" --query "Tell me about $POLITICIAN_NAME" --politician "$POLITICIAN_NAME" --results 2

if [ $? -ne 0 ]; then
    print_error "Query test failed" "exit"
fi

print_success "Data verification complete"

# ===== COMPLETION =====
print_header "Pipeline Completed Successfully"
print_info "Politician data for '$POLITICIAN_NAME' has been:"
print_info "1. Scraped from various online sources"
print_info "2. Formatted into a structured format"
print_info "3. Loaded into the Chroma vector database"
print_info ""
print_info "You can now query the data using:"
print_info "python scripts/query_data_patched.py --query \"Your question?\" --politician \"$POLITICIAN_NAME\""
print_info ""
print_info "To deactivate the Conda environment, run: conda deactivate"

# Deactivate conda environment
conda deactivate

exit 0 