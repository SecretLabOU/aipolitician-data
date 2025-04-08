#!/usr/bin/env python
"""
Runner script for the political data scraper.
This script provides a simple command-line interface to run the scrapers.

Usage:
    python run.py --politician "Politician Name" [--api-key NEWS_API_KEY]
"""

import argparse
import subprocess
import os
import sys
import time
import json
from pathlib import Path

def check_dependencies():
    """Check if all required packages are installed."""
    missing_packages = []
    
    # Check for required packages
    try:
        import scrapy
    except ImportError:
        missing_packages.append("scrapy")
    
    try:
        import numpy
    except ImportError:
        missing_packages.append("numpy")
    
    try:
        import requests
    except ImportError:
        missing_packages.append("requests")
    
    # Try to import spacy, but it's optional (fallback available)
    try:
        import spacy
        has_spacy = True
    except ImportError:
        has_spacy = False
        missing_packages.append("spacy (optional)")
    
    # If spacy is available, check for language model
    if has_spacy:
        try:
            spacy.load("en_core_web_sm")
        except OSError:
            missing_packages.append("spacy language model (en_core_web_sm)")
    
    if missing_packages:
        print("Warning: Some dependencies are missing:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nTo install missing dependencies, run:")
        print("  pip install -r requirements.txt")
        print("  python -m spacy download en_core_web_sm")
        
        # If critical packages are missing, ask to continue
        if any(p for p in missing_packages if "optional" not in p):
            choice = input("\nContinue anyway? [y/N]: ")
            if choice.lower() != 'y':
                print("Exiting.")
                sys.exit(1)
    
    return True

def validate_data(file_path):
    """Validate that the JSON file has the expected structure."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        required_fields = ['id', 'name']
        for field in required_fields:
            if field not in data:
                print(f"Warning: Required field '{field}' missing from data")
                return False
                
        return True
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {file_path}")
        return False
    except Exception as e:
        print(f"Error validating data: {str(e)}")
        return False

def merge_data_files(politician_name):
    """
    Merge multiple data files for the same politician into a single file.
    """
    # Get the project root directory
    root_dir = Path(__file__).resolve().parent.parent
    data_dir = root_dir / 'data'
    
    # Get all files that might be related to this politician
    # Create a simplified name for matching
    simplified_name = politician_name.lower().replace(' ', '-')
    matching_files = list(data_dir.glob(f"*{simplified_name}*.json"))
    
    if not matching_files:
        print(f"No data files found for {politician_name}")
        return False
        
    # If only one file, no need to merge
    if len(matching_files) == 1:
        print(f"Only one data file found, no need to merge: {matching_files[0].name}")
        return validate_data(matching_files[0])
    
    # We need to merge multiple files
    print(f"Found {len(matching_files)} data files to merge")
    
    # Load all data
    data_objects = []
    for file_path in matching_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data_objects.append(data)
                print(f"Loaded {file_path.name}")
        except Exception as e:
            print(f"Error loading {file_path.name}: {str(e)}")
    
    if not data_objects:
        print("No valid data files to merge")
        return False
    
    # Use the first file as the base
    merged_data = data_objects[0]
    
    # Merge in data from other files
    for data in data_objects[1:]:
        # Merge speeches
        if 'speeches' in data and data['speeches']:
            if 'speeches' not in merged_data:
                merged_data['speeches'] = []
            merged_data['speeches'].extend(data['speeches'])
            
        # Merge statements
        if 'statements' in data and data['statements']:
            if 'statements' not in merged_data:
                merged_data['statements'] = []
            merged_data['statements'].extend(data['statements'])
            
        # For other fields, only copy if missing in the merged data
        for key, value in data.items():
            if key not in merged_data and value:
                merged_data[key] = value
    
    # Create a clean output file with the politician's name
    output_filename = f"{simplified_name}.json"
    output_path = data_dir / output_filename
    
    # Save the merged data
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
        
    print(f"Merged data saved to {output_path}")
    
    # Clean up the individual files
    for file_path in matching_files:
        try:
            if file_path.name != output_filename:
                file_path.unlink()
                print(f"Deleted {file_path.name}")
        except Exception as e:
            print(f"Error deleting {file_path.name}: {str(e)}")
    
    return validate_data(output_path)

def run_spider(spider_name, args, script_dir):
    """Run a spider with proper error handling."""
    try:
        cmd = ["scrapy", "crawl", spider_name] + args
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=script_dir, capture_output=True, text=True)
        
        # Print the output
        if result.stdout:
            print(result.stdout)
        
        # Check for errors
        if result.returncode != 0:
            print(f"Error running {spider_name} spider:")
            if result.stderr:
                print(result.stderr)
            return False
        
        return True
    except Exception as e:
        print(f"Failed to run {spider_name} spider: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Political Data Scraper")
    parser.add_argument('--politician', type=str, required=True, 
                        help="Name of the politician to scrape data for")
    parser.add_argument('--api-key', type=str, 
                        help="NewsAPI API key (optional)")
    parser.add_argument('--check-only', action='store_true',
                        help="Only check dependencies, don't run scrapers")
    parser.add_argument('--no-news', action='store_true',
                        help="Skip the news API spider")
    
    args = parser.parse_args()
    
    # Check dependencies first
    check_dependencies()
    
    if args.check_only:
        print("Dependency check completed. Exiting.")
        return
    
    # Get the directory of the script
    script_dir = Path(__file__).resolve().parent
    
    # Ensure we're in the correct directory
    os.chdir(script_dir)
    
    print(f"Starting data collection for {args.politician}...")
    
    # Run the Wikipedia spider
    print("\n1. Running Wikipedia scraper...")
    wiki_args = ["-a", f"politician_name={args.politician}"]
    success = run_spider("wikipedia_politician", wiki_args, script_dir)
    
    if not success:
        print("Wikipedia scraper failed. Continuing with other scrapers...")
    
    # Run the News API spider if requested
    if not args.no_news:
        print("\n2. Running News API scraper...")
        news_args = ["-a", f"politician_name={args.politician}"]
        if args.api_key:
            news_args.extend(["-a", f"api_key={args.api_key}"])
        
        success = run_spider("news_api", news_args, script_dir)
        
        if not success:
            print("News API scraper failed.")
    else:
        print("\n2. Skipping News API scraper as requested.")
    
    # Allow time for any file operations to complete
    time.sleep(1)
    
    # Merge the data files if multiple files were created
    print("\n3. Processing and merging data...")
    if merge_data_files(args.politician):
        print("\nData collection completed successfully!")
    else:
        print("\nWarning: Data collection completed with some issues.")

if __name__ == "__main__":
    main() 