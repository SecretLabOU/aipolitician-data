import os
import json
import scrapy
import logging
from datetime import datetime, timedelta
from newsapi import NewsApiClient
from dotenv import load_dotenv
from ..items import PoliticianItem

class NewsApiSpider(scrapy.Spider):
    """
    Spider for fetching news articles about politicians using the News API.
    
    This spider extracts:
    - Recent news articles
    - Quotes and statements from news sources
    - Headlines and summaries
    """
    name = 'newsapi'
    
    def __init__(self, politician=None, api_key=None, max_pages=10, time_span=365, *args, **kwargs):
        super(NewsApiSpider, self).__init__(*args, **kwargs)
        
        if not politician:
            raise ValueError("Politician name is required")
            
        self.politician = politician
        self.max_pages = int(max_pages)
        self.time_span = int(time_span)
        
        # Set up logging
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)
        
        # Load API key from arguments, environment, or .env file
        self.api_key = api_key
        if not self.api_key:
            # Try to load from environment or .env file
            load_dotenv()
            self.api_key = os.getenv('NEWS_API_KEY')
            
        if not self.api_key:
            self.logger.error("News API key is required. Provide it as an argument or set it in the .env file.")
            raise ValueError("News API key is required")
            
        # Initialize the News API client
        self.news_api = NewsApiClient(api_key=self.api_key)
        
        # Initialize the politician item
        self.politician_item = PoliticianItem()
        self.politician_item['name'] = politician
        self.politician_item['statements'] = []
        self.politician_item['source_url'] = f"https://newsapi.org/v2/everything?q={politician.replace(' ', '+')}"
        
        # Generate a unique ID for the news data
        timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S+00-00')
        self.politician_item['id'] = f"{politician.lower().replace(' ', '-')}-{datetime.now().strftime('%Y%m%d')}"
        
        # Store the timestamp
        self.politician_item['timestamp'] = datetime.now().isoformat()
        
    def start_requests(self):
        """Fetch news articles about the politician."""
        self.logger.info(f"Fetching news for politician: {self.politician}")
        
        # Calculate the date range (from days_ago to today)
        from_date = (datetime.now() - timedelta(days=self.time_span)).strftime('%Y-%m-%d')
        
        # We'll make a fake request to satisfy Scrapy's requirements
        # The actual API calls will be made in the callback
        url = f"https://newsapi.org/v2/everything?q={self.politician.replace(' ', '+')}&from={from_date}&sortBy=relevancy&apiKey={self.api_key}"
        
        # Make a fake request to pass to the callback
        yield scrapy.Request(url=url, callback=self.parse_news_api_response)
    
    def parse_news_api_response(self, response):
        """Process the News API response."""
        try:
            # This is where we actually call the News API
            # We're not using the response data from Scrapy
            from_date = (datetime.now() - timedelta(days=self.time_span)).strftime('%Y-%m-%d')
            
            # Get top headlines first (more relevant but fewer results)
            self.logger.info("Fetching top headlines...")
            top_headlines = self.news_api.get_top_headlines(
                q=self.politician,
                language='en'
            )
            
            # Process top headlines
            if top_headlines.get('status') == 'ok':
                self.process_articles(top_headlines.get('articles', []))
            
            # Then search for everything (more comprehensive)
            self.logger.info("Fetching all articles...")
            all_articles = self.news_api.get_everything(
                q=self.politician,
                from_param=from_date,
                language='en',
                sort_by='relevancy',
                page_size=100,
                page=1
            )
            
            # Process all articles
            if all_articles.get('status') == 'ok':
                total_results = all_articles.get('totalResults', 0)
                self.logger.info(f"Found {total_results} articles")
                
                # Process first page of results
                self.process_articles(all_articles.get('articles', []))
                
                # Get additional pages if needed and available
                max_pages = min(self.max_pages, (total_results // 100) + 1)
                
                for page in range(2, max_pages + 1):
                    self.logger.info(f"Fetching page {page} of {max_pages}...")
                    more_articles = self.news_api.get_everything(
                        q=self.politician,
                        from_param=from_date,
                        language='en',
                        sort_by='relevancy',
                        page_size=100,
                        page=page
                    )
                    
                    if more_articles.get('status') == 'ok':
                        self.process_articles(more_articles.get('articles', []))
                    else:
                        self.logger.warning(f"Failed to fetch page {page}: {more_articles.get('message', 'Unknown error')}")
                        break
            
            # Save the results for debugging
            self.save_debug_data(all_articles)
            
            # Return the item with collected statements
            return self.politician_item
            
        except Exception as e:
            self.logger.error(f"Error fetching news data: {str(e)}")
            # Still return the item with whatever data was collected
            return self.politician_item
    
    def process_articles(self, articles):
        """Extract statements from articles."""
        for article in articles:
            # Get the content from the article
            content = article.get('content', '')
            description = article.get('description', '')
            title = article.get('title', '')
            
            # Combine all text
            full_text = ' '.join([text for text in [title, description, content] if text])
            
            # If the content is substantial, add it as a statement
            if full_text and len(full_text) > 20:
                self.politician_item['statements'].append(full_text)
    
    def save_debug_data(self, data):
        """Save the API response for debugging purposes."""
        try:
            # Create a timestamp for the filename
            timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S+00-00')
            filename = f"news_api_{timestamp}.json"
            
            # Use the same directory as other data files
            file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                   'data', filename)
            
            # Save the data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
            self.logger.info(f"Saved debug data to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save debug data: {str(e)}") 