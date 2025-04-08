#!/usr/bin/env python3
"""
Simple politician data scraper

A lightweight alternative to the full scraper, with minimal dependencies.
This script only requires the requests library.
"""

import os
import re
import json
import argparse
import requests
from datetime import datetime
from urllib.parse import quote, urlparse

def setup_argparse():
    """Set up command line arguments."""
    parser = argparse.ArgumentParser(description='Simple politician data scraper')
    parser.add_argument('--politician', '-p', required=True, help='Name of the politician to scrape')
    parser.add_argument('--output-dir', '-o', default='../data', help='Directory to save output')
    parser.add_argument('--skip-news', action='store_true', help='Skip news search')
    
    return parser.parse_args()

def create_output_dir(output_dir):
    """Create output directory if it doesn't exist."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

def scrape_wikipedia(politician_name):
    """Scrape Wikipedia for politician information."""
    print(f"Scraping Wikipedia for: {politician_name}")
    
    # Format the name for Wikipedia URL
    wiki_name = quote(politician_name.replace(' ', '_'))
    url = f"https://en.wikipedia.org/wiki/{wiki_name}"
    
    try:
        response = requests.get(url, headers={'User-Agent': 'Simple Politician Scraper/1.0'})
        response.raise_for_status()  # Raise exception for 404s etc.
        
        html = response.text
        
        # Extract data using simple regex patterns (not as robust as BeautifulSoup but works for basic extraction)
        
        # Get main content
        main_content_match = re.search(r'<div id="mw-content-text".*?>(.*?)<div class="printfooter">', html, re.DOTALL)
        main_content = main_content_match.group(1) if main_content_match else ""
        
        # Clean HTML tags
        cleaned_content = re.sub(r'<.*?>', ' ', main_content)
        cleaned_content = re.sub(r'\s+', ' ', cleaned_content).strip()
        
        # Extract infobox info
        political_party = None
        party_match = re.search(r'Political party</th>.*?<td.*?>(.*?)</td>', html, re.DOTALL)
        if party_match:
            political_party = re.sub(r'<.*?>', '', party_match.group(1)).strip()
        
        # Extract birth date
        birth_date = None
        birth_match = re.search(r'Born</th>.*?<span class="bday">(\d{4}-\d{2}-\d{2})', html, re.DOTALL)
        if birth_match:
            birth_date = birth_match.group(1)
        
        # Extract quotes
        quotes = []
        quote_matches = re.findall(r'<blockquote.*?>(.*?)</blockquote>', html, re.DOTALL)
        for quote in quote_matches:
            cleaned_quote = re.sub(r'<.*?>', ' ', quote)
            cleaned_quote = re.sub(r'\s+', ' ', cleaned_quote).strip()
            if len(cleaned_quote) > 20:
                quotes.append(cleaned_quote)
        
        # Also extract quoted text in paragraphs
        paragraph_quotes = re.findall(r'"([^"]{20,})"', cleaned_content)
        quotes.extend(paragraph_quotes)
        
        return {
            "raw_content": cleaned_content[:10000],  # Limit length to avoid excessive data
            "political_affiliation": political_party,
            "date_of_birth": birth_date,
            "statements": quotes[:50],  # Limit to 50 quotes
            "source_url": url
        }
    
    except Exception as e:
        print(f"Error scraping Wikipedia: {e}")
        return {
            "raw_content": f"Error scraping Wikipedia: {e}",
            "source_url": url
        }

def scrape_news(politician_name, api_key=None):
    """Fetch recent news about the politician."""
    print(f"Searching for news about: {politician_name}")
    
    # Use News API if key is available
    if api_key:
        print("Using News API for better results")
        return scrape_with_news_api(politician_name, api_key)
    
    # Fallback to a simple Google News search
    print("News API key not provided, falling back to Google News")
    
    # Format for URL
    query = quote(politician_name)
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        xml = response.text
        
        # Extract titles and descriptions using regex
        titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', xml)
        
        # Skip the first title as it's usually the feed title
        news_statements = titles[1:21] if len(titles) > 1 else []
        
        return {
            "statements": news_statements,
            "source_url": f"https://news.google.com/search?q={query}"
        }
    
    except Exception as e:
        print(f"Error scraping news: {e}")
        return {
            "statements": [f"Error scraping news: {e}"],
            "source_url": url
        }

def scrape_with_news_api(politician_name, api_key):
    """Use the News API for better news results."""
    url = f"https://newsapi.org/v2/everything?q={quote(politician_name)}&language=en&sortBy=relevancy&apiKey={api_key}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') != 'ok':
            raise Exception(data.get('message', 'Unknown error'))
        
        # Extract article titles and descriptions
        articles = data.get('articles', [])
        statements = []
        
        for article in articles[:30]:  # Limit to first 30 articles
            title = article.get('title', '')
            description = article.get('description', '')
            
            if title and len(title) > 10:
                statements.append(title)
            if description and len(description) > 20:
                statements.append(description)
        
        return {
            "statements": statements,
            "source_url": url
        }
    
    except Exception as e:
        print(f"Error with News API: {e}")
        return {
            "statements": [f"Error with News API: {e}"],
            "source_url": url
        }

def main():
    """Main function to run the scraper."""
    # Parse command line arguments
    args = setup_argparse()
    
    # Create output directory
    create_output_dir(args.output_dir)
    
    # Generate a unique filename
    normalized_name = args.politician.lower().replace(' ', '-')
    timestamp = datetime.now().strftime('%Y%m%d')
    filename = f"{normalized_name}-{timestamp}.json"
    output_path = os.path.join(args.output_dir, filename)
    
    # Initialize the result dictionary
    result = {
        "id": f"{normalized_name}-{timestamp}",
        "name": args.politician,
        "timestamp": datetime.now().isoformat()
    }
    
    # Scrape Wikipedia
    wiki_data = scrape_wikipedia(args.politician)
    result.update(wiki_data)
    
    # Scrape news if not skipped
    if not args.skip_news:
        # Try to get API key from environment
        api_key = os.environ.get('NEWS_API_KEY')
        
        news_data = scrape_news(args.politician, api_key)
        
        # Merge statements from news with any existing statements
        if 'statements' not in result:
            result['statements'] = []
        
        result['statements'].extend(news_data.get('statements', []))
    
    # Save to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    print(f"Data saved to: {output_path}")
    print(f"Found {len(result.get('statements', []))} statements/quotes")
    print(f"Raw content length: {len(result.get('raw_content', ''))}")
    
    # Suggest next steps
    print("\nNext Steps:")
    print(f"1. Run the data ingestion script: python ../scripts/ingest_data.py {output_path}")
    print(f"2. Query the data: python ../scripts/query_data.py")
    
if __name__ == "__main__":
    main() 