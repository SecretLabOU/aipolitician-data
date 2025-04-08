import scrapy
import re
from ..items import PoliticianItem

class WikipediaPoliticianSpider(scrapy.Spider):
    name = "wikipedia_politicians"
    allowed_domains = ["en.wikipedia.org"]
    
    def __init__(self, *args, **kwargs):
        super(WikipediaPoliticianSpider, self).__init__(*args, **kwargs)
        
        # Default politicians to scrape if none provided
        self.start_politicians = kwargs.get('politicians', [
            "Joe Biden",
            "Donald Trump",
            "Kamala Harris",
            "Bernie Sanders",
            "Alexandria Ocasio-Cortez"
        ])
    
    def start_requests(self):
        for politician in self.start_politicians:
            search_url = f"https://en.wikipedia.org/wiki/{politician.replace(' ', '_')}"
            yield scrapy.Request(
                url=search_url,
                callback=self.parse_politician,
                meta={"politician_name": politician}
            )
    
    def parse_politician(self, response):
        politician_name = response.meta.get("politician_name")
        item = PoliticianItem()
        
        # Basic info
        item["name"] = politician_name
        item["source_url"] = response.url
        item["source_type"] = "wikipedia"
        
        # Biography - using the first few paragraphs from the main content
        paragraphs = response.css("#mw-content-text .mw-parser-output > p:not(.mw-empty-elt)").getall()
        if paragraphs:
            # Join the first few paragraphs to form a biography
            biography = " ".join([self.clean_html(p) for p in paragraphs[:3]])
            item["biography"] = biography
        
        # Try to extract political affiliation
        info_box = response.css(".infobox")
        if info_box:
            # Political party
            party_row = info_box.xpath(".//th[contains(text(), 'Political party')]/following-sibling::td[1]")
            if party_row:
                item["political_affiliation"] = self.clean_html(" ".join(party_row.css("::text").getall()))
            
            # Birth date
            birth_date_row = info_box.xpath(".//th[contains(text(), 'Born')]/following-sibling::td[1]")
            if birth_date_row:
                birth_date_text = self.clean_html(" ".join(birth_date_row.css("::text").getall()))
                # Try to extract date in a cleaner format
                date_match = re.search(r'(\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{1,2},\s+\d{4})', birth_date_text)
                if date_match:
                    item["birth_date"] = date_match.group(1)
                else:
                    item["birth_date"] = birth_date_text
            
            # Birth place
            if birth_date_row:
                birth_place_text = self.clean_html(" ".join(birth_date_row.css("::text").getall()))
                # Try to extract location after the date
                place_match = re.search(r'(?:in|at)\s+(.*?)(?:\(|$)', birth_place_text)
                if place_match:
                    item["birth_place"] = place_match.group(1).strip()
        
        # Try to get image URL
        image_element = info_box.css(".image img")
        if image_element:
            img_src = image_element.css("::attr(src)").get()
            if img_src:
                if img_src.startswith("//"):
                    item["image_url"] = "https:" + img_src
                else:
                    item["image_url"] = img_src
        
        # Extract education information
        education_section = response.xpath("//span[@id='Education' or @id='Early_life_and_education']/parent::*/following-sibling::p")
        if education_section:
            education_text = " ".join([self.clean_html(p.get()) for p in education_section[:3]])
            item["education"] = education_text
        
        # Extract positions from the "Political positions" section if it exists
        positions_section = response.xpath("//span[@id='Political_positions']/parent::*/following-sibling::*")
        if positions_section:
            positions_text = []
            for i, element in enumerate(positions_section[:10]):  # Limit to first 10 elements
                if element.root.tag in ["p", "ul"]:
                    positions_text.append(self.clean_html(element.get()))
                elif element.root.tag == "h2":  # Stop at the next section heading
                    break
            if positions_text:
                item["positions"] = " ".join(positions_text)
        
        yield item
    
    def clean_html(self, html_text):
        """Clean HTML content by removing tags and extra whitespace"""
        if not html_text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html_text)
        
        # Remove citation references [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip() 