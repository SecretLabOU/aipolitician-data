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
import sys
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
        print(f"Requesting search results from: {search_url}")
        search_response = requests.get(search_url)
        search_data = search_response.json()
        
        print(f"Search response: {search_data}")
        
        if not search_data[3] or len(search_data[3]) == 0:
            print(f"No Wikipedia page found for {politician_name}")
            return None
            
        # Get the first result URL
        page_url = search_data[3][0]
        print(f"Found Wikipedia page: {page_url}")
        
        # Get the page title from the URL
        page_title = page_url.split('/')[-1].replace('_', ' ')
        print(f"Page title: {page_title}")
        
        # Get the content of the page using the Wikipedia API
        api_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts|pageimages|info&exintro=1&inprop=url&titles={urllib.parse.quote(page_title)}&format=json&explaintext=1"
        print(f"Requesting page content from: {api_url}")
        
        content_response = requests.get(api_url)
        content_data = content_response.json()
        
        # Extract the page content
        pages = content_data['query']['pages']
        if not pages:
            print("No page content found")
            return None
            
        page_id = list(pages.keys())[0]
        page_info = pages[page_id]
        
        # Check if page exists
        if 'missing' in page_info:
            print(f"Page {page_title} does not exist")
            return None
            
        # Extract basic information
        raw_content = page_info.get('extract', '')
        full_url = page_info.get('fullurl', page_url)
        
        print(f"Retrieved {len(raw_content)} characters of content")
        
        # Try to find political party affiliation using another API call
        party_url = f"https://en.wikipedia.org/w/api.php?action=parse&page={urllib.parse.quote(page_title)}&prop=text&section=0&format=json"
        print(f"Requesting infobox from: {party_url}")
        
        try:
            party_response = requests.get(party_url)
            party_data = party_response.json()
            
            # Extract political party from infobox if it exists
            if 'parse' in party_data and 'text' in party_data['parse']:
                html_content = party_data['parse']['text']['*']
                
                # Look for political party in the infobox
                party_match = re.search(r'Political party</th[^>]*><td[^>]*>(.*?)</td>', html_content)
                political_affiliation = ''
                
                if party_match:
                    # Clean up HTML tags
                    political_affiliation = clean_html(party_match.group(1))
                    print(f"Found political affiliation: {political_affiliation}")
                else:
                    print("Political affiliation not found in infobox")
            else:
                political_affiliation = ''
                print("Couldn't extract infobox data")
        except Exception as e:
            political_affiliation = ''
            print(f"Error extracting political party: {str(e)}")
        
        # Create a politician data object
        politician_data = {
            "id": generate_id_from_name(politician_name),
            "name": page_title,
            "source_url": full_url,
            "raw_content": raw_content,
            "political_affiliation": political_affiliation,
            "speeches": [],
            "statements": [],
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Try to extract some statements from the content
        # This is a very simple approach - just looking for quoted text
        quote_pattern = re.compile(r'"([^"]{10,})"')
        quotes = quote_pattern.findall(raw_content)
        
        if quotes:
            politician_data["statements"] = quotes[:5]  # Take up to 5 quotes
            print(f"Found {len(quotes)} potential statements/quotes")
        
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
    parser.add_argument('--verbose', '-v', action='store_true',
                        help="Show more detailed output")
    
    args = parser.parse_args()
    
    print(f"Starting simple data collection for {args.politician}...")
    
    # Check for requests module
    try:
        import requests
    except ImportError:
        print("Error: The 'requests' module is required for this script.")
        print("Please install it using: pip install requests")
        sys.exit(1)
    
    # Scrape Wikipedia
    politician_data = scrape_wikipedia(args.politician)
    
    if politician_data:
        # Save the data
        save_data(politician_data, args.politician)
        print("\nData collection completed successfully!")
        print(f"Fields collected: {', '.join(politician_data.keys())}")
        print(f"Content length: {len(politician_data.get('raw_content', ''))} characters")
        print(f"Statements found: {len(politician_data.get('statements', []))}")
    else:
        print("\nData collection failed. No information could be retrieved.")

if __name__ == "__main__":
    main() 