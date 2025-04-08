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
        self.logger.info(f"Starting search for: {politician_name}")
        self.logger.info(f"Start URL: {self.start_urls[0]}")
    
    def parse(self, response):
        """
        Parse the search results page and follow the first result if available.
        """
        self.logger.info(f"Processing URL: {response.url}")
        
        # Check if we're already on a politician's page
        if response.url.startswith("https://en.wikipedia.org/wiki/") and not "/Special:" in response.url:
            self.logger.info("Already on a Wikipedia article page")
            return self.parse_politician_page(response)
            
        # Check for direct hit or search results
        first_result = response.css(".mw-search-result-heading a::attr(href)").get()
        
        if first_result:
            # Follow the first search result
            self.logger.info(f"Found search result: {first_result}")
            yield response.follow(first_result, self.parse_politician_page)
        else:
            # Check if we were redirected to the politician's page
            title = response.css("h1#firstHeading::text").get()
            if title:
                self.logger.info(f"Redirected to page: {title}")
                return self.parse_politician_page(response)
            else:
                self.logger.error(f"No results found for {self.politician_name}")
                # Debug information about the page
                self.logger.debug(f"Page title: {response.css('title::text').get()}")
                self.logger.debug(f"Page content: {response.css('body').get()[:500]}...")
    
    def parse_politician_page(self, response):
        """Parse the politician's Wikipedia page."""
        self.logger.info(f"Parsing politician page: {response.url}")
        
        item = PoliticianItem()
        
        # Basic information
        title = response.css("h1#firstHeading::text").get()
        self.logger.info(f"Found page title: {title}")
        
        item['name'] = title
        item['source_url'] = response.url
        
        # Get the full name from the infobox if available
        full_name = response.css("table.infobox th:contains('Born') + td::text").get()
        if full_name:
            self.logger.info(f"Found full name: {full_name}")
            item['full_name'] = full_name.strip()
        else:
            self.logger.info(f"No full name found, using page title as full name")
            item['full_name'] = title
            
        # Extract birth date
        birth_date = response.css("table.infobox th:contains('Born') + td .bday::text").get()
        if birth_date:
            self.logger.info(f"Found birth date: {birth_date}")
            item['date_of_birth'] = birth_date
        else:
            self.logger.info("No birth date found")
            
        # Extract political party
        party = response.css("table.infobox th:contains('Political party') + td a::text").get()
        if party:
            self.logger.info(f"Found political party: {party}")
            item['political_affiliation'] = party
        else:
            self.logger.info("No political party found")
            
        # Get the main content
        content_paragraphs = response.css("#mw-content-text .mw-parser-output > p").getall()
        if content_paragraphs:
            raw_content = "\n".join([self.clean_html(p) for p in content_paragraphs if p.strip()])
            item['raw_content'] = raw_content
            self.logger.info(f"Found raw content, length: {len(raw_content)} characters")
        else:
            self.logger.warning("No content paragraphs found")
        
        # Extract speeches and statements (this is a simplified version)
        # For real use, you would need more sophisticated extraction or additional sources
        speeches = []
        statements = []
        
        # Look for quotes in the page that might be statements
        quotes = response.css("blockquote").getall()
        for i, quote in enumerate(quotes):
            clean_quote = self.clean_html(quote)
            if clean_quote:
                if len(clean_quote.split()) > 30:  # Longer quotes might be speeches
                    speeches.append(clean_quote)
                    self.logger.info(f"Found speech #{i+1}, length: {len(clean_quote)} characters")
                else:
                    statements.append(clean_quote)
                    self.logger.info(f"Found statement #{i+1}, length: {len(clean_quote)} characters")
        
        # Also check for statement sections like "Political positions" or "Views"
        statement_sections = response.xpath('//span[@class="mw-headline" and contains(text(), "Position") or contains(text(), "View") or contains(text(), "Statement")]/parent::*/following-sibling::p')
        for i, section in enumerate(statement_sections):
            clean_text = self.clean_html(section.get())
            if clean_text:
                statements.append(clean_text)
                self.logger.info(f"Found position statement #{i+1}, length: {len(clean_text)} characters")
        
        if speeches:
            item['speeches'] = speeches
            self.logger.info(f"Total speeches found: {len(speeches)}")
        else:
            self.logger.info("No speeches found")
        
        if statements:
            item['statements'] = statements
            self.logger.info(f"Total statements found: {len(statements)}")
        else:
            self.logger.info("No statements found")
        
        # Log the complete item
        self.logger.info(f"Created item with fields: {item.keys()}")
        
        # Debug if there's no data
        if not item.get('raw_content') and not item.get('speeches') and not item.get('statements'):
            self.logger.warning("Warning: No significant content extracted from the page")
        
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