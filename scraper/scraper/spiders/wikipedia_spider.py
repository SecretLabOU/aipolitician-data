import scrapy
import re
import urllib.parse
from scrapy.exceptions import CloseSpider
from ..items import PoliticianItem

class WikipediaPoliticianSpider(scrapy.Spider):
    name = "wikipedia_politician"
    allowed_domains = ["en.wikipedia.org"]
    
    def __init__(self, politician_name=None, *args, **kwargs):
        super(WikipediaPoliticianSpider, self).__init__(*args, **kwargs)
        
        if not politician_name:
            raise CloseSpider("Politician name is required. Use -a politician_name='Name'")
        
        # Format the name for URL
        self.politician_name = politician_name
        query = urllib.parse.quote(politician_name)
        self.start_urls = [f"https://en.wikipedia.org/wiki/Special:Search?search={query}&go=Go"]
    
    def parse(self, response):
        """
        Parse the search results page and follow the first result if available.
        """
        # Check if we're already on a politician's page
        if response.url.startswith("https://en.wikipedia.org/wiki/") and not "/Special:" in response.url:
            return self.parse_politician_page(response)
            
        # Check for direct hit or search results
        first_result = response.css(".mw-search-result-heading a::attr(href)").get()
        
        if first_result:
            # Follow the first search result
            yield response.follow(first_result, self.parse_politician_page)
        else:
            # Check if we were redirected to the politician's page
            title = response.css("h1#firstHeading::text").get()
            if title:
                return self.parse_politician_page(response)
            else:
                self.logger.error(f"No results found for {self.politician_name}")
    
    def parse_politician_page(self, response):
        """Parse the politician's Wikipedia page."""
        self.logger.info(f"Parsing politician page: {response.url}")
        
        item = PoliticianItem()
        
        # Basic information
        item['name'] = response.css("h1#firstHeading::text").get()
        item['source_url'] = response.url
        
        # Get the full name from the infobox if available
        item['full_name'] = response.css("table.infobox th:contains('Born') + td::text").get()
        if not item['full_name']:
            item['full_name'] = item['name']
            
        # Extract birth date
        birth_date = response.css("table.infobox th:contains('Born') + td .bday::text").get()
        if birth_date:
            item['date_of_birth'] = birth_date
            
        # Extract political party
        party = response.css("table.infobox th:contains('Political party') + td a::text").get()
        if party:
            item['political_affiliation'] = party
            
        # Get the main content
        content_paragraphs = response.css("#mw-content-text .mw-parser-output > p").getall()
        if content_paragraphs:
            raw_content = "\n".join([self.clean_html(p) for p in content_paragraphs if p.strip()])
            item['raw_content'] = raw_content
        
        # Extract speeches and statements (this is a simplified version)
        # For real use, you would need more sophisticated extraction or additional sources
        speeches = []
        statements = []
        
        # Look for quotes in the page that might be statements
        quotes = response.css("blockquote").getall()
        for quote in quotes:
            clean_quote = self.clean_html(quote)
            if clean_quote:
                if len(clean_quote.split()) > 30:  # Longer quotes might be speeches
                    speeches.append(clean_quote)
                else:
                    statements.append(clean_quote)
        
        # Also check for statement sections like "Political positions" or "Views"
        statement_sections = response.xpath('//span[@class="mw-headline" and contains(text(), "Position") or contains(text(), "View") or contains(text(), "Statement")]/parent::*/following-sibling::p')
        for section in statement_sections:
            clean_text = self.clean_html(section.get())
            if clean_text:
                statements.append(clean_text)
        
        if speeches:
            item['speeches'] = speeches
        
        if statements:
            item['statements'] = statements
        
        return item
    
    def clean_html(self, html_text):
        """Remove HTML tags and clean the text."""
        if not html_text:
            return ""
            
        # Basic HTML tag removal (in a real implementation, use a proper HTML parser)
        text = re.sub(r'<[^>]+>', ' ', html_text)
        
        # Remove citation brackets like [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip() 