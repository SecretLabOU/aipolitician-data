BOT_NAME = "politician_scraper"

SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 16

# Configure a delay for requests for the same website (default: 0)
DOWNLOAD_DELAY = 1

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Configure item pipelines
ITEM_PIPELINES = {
    "scraper.pipelines.PoliticianPipeline": 300,
}

# Configure logging level - set to DEBUG for more detailed output
LOG_LEVEL = 'DEBUG'

# Use absolute path for data directory
import os
from pathlib import Path
DATA_DIR = Path(__file__).resolve().parents[2] / 'data'
# Create the data directory if it doesn't exist
DATA_DIR.mkdir(exist_ok=True)

# Configure output directory for scraped files
FILES_STORE = str(DATA_DIR)

# Save items directly to JSON files
FEEDS = {
    str(DATA_DIR / '%(name)s_%(time)s.json'): {
        'format': 'json',
        'encoding': 'utf8',
        'store_empty': False,
        'fields': None,
        'indent': 4,
    },
}

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8" 