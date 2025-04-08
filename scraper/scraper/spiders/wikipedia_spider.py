import re
import scrapy
import logging
import wikipediaapi
from urllib.parse import urlparse, unquote
from ..items import PoliticianItem

class WikipediaSpider(scrapy.Spider):
    """
    Spider for scraping politician data from Wikipedia.
    
    This spider extracts:
    - Biographical information
    - Political career details
    - Speeches (when available)
    - Statements/quotes
    """
    name = 'wikipedia'
    
    def __init__(self, politician=None, follow_links=True, max_links=5, *args, **kwargs):
        super(WikipediaSpider, self).__init__(*args, **kwargs)
        
        if not politician:
            raise ValueError("Politician name is required")
            
        self.politician = politician
        self.follow_links = str(follow_links).lower() == 'true'
        self.max_links = int(max_links)
        
        # Configure logging
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)
        
        # Initialize Wikipedia API
        self.wiki = wikipediaapi.Wikipedia('en')
        
        # Politician item that will be built as we scrape
        self.politician_item = PoliticianItem()
        self.politician_item['name'] = politician
        self.politician_item['speeches'] = []
        self.politician_item['statements'] = []
        self.politician_item['links'] = []
        
        # Track visited pages to avoid loops
        self.visited_pages = set()
        
    def start_requests(self):
        """Start by searching for the politician on Wikipedia."""
        # Convert spaces to underscores for Wikipedia URLs
        wiki_title = self.politician.replace(' ', '_')
        url = f'https://en.wikipedia.org/wiki/{wiki_title}'
        
        # Start the crawl
        yield scrapy.Request(url=url, callback=self.parse_politician_page)
        
    def parse_politician_page(self, response):
        """Extract information from the politician's main Wikipedia page."""
        url_path = urlparse(response.url).path
        page_title = unquote(url_path.split('/')[-1]).replace('_', ' ')
        
        self.logger.info(f"Processing Wikipedia page: {page_title}")
        
        # Skip if we've already visited this page
        if page_title in self.visited_pages:
            return
            
        self.visited_pages.add(page_title)
        
        # Set source URL if this is the main page
        if not self.politician_item.get('source_url'):
            self.politician_item['source_url'] = response.url
        
        # Extract text content from main article
        main_content = response.css('#mw-content-text .mw-parser-output')
        
        # Extract the first paragraph as a summary
        first_para = main_content.css('p:not(.mw-empty-elt)::text').getall()
        first_para = ' '.join([p.strip() for p in first_para if p.strip()])
        
        # If this is the main page, capture the full content
        if not self.politician_item.get('raw_content'):
            # Combine all paragraphs as raw content
            paragraphs = main_content.css('p:not(.mw-empty-elt)::text, p:not(.mw-empty-elt) *::text').getall()
            raw_content = ' '.join([p.strip() for p in paragraphs if p.strip()])
            self.politician_item['raw_content'] = raw_content
            
            # Try to extract birth date
            birth_date = self.extract_birth_date(response)
            if birth_date:
                self.politician_item['date_of_birth'] = birth_date
                
            # Try to extract political affiliation
            affiliation = self.extract_political_affiliation(response)
            if affiliation:
                self.politician_item['political_affiliation'] = affiliation
        
        # Extract statements/quotes (often in blockquotes or with quotation marks)
        quotes = main_content.css('blockquote::text, blockquote *::text').getall()
        quotes = [q.strip() for q in quotes if q.strip()]
        
        # Also look for text in quotation marks
        text_content = ' '.join(main_content.css('p::text, p *::text').getall())
        quoted_text = re.findall(r'"([^"]*)"', text_content)
        quoted_text += re.findall(r'"([^"]*)"', text_content)
        quoted_text += re.findall(r"'([^']*)'", text_content)
        
        # Add found quotes to statements
        for quote in quotes + quoted_text:
            if len(quote) > 20 and quote not in self.politician_item['statements']:
                self.politician_item['statements'].append(quote)
        
        # Extract speeches (often in separate sections)
        speech_headings = main_content.css('h2 span#Speeches, h3 span#Speeches, h2 span#Notable_speeches, h3 span#Notable_speeches')
        if speech_headings:
            # Find the section containing speeches
            for heading in speech_headings:
                section = heading.xpath('./parent::*/following-sibling::*')
                for elem in section:
                    if elem.root.tag == 'p':
                        speech_text = ' '.join(elem.css('::text').getall()).strip()
                        if speech_text and len(speech_text) > 50:
                            self.politician_item['speeches'].append(speech_text)
                    elif elem.root.tag in ['h2', 'h3', 'h4']:
                        # Stop when we hit the next heading
                        break
        
        # Follow links to related pages if enabled
        if self.follow_links and len(self.visited_pages) <= self.max_links:
            # Look for links to pages about speeches, statements, politics, etc.
            relevant_terms = ['speech', 'statement', 'address', 'political position', 
                             'policy', 'platform', 'presidency', 'administration']
                             
            # Find links that might contain relevant information
            links = main_content.css('a[href^="/wiki/"]')
            
            for link in links:
                link_text = link.css('::text').get('').lower()
                link_href = link.attrib.get('href', '')
                
                # Skip links to files, categories, help pages
                if any(x in link_href for x in ['/File:', '/Category:', '/Help:', '/Wikipedia:']):
                    continue
                    
                # Follow link if it contains relevant terms
                if any(term in link_text.lower() for term in relevant_terms) and link_href.startswith('/wiki/'):
                    full_url = response.urljoin(link_href)
                    
                    # Only follow if we haven't visited this page yet
                    page_name = unquote(link_href.split('/')[-1]).replace('_', ' ')
                    if page_name not in self.visited_pages:
                        self.politician_item['links'].append(full_url)
                        yield scrapy.Request(full_url, callback=self.parse_politician_page)
        
        # Return the constructed item
        return self.politician_item
    
    def extract_birth_date(self, response):
        """Extract birth date from the Wikipedia page."""
        # Try different patterns for birth date
        # Pattern 1: Infobox
        birth_date = response.css('.infobox .bday::text').get()
        if birth_date:
            return birth_date
            
        # Pattern 2: Regular text in first paragraphs
        first_paras = ' '.join(response.css('p:not(.mw-empty-elt)::text').getall()[:3])
        date_match = re.search(r'born (\w+ \d+, \d{4})', first_paras)
        if date_match:
            # Convert to YYYY-MM-DD format if possible
            try:
                from datetime import datetime
                date_obj = datetime.strptime(date_match.group(1), '%B %d, %Y')
                return date_obj.strftime('%Y-%m-%d')
            except:
                return date_match.group(1)
                
        return None
        
    def extract_political_affiliation(self, response):
        """Extract political party affiliation from the Wikipedia page."""
        # Try to find political party in infobox
        party_label = response.css('.infobox th:contains("Political party"), .infobox th:contains("Party")')
        if party_label:
            party = party_label.xpath('./following-sibling::td[1]//text()').getall()
            party = ' '.join([p.strip() for p in party if p.strip()])
            return party
            
        # Try to find in text
        first_paras = ' '.join(response.css('p:not(.mw-empty-elt)::text').getall()[:5])
        party_match = re.search(r'(Democratic Party|Republican Party|Democratic|Republican|Independent)', first_paras)
        if party_match:
            return party_match.group(1)
            
        return None 