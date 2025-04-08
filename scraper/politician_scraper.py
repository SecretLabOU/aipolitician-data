#!/usr/bin/env python3
import argparse
import requests
from bs4 import BeautifulSoup
import wikipedia
import json
import os
from time import sleep
import logging
from urllib.parse import quote_plus
import re
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PoliticianScraper:
    def __init__(self, name):
        self.name = name
        self.data = {
            "name": name,
            "wikipedia": {},
            "news_articles": [],
            "social_media": {},
            "ballotpedia": {},
            "govinfo": {},
            "scraped_at": datetime.now().isoformat()
        }
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "politicians")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def scrape_all(self):
        """Run all scraping methods and save the data"""
        logger.info(f"Starting to scrape data for {self.name}")
        
        try:
            self.scrape_wikipedia()
        except Exception as e:
            logger.error(f"Error scraping Wikipedia: {e}")
        
        try:
            self.scrape_news()
        except Exception as e:
            logger.error(f"Error scraping news: {e}")
        
        try:
            self.scrape_ballotpedia()
        except Exception as e:
            logger.error(f"Error scraping Ballotpedia: {e}")
        
        try:
            self.scrape_social_media()
        except Exception as e:
            logger.error(f"Error scraping social media: {e}")
        
        self.save_data()
        logger.info(f"Completed scraping data for {self.name}")
        
    def scrape_wikipedia(self):
        """Scrape Wikipedia for information about the politician"""
        logger.info(f"Scraping Wikipedia for {self.name}")
        
        try:
            # Search for the politician's page
            search_results = wikipedia.search(f"{self.name} politician")
            
            if not search_results:
                logger.warning(f"No Wikipedia results found for {self.name}")
                return
            
            # Try to get the most relevant page
            try:
                page = wikipedia.page(search_results[0], auto_suggest=False)
            except wikipedia.DisambiguationError as e:
                # If disambiguation page, try to find the most relevant option
                politician_options = [opt for opt in e.options if 'politician' in opt.lower() or 'congress' in opt.lower() or 'senator' in opt.lower() or 'representative' in opt.lower()]
                if politician_options:
                    page = wikipedia.page(politician_options[0], auto_suggest=False)
                else:
                    page = wikipedia.page(e.options[0], auto_suggest=False)
            
            # Extract the content and basic information
            self.data["wikipedia"] = {
                "title": page.title,
                "url": page.url,
                "summary": page.summary,
                "content": page.content[:5000],  # Limit content to avoid huge data files
                "categories": page.categories,
                "references": page.references
            }
            
            # Get infobox data if available
            response = requests.get(page.url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                infobox = soup.find("table", {"class": "infobox"})
                
                if infobox:
                    infobox_data = {}
                    rows = infobox.find_all("tr")
                    for row in rows:
                        header = row.find("th")
                        value = row.find("td")
                        if header and value:
                            header_text = header.get_text().strip()
                            value_text = value.get_text().strip()
                            infobox_data[header_text] = value_text
                    
                    self.data["wikipedia"]["infobox"] = infobox_data
            
            logger.info(f"Successfully scraped Wikipedia for {self.name}")
            
        except Exception as e:
            logger.error(f"Error in Wikipedia scraping: {str(e)}")
            
    def scrape_news(self):
        """Scrape recent news articles about the politician using Google News"""
        logger.info(f"Scraping news for {self.name}")
        
        # Format name for URL
        query = quote_plus(f"{self.name} politician")
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'xml')
                items = soup.find_all('item')
                
                for item in items[:10]:  # Limit to 10 articles
                    try:
                        title = item.title.text
                        link = item.link.text
                        pub_date = item.pubDate.text
                        description = item.description.text if item.find('description') else ""
                        
                        self.data["news_articles"].append({
                            "title": title,
                            "url": link,
                            "published_date": pub_date,
                            "description": description
                        })
                    except Exception as e:
                        logger.error(f"Error parsing news item: {e}")
                
                logger.info(f"Found {len(self.data['news_articles'])} news articles for {self.name}")
            else:
                logger.warning(f"Failed to retrieve news: status code {response.status_code}")
        except Exception as e:
            logger.error(f"Error in news scraping: {str(e)}")
    
    def scrape_ballotpedia(self):
        """Scrape Ballotpedia for information"""
        logger.info(f"Scraping Ballotpedia for {self.name}")
        
        # Format name for URL (replace spaces with underscores)
        formatted_name = self.name.replace(" ", "_")
        url = f"https://ballotpedia.org/{formatted_name}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Get infobox data if available
                infobox = soup.find("table", {"class": "infobox"})
                
                if infobox:
                    infobox_data = {}
                    rows = infobox.find_all("tr")
                    for row in rows:
                        header = row.find("th")
                        value = row.find("td")
                        if header and value:
                            header_text = header.get_text().strip()
                            value_text = value.get_text().strip()
                            infobox_data[header_text] = value_text
                    
                    self.data["ballotpedia"]["infobox"] = infobox_data
                
                # Get main content areas
                content_div = soup.find("div", {"id": "bodyContent"})
                if content_div:
                    sections = {}
                    headers = content_div.find_all(["h2", "h3"])
                    
                    for header in headers:
                        section_title = header.get_text().strip()
                        # Clean up the title (remove edit links etc.)
                        section_title = re.sub(r'\[edit\]|\[source\]', '', section_title).strip()
                        
                        if section_title:
                            # Get all p tags until the next header
                            content = []
                            for sibling in header.next_siblings:
                                if sibling.name in ["h2", "h3"]:
                                    break
                                if sibling.name == "p":
                                    content.append(sibling.get_text().strip())
                            
                            if content:
                                sections[section_title] = "\n".join(content)
                    
                    self.data["ballotpedia"]["sections"] = sections
                
                self.data["ballotpedia"]["url"] = url
                logger.info(f"Successfully scraped Ballotpedia for {self.name}")
            else:
                logger.warning(f"Ballotpedia page not found for {self.name}: status code {response.status_code}")
        except Exception as e:
            logger.error(f"Error in Ballotpedia scraping: {str(e)}")
    
    def scrape_social_media(self):
        """Try to identify social media accounts"""
        logger.info(f"Searching for social media accounts for {self.name}")
        
        # We'll use Wikipedia data if available to find social media links
        if "wikipedia" in self.data and "content" in self.data["wikipedia"]:
            content = self.data["wikipedia"]["content"]
            
            # Look for Twitter/X handles
            twitter_matches = re.findall(r'(?:twitter\.com\/|@)([A-Za-z0-9_]+)', content)
            if twitter_matches:
                self.data["social_media"]["twitter"] = f"https://twitter.com/{twitter_matches[0]}"
            
            # Look for Facebook pages
            fb_matches = re.findall(r'facebook\.com\/([A-Za-z0-9.]+)', content)
            if fb_matches:
                self.data["social_media"]["facebook"] = f"https://facebook.com/{fb_matches[0]}"
            
            # Look for Instagram handles
            ig_matches = re.findall(r'instagram\.com\/([A-Za-z0-9_.]+)', content)
            if ig_matches:
                self.data["social_media"]["instagram"] = f"https://instagram.com/{ig_matches[0]}"
            
            # Look for YouTube channels
            yt_matches = re.findall(r'youtube\.com\/(user|channel|c)\/([A-Za-z0-9_-]+)', content)
            if yt_matches:
                self.data["social_media"]["youtube"] = f"https://youtube.com/{yt_matches[0][0]}/{yt_matches[0][1]}"
        
        # If we have Ballotpedia data, check there too
        if "ballotpedia" in self.data and "sections" in self.data["ballotpedia"]:
            for section_title, section_content in self.data["ballotpedia"]["sections"].items():
                if "external links" in section_title.lower() or "contact" in section_title.lower():
                    # Check for Twitter/X
                    twitter_matches = re.findall(r'(?:twitter\.com\/|@)([A-Za-z0-9_]+)', section_content)
                    if twitter_matches and "twitter" not in self.data["social_media"]:
                        self.data["social_media"]["twitter"] = f"https://twitter.com/{twitter_matches[0]}"
                    
                    # Check for others...
                    fb_matches = re.findall(r'facebook\.com\/([A-Za-z0-9.]+)', section_content)
                    if fb_matches and "facebook" not in self.data["social_media"]:
                        self.data["social_media"]["facebook"] = f"https://facebook.com/{fb_matches[0]}"
        
        logger.info(f"Found {len(self.data['social_media'])} social media accounts for {self.name}")
    
    def save_data(self):
        """Save the scraped data to a JSON file"""
        # Create a safe filename from the politician's name
        safe_filename = re.sub(r'[^\w\s-]', '', self.name).strip().lower()
        safe_filename = re.sub(r'[-\s]+', '_', safe_filename)
        
        output_file = os.path.join(self.output_dir, f"{safe_filename}.json")
        
        with open(output_file, 'w') as f:
            json.dump(self.data, f, indent=2)
        
        logger.info(f"Data saved to {output_file}")
        return output_file

def main():
    parser = argparse.ArgumentParser(description='Scrape data for a politician')
    parser.add_argument('name', help='The name of the politician to scrape data for')
    args = parser.parse_args()
    
    scraper = PoliticianScraper(args.name)
    scraper.scrape_all()

if __name__ == "__main__":
    main() 