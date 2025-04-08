#!/usr/bin/env python3
# scripts/run_pipeline.py
"""
Automated script to run the full data pipeline:
1. Set up Chroma DB (or check if it exists)
2. Ingest all data files in the data directory
3. Run a test query to verify everything is working
"""

import os
import sys
import glob
import subprocess
import argparse
from datetime import datetime

# Get the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the project root directory (parent of scripts)
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
# Default data directory
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the full data pipeline.")
    parser.add_argument("--reset", action="store_true",
                        help="Reset the database before ingestion")
    parser.add_argument("--data-dir", type=str, default=DATA_DIR,
                        help=f"Directory containing JSON data files (default: {DATA_DIR})")
    parser.add_argument("--pattern", type=str, default="*.json",
                        help="File pattern to match for ingestion (default: *.json)")
    parser.add_argument("--exclude", type=str, nargs="+", default=["sample_politician.json"],
                        help="Files to exclude from ingestion (default: sample_politician.json)")
    parser.add_argument("--test-query", type=str, default="What are their views on economy?",
                        help="Test query to run after ingestion")
    return parser.parse_args()

def run_command(cmd, description):
    """Run a command and print its output."""
    print(f"\n=== {description} ===")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Errors: {result.stderr}")
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

def setup_chroma():
    """Set up the Chroma database."""
    cmd = [sys.executable, os.path.join(SCRIPT_DIR, "setup_chroma.py")]
    return run_command(cmd, "Setting up Chroma DB")

def diagnose_chroma():
    """Run diagnostics on the Chroma database."""
    cmd = [sys.executable, os.path.join(SCRIPT_DIR, "diagnose_chroma.py")]
    return run_command(cmd, "Running Chroma diagnostics")

def ingest_data_files(data_files):
    """Ingest all specified data files."""
    if not data_files:
        print("No data files to ingest.")
        return False
    
    cmd = [sys.executable, os.path.join(SCRIPT_DIR, "ingest_data.py")] + data_files
    return run_command(cmd, f"Ingesting {len(data_files)} data files")

def test_query(query_text):
    """Run a test query to verify ingestion."""
    cmd = [
        sys.executable, 
        os.path.join(SCRIPT_DIR, "query_data.py"),
        "--query", query_text,
        "--results", "3"
    ]
    return run_command(cmd, f"Testing query: '{query_text}'")

def main():
    """Run the full pipeline."""
    args = parse_arguments()
    
    print(f"=== Starting data pipeline at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    # Step 1: Set up or check Chroma
    if args.reset:
        print("\nNote: Database reset requested. Running diagnostics first...")
        diagnose_chroma()
    
    # Step 2: Set up Chroma
    if not setup_chroma():
        print("Failed to set up Chroma. Aborting pipeline.")
        sys.exit(1)
    
    # Step 3: Find and filter data files
    data_dir = os.path.abspath(args.data_dir)
    file_pattern = os.path.join(data_dir, args.pattern)
    data_files = glob.glob(file_pattern)
    
    # Filter out excluded files
    exclude_files = set(args.exclude)
    filtered_files = [f for f in data_files if os.path.basename(f) not in exclude_files]
    
    if not filtered_files:
        print(f"No data files found matching pattern '{args.pattern}' in {data_dir}")
        print(f"(excluding {', '.join(exclude_files)})")
        sys.exit(1)
    
    print(f"\nFound {len(filtered_files)} data files to process:")
    for file in filtered_files:
        print(f"  - {file}")
    
    # Step 4: Ingest data
    if not ingest_data_files(filtered_files):
        print("Data ingestion failed. Aborting pipeline.")
        sys.exit(1)
    
    # Step 5: Test query
    if not test_query(args.test_query):
        print("Test query failed. Check the Chroma database.")
        sys.exit(1)
    
    print(f"\n=== Pipeline completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    print("To query the database, you can run:")
    print(f"python {os.path.join(SCRIPT_DIR, 'query_data.py')} --query \"YOUR QUERY HERE\"")
    print("Additional options: --politician \"Name\", --type \"speech\", --results 5")

if __name__ == "__main__":
    main() 