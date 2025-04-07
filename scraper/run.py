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

def main():
    parser = argparse.ArgumentParser(description="Political Data Scraper")
    parser.add_argument('--politician', type=str, required=True, 
                        help="Name of the politician to scrape data for")
    parser.add_argument('--api-key', type=str, 
                        help="NewsAPI API key (optional)")
    
    args = parser.parse_args()
    
    # Get the directory of the script
    script_dir = Path(__file__).resolve().parent
    
    # Ensure we're in the correct directory
    os.chdir(script_dir)
    
    print(f"Starting data collection for {args.politician}...")
    
    # Run the Wikipedia spider
    print("\n1. Running Wikipedia scraper...")
    subprocess.run([
        "scrapy", "crawl", "wikipedia_politician",
        "-a", f"politician_name={args.politician}"
    ], cwd=script_dir)
    
    # Run the News API spider if API key provided
    print("\n2. Running News API scraper...")
    news_cmd = ["scrapy", "crawl", "news_api", "-a", f"politician_name={args.politician}"]
    if args.api_key:
        news_cmd.extend(["-a", f"api_key={args.api_key}"])
    subprocess.run(news_cmd, cwd=script_dir)
    
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