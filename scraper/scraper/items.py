import scrapy

class PoliticianItem(scrapy.Item):
    """Item for storing politician data"""
    id = scrapy.Field()
    name = scrapy.Field()
    full_name = scrapy.Field()
    source_url = scrapy.Field()
    date_of_birth = scrapy.Field() 
    political_affiliation = scrapy.Field()
    raw_content = scrapy.Field()
    speeches = scrapy.Field()
    statements = scrapy.Field()
    timestamp = scrapy.Field() 