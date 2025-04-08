import scrapy
import json
import datetime
import os
import time
from scrapy.exceptions import CloseSpider
from ..items import PoliticianItem
from dotenv import load_dotenv

class NewsApiSpider(scrapy.Spider):
    name = "news_api"
    
    def __init__(self, politician_name=None, api_key=None, max_pages=10, time_span=365, *args, **kwargs):
        super(NewsApiSpider, self).__init__(*args, **kwargs)
        
        if not politician_name:
            raise CloseSpider("Politician name is required. Use -a politician_name='Name'")
        
        # Convert max_pages to int if provided as string
        try:
            self.max_pages = int(max_pages)
        except (ValueError, TypeError):
            self.max_pages = 10  # Default to 10 pages
            
        # Convert time_span to int if provided as string
        try:
            self.time_span = int(time_span)
        except (ValueError, TypeError):
            self.time_span = 365  # Default to 1 year
        
        # Try to load API key from .env file if not provided as argument
        if not api_key:
            # Load environment variables from .env file
            try:
                # Look for .env in the project root directory
                env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
                load_dotenv(env_path)
                
                # Try to get the API key from environment variables
                api_key = os.getenv('NEWS_API_KEY')
                
                if api_key:
                    self.logger.info("Using API key from .env file")
                else:
                    self.logger.warning("No API key found in .env file. Using free limited NewsAPI access.")
            except Exception as e:
                self.logger.error(f"Error loading .env file: {str(e)}")
                api_key = None
        
        # Set API usage flag based on whether we have an API key
        if api_key:
            self.use_api = True
            self.api_key = api_key
            self.logger.info(f"Using NewsAPI with max pages: {self.max_pages}, time span: {self.time_span} days")
        else:
            self.logger.warning("No API key provided. Using free limited NewsAPI access.")
            self.use_api = False
            
        # Format the query for news search
        self.politician_name = politician_name
        self.query = politician_name.replace(" ", "+")
        
        # Store all collected statements
        self.all_statements = []
        self.current_page = 1
        
        # Define start URLs based on availability of API key
        if self.use_api:
            # If we have an API key, use the NewsAPI
            # Set a longer time span for more historical data
            self.start_date = (datetime.datetime.now() - datetime.timedelta(days=self.time_span)).strftime("%Y-%m-%d")
            self.start_urls = [
                f"https://newsapi.org/v2/everything?q={self.query}&from={self.start_date}&sortBy=relevancy&apiKey={self.api_key}&pageSize=100&page=1"
            ]
        else:
            # If no API key, use a fallback to Google News
            self.start_urls = [
                f"https://news.google.com/search?q={self.query}"
            ]
    
    def parse(self, response):
        """Parse the news search results."""
        if self.use_api:
            # Parse NewsAPI JSON response
            try:
                data = json.loads(response.text)
                if data.get('status') == 'ok':
                    articles = data.get('articles', [])
                    total_results = data.get('totalResults', 0)
                    
                    self.logger.info(f"Page {self.current_page}: Found {len(articles)} articles out of {total_results} total results")
                    
                    for article in articles:
                        title = article.get('title', '')
                        description = article.get('description', '')
                        content = article.get('content', '')
                        
                        # Collect both title and description for more data
                        if title and not title.endswith('...'):
                            self.all_statements.append(title)
                            
                        if description and len(description) > 10:
                            self.all_statements.append(description)
                        elif content and len(content) > 10:
                            # NewsAPI usually truncates content, but we'll use what we have
                            self.all_statements.append(content)
                    
                    # Check if we can fetch the next page
                    if self.current_page < self.max_pages and articles:
                        self.current_page += 1
                        next_page_url = f"https://newsapi.org/v2/everything?q={self.query}&from={self.start_date}&sortBy=relevancy&apiKey={self.api_key}&pageSize=100&page={self.current_page}"
                        
                        self.logger.info(f"Requesting next page: {self.current_page}")
                        # Add a small delay to avoid hitting rate limits
                        time.sleep(1)
                        yield scrapy.Request(next_page_url, callback=self.parse)
                    else:
                        # We've reached the maximum pages or no more articles
                        self.logger.info(f"Completed fetching {self.current_page} pages with {len(self.all_statements)} statements")
                        yield self.create_item()
                else:
                    self.logger.error(f"NewsAPI error: {data.get('message')}")
                    yield self.create_item()
            except json.JSONDecodeError:
                self.logger.error("Failed to parse NewsAPI response")
                yield self.create_item()
        else:
            # Parse Google News results
            articles = response.css("article")
            for article in articles:
                title = article.css("h3 a::text").get()
                snippet = article.css(".HO8did::text").get()
                
                if title:
                    self.all_statements.append(title)
                    
                if snippet and len(snippet) > 10:
                    self.all_statements.append(snippet)
            
            yield self.create_item()
    
    def create_item(self):
        """Create the final item with all collected statements."""
        item = PoliticianItem()
        item['name'] = self.politician_name
        
        if self.all_statements:
            # Remove duplicates while preserving order
            unique_statements = []
            seen = set()
            for statement in self.all_statements:
                if statement not in seen:
                    unique_statements.append(statement)
                    seen.add(statement)
            
            item['statements'] = unique_statements
            item['source_url'] = self.start_urls[0]
            
            self.logger.info(f"Found {len(unique_statements)} unique news statements about {self.politician_name}")
        else:
            self.logger.warning(f"No news statements found for {self.politician_name}")
            item['statements'] = []
            
        return item 