#!/usr/bin/env python
"""
Simplified scraper for collecting politician data.
This version doesn't require spaCy or other advanced dependencies.

Usage:
    python simple_scrape.py --politician "Politician Name"
"""

import argparse
import requests
import json
import re
import datetime
import os
from pathlib import Path
import urllib.parse

def clean_html(html_text):
    """Simple function to remove HTML tags and clean text"""
    if not html_text:
        return ""
        
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html_text)
    
    # Remove citation brackets like [1], [2], etc.
    text = re.sub(r'\[\d+\]', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def scrape_wikipedia(politician_name):
    """Scrape basic information about a politician from Wikipedia"""
    print(f"Searching Wikipedia for: {politician_name}")
    
    # Format the name for URL
    query = urllib.parse.quote(politician_name)
    search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={query}&limit=1&format=json"
    
    try:
        # Search for the politician
        search_response = requests.get(search_url)
        search_data = search_response.json()
        
        if not search_data[3] or len(search_data[3]) == 0:
            print(f"No Wikipedia page found for {politician_name}")
            return None
            
        # Get the first result URL
        page_url = search_data[3][0]
        print(f"Found Wikipedia page: {page_url}")
        
        # Get the content of the page
        content_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&titles={page_url.split('/')[-1]}&format=json&explaintext"
        content_response = requests.get(content_url)
        content_data = content_response.json()
        
        # Extract the page content
        page_id = list(content_data['query']['pages'].keys())[0]
        raw_content = content_data['query']['pages'][page_id].get('extract', '')
        
        # Create a politician data object
        politician_data = {
            "id": generate_id_from_name(politician_name),
            "name": politician_name,
            "source_url": page_url,
            "raw_content": raw_content,
            "speeches": [],
            "statements": [],
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        return politician_data
    except Exception as e:
        print(f"Error scraping Wikipedia: {str(e)}")
        return None

def generate_id_from_name(name):
    """Generate a URL-friendly ID from the politician's name"""
    # Convert to lowercase and replace spaces with hyphens
    name_id = name.lower().replace(' ', '-')
    
    # Remove special characters
    name_id = re.sub(r'[^a-z0-9-]', '', name_id)
    
    # Add timestamp to ensure uniqueness
    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    return f"{name_id}-{timestamp}"

def save_data(data, politician_name):
    """Save the politician data to a JSON file"""
    # Get the project root directory and create data directory if needed
    root_dir = Path(__file__).resolve().parent.parent
    data_dir = root_dir / 'data'
    data_dir.mkdir(exist_ok=True)
    
    # Create a filename based on the politician's name
    simplified_name = politician_name.lower().replace(' ', '-')
    filename = f"{simplified_name}.json"
    filepath = data_dir / filename
    
    # Save the data to a file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Saved politician data to {filepath}")
    return filepath

def main():
    parser = argparse.ArgumentParser(description="Simple Political Data Scraper")
    parser.add_argument('--politician', type=str, required=True, 
                        help="Name of the politician to scrape data for")
    
    args = parser.parse_args()
    
    print(f"Starting simple data collection for {args.politician}...")
    
    # Scrape Wikipedia
    politician_data = scrape_wikipedia(args.politician)
    
    if politician_data:
        # Save the data
        save_data(politician_data, args.politician)
        print("\nData collection completed successfully!")
    else:
        print("\nData collection failed.")

if __name__ == "__main__":
    main() 