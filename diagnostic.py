#!/usr/bin/env python
"""
Diagnostic script for the political data scraper.
This will check for common issues and help debug problems.
"""

import os
import sys
from pathlib import Path
import json

def check_environment():
    """Check the Python environment and dependencies"""
    print("=== Python Environment ===")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    
    # Check for .env file
    root_dir = Path().resolve()
    env_path = root_dir / '.env'
    if env_path.exists():
        print(f".env file found at: {env_path}")
        
        # Check .env file content without displaying API key
        with open(env_path, 'r') as f:
            content = f.read().strip()
            lines = content.split('\n')
            for line in lines:
                if line and not line.startswith('#'):
                    # Don't show actual API key, just indicate it exists
                    if 'API_KEY' in line:
                        key_name = line.split('=')[0].strip()
                        print(f"Found key in .env: {key_name}=********")
                    else:
                        print(f"Found in .env: {line}")
    else:
        print("No .env file found in root directory")
        
        # Check in scraper directory
        scraper_env = root_dir / 'scraper' / '.env'
        if scraper_env.exists():
            print(f".env file found at: {scraper_env}")
        else:
            print("No .env file found in scraper directory either")
    
    # Check for data directory
    data_dir = root_dir / 'data'
    if data_dir.exists() and data_dir.is_dir():
        print(f"Data directory found at: {data_dir}")
        
        # Check for any JSON files
        json_files = list(data_dir.glob('*.json'))
        if json_files:
            print(f"Found {len(json_files)} JSON files in data directory:")
            for file in json_files:
                print(f"  - {file.name}")
        else:
            print("No JSON files found in data directory")
    else:
        print("Data directory not found, will need to be created")
    
    # Check for spaCy
    try:
        import spacy
        print(f"spaCy is installed (version: {spacy.__version__})")
        
        # Check for spaCy models
        try:
            nlp = spacy.load("en_core_web_sm")
            print("en_core_web_sm model is available")
        except OSError:
            print("en_core_web_sm model is NOT available")
    except ImportError:
        print("spaCy is NOT installed or not found in PYTHONPATH")
    
    # Check for other dependencies
    for module in ["scrapy", "requests", "dotenv"]:
        try:
            __import__(module)
            print(f"{module} is installed")
        except ImportError:
            print(f"{module} is NOT installed")

def test_simple_scrape():
    """Test simple scraper functionality"""
    print("\n=== Testing Simple Scrape ===")
    
    try:
        import requests
        print("Testing Wikipedia API access...")
        
        # Test access to Wikipedia API
        response = requests.get("https://en.wikipedia.org/w/api.php?action=opensearch&search=test&limit=1&format=json")
        if response.status_code == 200:
            print(f"Wikipedia API is accessible (status: {response.status_code})")
        else:
            print(f"Wikipedia API returned status: {response.status_code}")
    except Exception as e:
        print(f"Error testing Wikipedia API: {str(e)}")
    
    # Test NewsAPI access if key available
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('NEWS_API_KEY')
        
        if api_key:
            print("Testing NewsAPI access with key from .env...")
            url = f"https://newsapi.org/v2/everything?q=test&pageSize=1&apiKey={api_key}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    print("NewsAPI is accessible and API key is valid")
                else:
                    print(f"NewsAPI error: {data.get('message', 'Unknown error')}")
            else:
                print(f"NewsAPI returned status: {response.status_code}")
        else:
            print("No NewsAPI key found in environment variables")
    except Exception as e:
        print(f"Error testing NewsAPI: {str(e)}")

def main():
    print("=== Scraper Diagnostic Tool ===")
    print("This tool will check for common issues with the political data scraper\n")
    
    check_environment()
    test_simple_scrape()
    
    print("\n=== Diagnostic Complete ===")
    print("If you're experiencing issues, try the following fixes:")
    print("1. For spaCy issues, make sure to run: python -m spacy download en_core_web_sm")
    print("2. For NewsAPI issues, check your .env file has NEWS_API_KEY=yourkeyhere")
    print("3. For 'No data files found', check file permissions in the data directory")
    print("4. Try the simple_scrape.py directly: python scraper/simple_scrape.py --politician \"Kamala Harris\"")

if __name__ == "__main__":
    main()
