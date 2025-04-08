# Define scraped items here
import scrapy

class PoliticianItem(scrapy.Item):
    # Basic information
    id = scrapy.Field()  # Unique identifier
    name = scrapy.Field()  # Politician name
    full_name = scrapy.Field()  # Full name if different
    date_of_birth = scrapy.Field()  # Birth date in YYYY-MM-DD format
    political_affiliation = scrapy.Field()  # Political party
    
    # Content fields
    raw_content = scrapy.Field()  # Main biographical content
    speeches = scrapy.Field()  # List of speeches
    statements = scrapy.Field()  # List of statements/quotes
    
    # Optional additional fields
    public_tweets = scrapy.Field()  # Twitter posts
    interviews = scrapy.Field()  # Interview text
    press_releases = scrapy.Field()  # Press releases
    voting_record = scrapy.Field()  # Voting history entries
    sponsored_bills = scrapy.Field()  # Bills sponsored
    
    # Metadata
    source_url = scrapy.Field()  # URL source of the data
    links = scrapy.Field()  # Related links
    timestamp = scrapy.Field()  # When this data was collected 