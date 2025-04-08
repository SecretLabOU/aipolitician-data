import scrapy
import json
import datetime
import os
from scrapy.exceptions import CloseSpider
from ..items import PoliticianItem
from dotenv import load_dotenv

class NewsApiSpider(scrapy.Spider):
    name = "news_api"
    
    def __init__(self, politician_name=None, api_key=None, *args, **kwargs):
        super(NewsApiSpider, self).__init__(*args, **kwargs)
        
        if not politician_name:
            raise CloseSpider("Politician name is required. Use -a politician_name='Name'")
        
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
        else:
            self.logger.warning("No API key provided. Using free limited NewsAPI access.")
            self.use_api = False
            
        # Format the query for news search
        self.politician_name = politician_name
        self.query = politician_name.replace(" ", "+")
        
        # Define start URLs based on availability of API key
        if self.use_api:
            # If we have an API key, use the NewsAPI
            # Limit to articles from the last month
            one_month_ago = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
            self.start_urls = [
                f"https://newsapi.org/v2/everything?q={self.query}&from={one_month_ago}&sortBy=relevancy&apiKey={self.api_key}"
            ]
        else:
            # If no API key, use a fallback to Google News
            self.start_urls = [
                f"https://news.google.com/search?q={self.query}"
            ]
    
    def parse(self, response):
        """Parse the news search results."""
        item = PoliticianItem()
        item['name'] = self.politician_name
        
        # Statements will contain excerpts from news articles
        statements = []
        
        if self.use_api:
            # Parse NewsAPI JSON response
            try:
                data = json.loads(response.text)
                if data.get('status') == 'ok':
                    articles = data.get('articles', [])
                    
                    for article in articles:
                        title = article.get('title', '')
                        description = article.get('description', '')
                        content = article.get('content', '')
                        
                        if description and len(description) > 10:
                            statements.append(description)
                        elif content and len(content) > 10:
                            # NewsAPI usually truncates content, but we'll use what we have
                            statements.append(content)
                else:
                    self.logger.error(f"NewsAPI error: {data.get('message')}")
            except json.JSONDecodeError:
                self.logger.error("Failed to parse NewsAPI response")
        else:
            # Parse Google News results
            articles = response.css("article")
            for article in articles:
                title = article.css("h3 a::text").get()
                snippet = article.css(".HO8did::text").get()
                
                if snippet and len(snippet) > 10:
                    statements.append(snippet)
        
        if statements:
            item['statements'] = statements
            item['source_url'] = self.start_urls[0]
            
            self.logger.info(f"Found {len(statements)} news statements about {self.politician_name}")
            return item
        else:
            self.logger.warning(f"No news statements found for {self.politician_name}")
            return None 