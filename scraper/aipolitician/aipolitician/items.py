import scrapy


class PoliticianItem(scrapy.Item):
    # Basic information
    id = scrapy.Field()
    name = scrapy.Field()
    source_url = scrapy.Field()
    source_type = scrapy.Field()
    
    # Content fields
    biography = scrapy.Field()
    political_affiliation = scrapy.Field()
    positions = scrapy.Field()
    achievements = scrapy.Field()
    controversies = scrapy.Field()
    speeches = scrapy.Field()
    policies = scrapy.Field()
    news_articles = scrapy.Field()
    quotes = scrapy.Field()
    
    # Optional additional fields
    birth_date = scrapy.Field()
    birth_place = scrapy.Field()
    image_url = scrapy.Field()
    social_media = scrapy.Field()
    education = scrapy.Field()
    career = scrapy.Field()
    
    # Metadata
    scraped_at = scrapy.Field()
    last_updated = scrapy.Field() 