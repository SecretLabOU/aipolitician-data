import scrapy
import re
import urllib.parse
from scrapy.exceptions import CloseSpider
from ..items import PoliticianItem

class WikipediaPoliticianSpider(scrapy.Spider):
    name = "wikipedia_politician"
    allowed_domains = ["en.wikipedia.org"]
    
    def __init__(self, politician_name=None, follow_links=True, max_links=5, *args, **kwargs):
        super(WikipediaPoliticianSpider, self).__init__(*args, **kwargs)
        
        if not politician_name:
            raise CloseSpider("Politician name is required. Use -a politician_name='Name'")
        
        # Convert follow_links to boolean
        self.follow_links = str(follow_links).lower() in ['true', '1', 't', 'y', 'yes']
        
        # Convert max_links to int
        try:
            self.max_links = int(max_links)
        except (ValueError, TypeError):
            self.max_links = 5
            
        # Format the name for URL
        self.politician_name = politician_name
        query = urllib.parse.quote(politician_name)
        self.start_urls = [f"https://en.wikipedia.org/wiki/Special:Search?search={query}&go=Go"]
        self.logger.info(f"Starting search for: {politician_name}")
        self.logger.info(f"Start URL: {self.start_urls[0]}")
        self.logger.info(f"Follow links: {self.follow_links}, Max links: {self.max_links}")
        
        # Keep track of visited pages to avoid cycles
        self.visited_urls = set()
        
        # Store all collected data
        self.main_item = None
        self.all_speeches = []
        self.all_statements = []
        self.related_content = []
        self.links_followed = 0
    
    def parse(self, response):
        """
        Parse the search results page and follow the first result if available.
        """
        self.logger.info(f"Processing URL: {response.url}")
        self.visited_urls.add(response.url)
        
        # Check if we're already on a politician's page
        if response.url.startswith("https://en.wikipedia.org/wiki/") and "/Special:" not in response.url:
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
        
        # Create item on first page only
        if self.main_item is None:
            self.main_item = PoliticianItem()
            # Basic information
            title = response.css("h1#firstHeading::text").get()
            self.logger.info(f"Found page title: {title}")
            
            self.main_item['name'] = title
            self.main_item['source_url'] = response.url
            
            # Get the full name from the infobox if available
            full_name = response.css("table.infobox th:contains('Born') + td::text").get()
            if full_name:
                self.logger.info(f"Found full name: {full_name}")
                self.main_item['full_name'] = full_name.strip()
            else:
                self.logger.info(f"No full name found, using page title as full name")
                self.main_item['full_name'] = title
                
            # Extract birth date
            birth_date = response.css("table.infobox th:contains('Born') + td .bday::text").get()
            if birth_date:
                self.logger.info(f"Found birth date: {birth_date}")
                self.main_item['date_of_birth'] = birth_date
            else:
                self.logger.info("No birth date found")
                
            # Extract political party
            party = response.css("table.infobox th:contains('Political party') + td a::text").get()
            if party:
                self.logger.info(f"Found political party: {party}")
                self.main_item['political_affiliation'] = party
            else:
                self.logger.info("No political party found")
        
        # Get the main content from the current page
        content_paragraphs = response.css("#mw-content-text .mw-parser-output > p").getall()
        if content_paragraphs:
            raw_content = "\n".join([self.clean_html(p) for p in content_paragraphs if p.strip()])
            self.related_content.append(raw_content)
            self.logger.info(f"Found raw content, length: {len(raw_content)} characters")
        else:
            self.logger.warning("No content paragraphs found")
        
        # Extract list items that might contain policy positions
        list_items = response.css("#mw-content-text .mw-parser-output > ul > li").getall()
        if list_items:
            for item in list_items:
                clean_item = self.clean_html(item)
                if clean_item and len(clean_item) > 20:  # Avoid tiny list items
                    self.all_statements.append(clean_item)
        
        # Extract speeches and statements
        quotes = response.css("blockquote").getall()
        for i, quote in enumerate(quotes):
            clean_quote = self.clean_html(quote)
            if clean_quote:
                if len(clean_quote.split()) > 30:  # Longer quotes might be speeches
                    self.all_speeches.append(clean_quote)
                    self.logger.info(f"Found speech #{i+1}, length: {len(clean_quote)} characters")
                else:
                    self.all_statements.append(clean_quote)
                    self.logger.info(f"Found statement #{i+1}, length: {len(clean_quote)} characters")
        
        # Also check for statement sections like "Political positions" or "Views"
        statement_sections = response.xpath('//span[@class="mw-headline" and contains(text(), "Position") or contains(text(), "View") or contains(text(), "Statement") or contains(text(), "Policy") or contains(text(), "Campaign") or contains(text(), "Platform")]/parent::*/following-sibling::p')
        for i, section in enumerate(statement_sections):
            clean_text = self.clean_html(section.get())
            if clean_text:
                self.all_statements.append(clean_text)
                self.logger.info(f"Found position statement #{i+1}, length: {len(clean_text)} characters")
        
        # Follow links to related pages if enabled
        if self.follow_links and self.links_followed < self.max_links:
            # Find relevant links to follow
            # Look specifically for links that might contain political information
            relevant_sections = [
                "Political positions", "Political views", "Presidency",
                "Policy", "Campaign", "Electoral history", "Political career",
                "Senate career", "Governorship", "Foreign policy", "Domestic policy"
            ]
            
            # Build XPath to find links in sections with these titles
            xpath_queries = []
            for section in relevant_sections:
                xpath_queries.append(f'//span[@class="mw-headline" and contains(text(), "{section}")]/parent::*/following-sibling::*/descendant::a[starts-with(@href, "/wiki/")]/@href')
            
            # Also look for links in the "See also" section
            xpath_queries.append('//span[@class="mw-headline" and text()="See also"]/parent::*/following-sibling::ul/li/a[starts-with(@href, "/wiki/")]/@href')
            
            # Combine all the XPath queries
            related_links = []
            for query in xpath_queries:
                links = response.xpath(query).getall()
                if links:
                    related_links.extend(links)
            
            # Make the list unique and filter out unwanted links
            related_links = list(set(related_links))
            filtered_links = []
            for link in related_links:
                full_url = response.urljoin(link)
                if full_url not in self.visited_urls and not any(x in link for x in [':', 'File:', 'Category:', 'Help:', 'Wikipedia:']):
                    filtered_links.append(link)
            
            # Follow a limited number of the most relevant links
            for link in filtered_links[:self.max_links - self.links_followed]:
                self.links_followed += 1
                self.logger.info(f"Following related link {self.links_followed}: {link}")
                yield response.follow(link, self.parse_related_page)
            
        # Final yield if this was the main page or if we've followed all links
        if response.url == self.main_item['source_url'] or (self.follow_links and self.links_followed >= self.max_links):
            # Add all collected content to the main item
            if self.related_content:
                self.main_item['raw_content'] = "\n\n".join(self.related_content)
            
            if self.all_speeches:
                self.main_item['speeches'] = self.all_speeches
                self.logger.info(f"Total speeches found: {len(self.all_speeches)}")
            else:
                self.logger.info("No speeches found")
            
            if self.all_statements:
                self.main_item['statements'] = self.all_statements
                self.logger.info(f"Total statements found: {len(self.all_statements)}")
            else:
                self.logger.info("No statements found")
            
            # Log the complete item
            self.logger.info(f"Created item with fields: {self.main_item.keys()}")
            
            # Debug if there's no data
            if not self.main_item.get('raw_content') and not self.main_item.get('speeches') and not self.main_item.get('statements'):
                self.logger.warning("Warning: No significant content extracted from the page")
            
            yield self.main_item
    
    def parse_related_page(self, response):
        """Parse related pages and extract additional content."""
        self.logger.info(f"Parsing related page: {response.url}")
        self.visited_urls.add(response.url)
        
        # Extract content from the page
        title = response.css("h1#firstHeading::text").get()
        self.logger.info(f"Related page title: {title}")
        
        # Get the main content
        content_paragraphs = response.css("#mw-content-text .mw-parser-output > p").getall()
        if content_paragraphs:
            raw_content = "\n".join([self.clean_html(p) for p in content_paragraphs if p.strip()])
            # Add a header to identify the source
            self.related_content.append(f"From related article '{title}':\n{raw_content}")
            self.logger.info(f"Found related content, length: {len(raw_content)} characters")
        
        # Extract speeches and statements
        quotes = response.css("blockquote").getall()
        for i, quote in enumerate(quotes):
            clean_quote = self.clean_html(quote)
            if clean_quote:
                source_prefix = f"[From '{title}'] "
                if len(clean_quote.split()) > 30:
                    self.all_speeches.append(source_prefix + clean_quote)
                else:
                    self.all_statements.append(source_prefix + clean_quote)
        
        # Also look for policy positions and statements
        statement_sections = response.xpath('//span[@class="mw-headline" and contains(text(), "Position") or contains(text(), "View") or contains(text(), "Statement") or contains(text(), "Policy")]/parent::*/following-sibling::p')
        for section in statement_sections:
            clean_text = self.clean_html(section.get())
            if clean_text:
                self.all_statements.append(f"[From '{title}'] {clean_text}")
        
        # We always return to the main parse function for final processing
    
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