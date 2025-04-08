# Scrapy settings for the AI Politician scraper

BOT_NAME = 'aipolitician'

SPIDER_MODULES = ['scraper.spiders']
NEWSPIDER_MODULE = 'scraper.spiders'

# Respect robots.txt
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 8

# Configure a delay for requests (in seconds)
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True

# Disable cookies
COOKIES_ENABLED = False

# Set the user agent
USER_AGENT = 'AI Politician Data Scraper (https://github.com/nataliehill/aipolitician-data)'

# Configure item pipelines
ITEM_PIPELINES = {
   'scraper.pipelines.PoliticianDataPipeline': 300,
}

# Enable and configure logging
LOG_LEVEL = 'INFO'

# Configure maximum depth for following links
DEPTH_LIMIT = 5 