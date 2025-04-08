#!/usr/bin/env python3
"""
Main runner script for the AI Politician data scraper.

This script:
1. Parses command-line arguments
2. Checks dependencies
3. Runs the appropriate spiders
"""

import os
import sys
import argparse
import subprocess
import importlib.util
from datetime import datetime

# Constants
DEFAULT_MAX_PAGES = 10
DEFAULT_TIME_SPAN = 365  # days
DEFAULT_MAX_LINKS = 5

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='AI Politician Data Scraper')
    
    # Required arguments
    parser.add_argument('--politician', '-p', required=True,
                        help='Name of the politician to scrape data for')
    
    # Optional arguments
    parser.add_argument('--api-key', '-k',
                        help='NewsAPI key (will use from .env if not provided)')
    parser.add_argument('--check-only', action='store_true',
                        help='Only check dependencies, don\'t run scrapers')
    parser.add_argument('--no-news', action='store_true',
                        help='Skip the NewsAPI spider')
    parser.add_argument('--max-pages', type=int, default=DEFAULT_MAX_PAGES,
                        help=f'Maximum number of news pages to fetch (default: {DEFAULT_MAX_PAGES})')
    parser.add_argument('--time-span', type=int, default=DEFAULT_TIME_SPAN,
                        help=f'Time span in days to fetch news for (default: {DEFAULT_TIME_SPAN})')
    parser.add_argument('--follow-links', type=str, default='true',
                        help='Follow links from Wikipedia to related pages (default: true)')
    parser.add_argument('--max-links', type=int, default=DEFAULT_MAX_LINKS,
                        help=f'Maximum number of related links to follow (default: {DEFAULT_MAX_LINKS})')
    parser.add_argument('--comprehensive', action='store_true',
                        help='Use maximum settings for comprehensive data collection')
    parser.add_argument('--simple', action='store_true',
                        help='Use simple scraper script instead of Scrapy spiders')
    
    return parser.parse_args()

def check_dependencies():
    """Check if required dependencies are installed."""
    print("Checking dependencies...")
    
    missing_deps = []
    optional_deps = []
    
    # Check core dependencies
    for package in ['requests']:
        if not importlib.util.find_spec(package):
            missing_deps.append(package)
    
    # Check for Scrapy (needed for full scraper)
    if not importlib.util.find_spec('scrapy'):
        optional_deps.append('scrapy')
    
    # Check for NewsAPI (needed for News API spider)
    if not importlib.util.find_spec('newsapi'):
        optional_deps.append('newsapi-python')
    
    # Check for dotenv (needed for API key management)
    if not importlib.util.find_spec('dotenv'):
        optional_deps.append('python-dotenv')
    
    # Check for Wikipedia API
    if not importlib.util.find_spec('wikipediaapi'):
        optional_deps.append('wikipedia-api')
    
    # Check for spaCy (used for better text processing)
    spacy_available = importlib.util.find_spec('spacy') is not None
    if not spacy_available:
        optional_deps.append('spacy')
    
    # Print results
    if missing_deps:
        print("Error: Missing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPlease install them with: pip install " + " ".join(missing_deps))
        sys.exit(1)
    
    if optional_deps:
        print("Warning: Some optional dependencies are missing:")
        for dep in optional_deps:
            print(f"  - {dep}")
        print("\nYou can still use the simple scraper, but for full functionality, install:")
        print("pip install " + " ".join(optional_deps))
        print("\nTo use the simple scraper, pass the --simple flag")
    
    if not missing_deps and not optional_deps:
        print("All dependencies are installed.")
    
    return bool(optional_deps)

def adjust_args_for_comprehensive(args):
    """Adjust arguments if comprehensive mode is enabled."""
    if args.comprehensive:
        print("Comprehensive mode enabled. Using maximum settings.")
        args.max_pages = 100
        args.time_span = 3650  # 10 years
        args.follow_links = 'true'
        args.max_links = 10
    
    return args

def run_scrapy_spider(spider_name, politician, **kwargs):
    """Run a Scrapy spider with the given arguments."""
    print(f"\nRunning {spider_name} spider for '{politician}'...")
    
    # Build the Scrapy command
    cmd = [
        'scrapy', 'crawl', spider_name,
        '-a', f'politician={politician}'
    ]
    
    # Add additional arguments
    for key, value in kwargs.items():
        if value is not None:
            cmd.extend(['-a', f'{key}={value}'])
    
    # Run the command
    try:
        subprocess.run(cmd, check=True, cwd=os.path.join(os.path.dirname(__file__), 'scraper'))
        print(f"{spider_name} completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {spider_name}: {e}")
        return False
    except FileNotFoundError:
        print(f"Error: scrapy command not found. Make sure Scrapy is installed.")
        return False

def run_simple_scraper(politician, output_dir="../data", skip_news=False):
    """Run the simplified scraper script."""
    print(f"\nRunning simple scraper for '{politician}'...")
    
    cmd = [
        sys.executable, 'simple_scrape.py',
        '--politician', politician,
        '--output-dir', output_dir
    ]
    
    if skip_news:
        cmd.append('--skip-news')
    
    try:
        subprocess.run(cmd, check=True, cwd=os.path.dirname(__file__))
        print("Simple scraper completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running simple scraper: {e}")
        return False

def main():
    """Main entry point for the scraper."""
    args = parse_arguments()
    
    print(f"=== AI Politician Data Scraper ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Politician: {args.politician}")
    
    # Check dependencies
    missing_optional_deps = check_dependencies()
    
    # Exit if check-only mode
    if args.check_only:
        print("Dependency check completed. Exiting.")
        return
    
    # If missing optional dependencies, suggest using the simple scraper
    if missing_optional_deps and not args.simple:
        print("\nWould you like to use the simple scraper instead? (y/n)")
        choice = input().lower()
        if choice.startswith('y'):
            args.simple = True
    
    # Adjust arguments for comprehensive mode
    args = adjust_args_for_comprehensive(args)
    
    # Run the appropriate scraper
    if args.simple:
        success = run_simple_scraper(
            args.politician,
            skip_news=args.no_news
        )
    else:
        # Run Wikipedia spider
        wiki_success = run_scrapy_spider(
            'wikipedia',
            args.politician,
            follow_links=args.follow_links,
            max_links=args.max_links
        )
        
        # Run News API spider if not disabled
        news_success = True
        if not args.no_news:
            news_success = run_scrapy_spider(
                'newsapi',
                args.politician,
                api_key=args.api_key,
                max_pages=args.max_pages,
                time_span=args.time_span
            )
        
        success = wiki_success and (news_success or args.no_news)
    
    # Print completion message
    print(f"\n=== Scraping completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    if success:
        print("All data collected successfully!")
        print("\nNext Steps:")
        print("1. Check the data directory for the generated JSON files")
        print("2. Run the ingestion script: python ../scripts/ingest_data.py ../data/*.json")
        print("3. Query the data: python ../scripts/query_data.py")
    else:
        print("There were some errors during data collection.")
        print("Check the messages above for details.")

if __name__ == "__main__":
    main() 