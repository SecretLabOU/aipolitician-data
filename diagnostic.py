#!/usr/bin/env python
"""
Diagnostic tool for the AI Politician data scraper.
This script checks common issues with the scraper setup and configuration.

Usage:
    python diagnostic.py
"""

import os
import sys
import json
import platform
from pathlib import Path
import importlib.util

def check_python_version():
    """Check Python version."""
    print("=== Python Environment ===")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    return True

def check_env_file():
    """Check for .env file and API key."""
    # Check in current directory and one level up
    env_paths = [
        Path('.env'),
        Path('../.env'),
        Path('scraper/.env')
    ]
    
    env_found = False
    for env_path in env_paths:
        if env_path.exists():
            print(f".env file found at: {env_path.resolve()}")
            env_found = True
            
            # Check if it contains the API key
            with open(env_path, 'r') as f:
                content = f.read()
                if 'NEWS_API_KEY' in content:
                    key_value = content.split('NEWS_API_KEY=')[1].split('\n')[0]
                    masked_key = '*' * len(key_value)
                    print(f"Found key in .env: NEWS_API_KEY={masked_key}")
                else:
                    print("Warning: No NEWS_API_KEY found in .env file")
    
    if not env_found:
        print("Warning: No .env file found")
    
    return env_found

def check_data_directory():
    """Check if data directory exists and has files."""
    data_paths = [
        Path('data'),
        Path('../data'),
        Path('scraper/data')
    ]
    
    data_dir = None
    for path in data_paths:
        if path.exists() and path.is_dir():
            data_dir = path
            break
    
    if data_dir:
        print(f"Data directory found at: {data_dir.resolve()}")
        json_files = list(data_dir.glob('*.json'))
        print(f"Found {len(json_files)} JSON files in data directory:")
        for file in json_files[:5]:  # Show up to 5 files
            print(f"  - {file.name}")
        if len(json_files) > 5:
            print(f"  - ...and {len(json_files) - 5} more")
        return True
    else:
        print("Warning: Data directory not found")
        return False

def check_dependencies():
    """Check if required packages are installed."""
    dependencies = {
        'spacy': {'required': False, 'version': None},
        'scrapy': {'required': True, 'version': None},
        'requests': {'required': True, 'version': None},
        'python-dotenv': {'required': True, 'version': None, 'import_name': 'dotenv'},
    }
    
    # Check each dependency
    for pkg, info in dependencies.items():
        import_name = info.get('import_name', pkg)
        spec = importlib.util.find_spec(import_name)
        if spec is not None:
            try:
                module = importlib.import_module(import_name)
                if hasattr(module, '__version__'):
                    info['version'] = module.__version__
                    print(f"{pkg} is installed (version: {info['version']})")
                else:
                    print(f"{pkg} is installed")
                info['installed'] = True
            except ImportError:
                info['installed'] = False
                if info['required']:
                    print(f"ERROR: {pkg} is required but could not be imported")
                else:
                    print(f"Warning: {pkg} is not available")
        else:
            info['installed'] = False
            if info['required']:
                print(f"ERROR: {pkg} is required but not installed")
            else:
                print(f"Warning: {pkg} is not installed")
    
    # Check spaCy model
    if dependencies['spacy']['installed']:
        try:
            import spacy
            model_name = "en_core_web_sm"
            try:
                spacy.load(model_name)
                print(f"{model_name} model is available")
            except OSError:
                print(f"Warning: {model_name} model is not available. Install with:")
                print(f"python -m spacy download {model_name}")
        except ImportError:
            pass
    
    return all(info['installed'] for pkg, info in dependencies.items() if info['required'])

def test_wikipedia_api():
    """Test access to Wikipedia API."""
    print("\n=== Testing Simple Scrape ===")
    print("Testing Wikipedia API access...")
    try:
        import requests
        response = requests.get("https://en.wikipedia.org/w/api.php?action=query&titles=Barack_Obama&format=json")
        if response.status_code == 200:
            print(f"Wikipedia API is accessible (status: {response.status_code})")
            return True
        else:
            print(f"Warning: Wikipedia API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"Error accessing Wikipedia API: {str(e)}")
        return False

def test_newsapi_access():
    """Test access to NewsAPI."""
    print("Testing NewsAPI access with key from .env...")
    
    # Find .env file
    env_paths = [
        Path('.env'),
        Path('../.env'),
        Path('scraper/.env')
    ]
    
    api_key = None
    for env_path in env_paths:
        if env_path.exists():
            with open(env_path, 'r') as f:
                content = f.read()
                if 'NEWS_API_KEY' in content:
                    api_key = content.split('NEWS_API_KEY=')[1].split('\n')[0]
                    break
    
    if not api_key:
        print("Warning: No NewsAPI key found in .env files")
        return False
    
    try:
        import requests
        url = f"https://newsapi.org/v2/everything?q=test&apiKey={api_key}&pageSize=1"
        response = requests.get(url)
        if response.status_code == 200:
            print("NewsAPI is accessible and API key is valid")
            return True
        else:
            print(f"Warning: NewsAPI returned status {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
    except Exception as e:
        print(f"Error accessing NewsAPI: {str(e)}")
        return False

def main():
    """Run all diagnostic checks."""
    print("=== Scraper Diagnostic Tool ===")
    print("This tool will check for common issues with the political data scraper")
    print("")
    
    # Check Python environment
    check_python_version()
    
    # Check .env file
    check_env_file()
    
    # Check data directory
    check_data_directory()
    
    # Check dependencies
    check_dependencies()
    
    # Test API access
    test_wikipedia_api()
    test_newsapi_access()
    
    print("\n=== Diagnostic Complete ===")
    print("If you're experiencing issues, try the following fixes:")
    print("1. For spaCy issues, make sure to run: python -m spacy download en_core_web_sm")
    print("2. For NewsAPI issues, check your .env file has NEWS_API_KEY=yourkeyhere")
    print("3. For 'No data files found', check file permissions in the data directory")
    print("4. Try the simple_scrape.py directly: python scraper/simple_scrape.py --politician \"Kamala Harris\"")

if __name__ == "__main__":
    main() 