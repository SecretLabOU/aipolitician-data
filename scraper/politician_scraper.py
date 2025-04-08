#!/usr/bin/env python3
import argparse
import requests
from bs4 import BeautifulSoup
import wikipedia
import json
import os
from time import sleep
import logging
from urllib.parse import quote_plus, urljoin
import re
import feedparser
from datetime import datetime
from newspaper import Article, Config
import trafilatura
from dateutil import parser
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure newspaper
news_config = Config()
news_config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
news_config.request_timeout = 10

# Utility functions
def get_article_content(url, max_retries=3):
    """Extract content from a news article URL using newspaper3k and trafilatura as backup"""
    retries = 0
    content = {"title": "", "text": "", "published_date": "", "authors": []}
    
    while retries < max_retries:
        try:
            # Try with newspaper3k first
            article = Article(url, config=news_config)
            article.download()
            article.parse()
            
            if article.text:
                content["title"] = article.title
                content["text"] = article.text
                content["published_date"] = article.publish_date.isoformat() if article.publish_date else ""
                content["authors"] = article.authors
                return content
            
            # If newspaper3k fails to get text, try trafilatura
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                result = trafilatura.extract(downloaded, include_comments=False, 
                                           include_tables=True, output_format='json',
                                           with_metadata=True)
                if result:
                    result_dict = json.loads(result)
                    content["title"] = result_dict.get("title", "")
                    content["text"] = result_dict.get("text", "")
                    content["published_date"] = result_dict.get("date", "")
                    content["authors"] = [result_dict.get("author", "")]
                    return content
            
            # If both fail, return empty content
            return content
        except Exception as e:
            retries += 1
            sleep(2)
            logger.warning(f"Error extracting article content (attempt {retries}): {e}")
    
    return content

def setup_selenium_driver():
    """Set up a selenium driver for scraping JavaScript-rendered websites"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        return driver
    except Exception as e:
        logger.error(f"Failed to set up Selenium driver: {e}")
        return None

def get_text_with_selenium(url, wait_time=10):
    """Scrape a page with Selenium and extract text content"""
    driver = setup_selenium_driver()
    if not driver:
        return ""
    
    try:
        driver.get(url)
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        sleep(2)  # Give JavaScript time to fully render
        page_source = driver.page_source
        text = trafilatura.extract(page_source)
        return text
    except Exception as e:
        logger.error(f"Error scraping with Selenium: {e}")
        return ""
    finally:
        driver.quit()

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
            "official_websites": {},
            "congress_bio": {},
            "voting_record": {},
            "speeches": [],
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
            logger.error(traceback.format_exc())
        
        try:
            self.scrape_news()
        except Exception as e:
            logger.error(f"Error scraping news: {e}")
            logger.error(traceback.format_exc())
        
        try:
            self.scrape_ballotpedia()
        except Exception as e:
            logger.error(f"Error scraping Ballotpedia: {e}")
            logger.error(traceback.format_exc())
        
        try:
            self.scrape_social_media()
        except Exception as e:
            logger.error(f"Error scraping social media: {e}")
            logger.error(traceback.format_exc())
        
        try:
            self.scrape_congress_bio()
        except Exception as e:
            logger.error(f"Error scraping Congress bio: {e}")
            logger.error(traceback.format_exc())
        
        try:
            self.scrape_official_websites()
        except Exception as e:
            logger.error(f"Error scraping official websites: {e}")
            logger.error(traceback.format_exc())
        
        try:
            self.scrape_voting_record()
        except Exception as e:
            logger.error(f"Error scraping voting record: {e}")
            logger.error(traceback.format_exc())
        
        self.save_data()
        logger.info(f"Completed scraping data for {self.name}")
        
    def scrape_wikipedia(self):
        """Scrape Wikipedia for information about the politician"""
        logger.info(f"Scraping Wikipedia for {self.name}")
        
        try:
            # Search for the politician's page
            search_results = wikipedia.search(f"{self.name} politician")
            
            if not search_results:
                # Try without "politician" qualifier
                search_results = wikipedia.search(self.name)
                if not search_results:
                    logger.warning(f"No Wikipedia results found for {self.name}")
                    return
            
            # Try to get the most relevant page
            try:
                page = wikipedia.page(search_results[0], auto_suggest=False)
            except wikipedia.DisambiguationError as e:
                # If disambiguation page, try to find the most relevant option
                politician_options = [opt for opt in e.options if any(term in opt.lower() for term in 
                                     ['politician', 'congress', 'senator', 'representative', 
                                      'governor', 'mayor', 'cabinet', 'president'])]
                if politician_options:
                    page = wikipedia.page(politician_options[0], auto_suggest=False)
                else:
                    page = wikipedia.page(e.options[0], auto_suggest=False)
            
            # Extract the content and basic information
            self.data["wikipedia"] = {
                "title": page.title,
                "url": page.url,
                "summary": page.summary,
                "content": page.content,  # Get full content
                "categories": page.categories,
                "references": page.references,
                "links": page.links,
                "sections": {},
                "images": page.images
            }
            
            # Extract content by section
            for section in page.sections:
                try:
                    section_content = page.section(section)
                    if section_content and len(section_content) > 0:
                        self.data["wikipedia"]["sections"][section] = section_content
                except Exception as e:
                    logger.error(f"Error extracting section {section}: {e}")
            
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
                
                # Also extract tables that might contain voting records or biographical info
                tables = soup.find_all("table", {"class": ["wikitable", "sortable"]})
                if tables:
                    self.data["wikipedia"]["tables"] = []
                    for i, table in enumerate(tables):
                        table_data = {"headers": [], "rows": []}
                        headers = table.find_all("th")
                        table_data["headers"] = [h.get_text().strip() for h in headers]
                        
                        rows = table.find_all("tr")[1:]  # Skip header row
                        for row in rows:
                            cells = row.find_all(["td", "th"])
                            row_data = [cell.get_text().strip() for cell in cells]
                            if row_data:
                                table_data["rows"].append(row_data)
                        
                        self.data["wikipedia"]["tables"].append(table_data)
            
            logger.info(f"Successfully scraped Wikipedia for {self.name}")
            
        except Exception as e:
            logger.error(f"Error in Wikipedia scraping: {str(e)}")
            logger.error(traceback.format_exc())
            
    def scrape_news(self):
        """Scrape recent news articles about the politician"""
        logger.info(f"Scraping news for {self.name}")
        
        # Format name for URL
        query = quote_plus(f"{self.name} politician")
        
        # Try Google News
        google_news_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            # Parse the RSS feed
            feed = feedparser.parse(google_news_url)
            
            for item in feed.entries[:15]:  # Increased from 10 to 15 articles
                try:
                    title = item.title
                    link = item.link
                    pub_date = item.published
                    description = item.description if hasattr(item, 'description') else ""
                    
                    # Extract the full article content
                    article_content = get_article_content(link)
                    
                    # Only add articles that have substantial content
                    if article_content["text"] and len(article_content["text"]) > 100:
                        self.data["news_articles"].append({
                            "title": title,
                            "url": link,
                            "published_date": pub_date,
                            "description": description,
                            "content": article_content["text"],
                            "authors": article_content["authors"]
                        })
                except Exception as e:
                    logger.error(f"Error processing news item: {e}")
            
            logger.info(f"Found {len(self.data['news_articles'])} news articles for {self.name}")
        except Exception as e:
            logger.error(f"Error in Google News scraping: {str(e)}")
        
        # Also try other news sources if Google News didn't return enough results
        if len(self.data["news_articles"]) < 5:
            try:
                # Use news API if available or other sources
                pass
            except Exception as e:
                logger.error(f"Error in additional news sources scraping: {str(e)}")
    
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
                    headers = content_div.find_all(["h2", "h3", "h4"])
                    
                    for header in headers:
                        section_title = header.get_text().strip()
                        # Clean up the title (remove edit links etc.)
                        section_title = re.sub(r'\[edit\]|\[source\]', '', section_title).strip()
                        
                        if section_title:
                            # Get all content until the next header
                            content = []
                            element = header.next_sibling
                            
                            while element and element.name not in ["h2", "h3", "h4"]:
                                if element.name in ["p", "ul", "ol", "div", "table"]:
                                    # Extract text from the element
                                    text = element.get_text().strip()
                                    if text:
                                        content.append(text)
                                element = element.next_sibling
                            
                            if content:
                                sections[section_title] = "\n".join(content)
                    
                    self.data["ballotpedia"]["sections"] = sections
                
                # Extract tables (for voting records, committee assignments, etc.)
                tables = soup.find_all("table", {"class": ["wikitable", "sortable"]})
                if tables:
                    self.data["ballotpedia"]["tables"] = []
                    for i, table in enumerate(tables):
                        table_data = {"caption": "", "headers": [], "rows": []}
                        
                        # Get caption if available
                        caption = table.find("caption")
                        if caption:
                            table_data["caption"] = caption.get_text().strip()
                        
                        # Get headers
                        headers = table.find_all("th")
                        table_data["headers"] = [h.get_text().strip() for h in headers]
                        
                        # Get rows
                        rows = table.find_all("tr")[1:]  # Skip header row
                        for row in rows:
                            cells = row.find_all(["td", "th"])
                            row_data = [cell.get_text().strip() for cell in cells]
                            if row_data:
                                table_data["rows"].append(row_data)
                        
                        self.data["ballotpedia"]["tables"].append(table_data)
                
                self.data["ballotpedia"]["url"] = url
                logger.info(f"Successfully scraped Ballotpedia for {self.name}")
            else:
                logger.warning(f"Ballotpedia page not found for {self.name}: status code {response.status_code}")
        except Exception as e:
            logger.error(f"Error in Ballotpedia scraping: {str(e)}")
            logger.error(traceback.format_exc())
    
    def scrape_social_media(self):
        """Try to identify and scrape social media accounts"""
        logger.info(f"Searching for social media accounts for {self.name}")
        
        # Lists to store found accounts
        twitter_accounts = []
        facebook_accounts = []
        instagram_accounts = []
        youtube_accounts = []
        linkedin_accounts = []
        
        # Search in Wikipedia data
        if "wikipedia" in self.data:
            content_to_search = ""
            
            # Search in full content
            if "content" in self.data["wikipedia"]:
                content_to_search += self.data["wikipedia"]["content"]
            
            # Search in infobox
            if "infobox" in self.data["wikipedia"]:
                for key, value in self.data["wikipedia"]["infobox"].items():
                    content_to_search += f" {value}"
            
            # Look for Twitter/X handles
            twitter_matches = re.findall(r'(?:twitter\.com\/|x\.com\/|@)([A-Za-z0-9_]+)', content_to_search)
            twitter_accounts.extend([f"https://twitter.com/{handle}" for handle in twitter_matches])
            
            # Look for Facebook pages
            fb_matches = re.findall(r'facebook\.com\/([A-Za-z0-9.]+)', content_to_search)
            facebook_accounts.extend([f"https://facebook.com/{handle}" for handle in fb_matches])
            
            # Look for Instagram handles
            ig_matches = re.findall(r'instagram\.com\/([A-Za-z0-9_.]+)', content_to_search)
            instagram_accounts.extend([f"https://instagram.com/{handle}" for handle in ig_matches])
            
            # Look for YouTube channels
            yt_matches = re.findall(r'youtube\.com\/(user|channel|c)\/([A-Za-z0-9_-]+)', content_to_search)
            youtube_accounts.extend([f"https://youtube.com/{m[0]}/{m[1]}" for m in yt_matches])
            
            # Look for LinkedIn profiles
            li_matches = re.findall(r'linkedin\.com\/in\/([A-Za-z0-9_-]+)', content_to_search)
            linkedin_accounts.extend([f"https://linkedin.com/in/{handle}" for handle in li_matches])
        
        # Search in Ballotpedia data
        if "ballotpedia" in self.data:
            content_to_search = ""
            
            # Search in sections
            if "sections" in self.data["ballotpedia"]:
                for section_title, section_content in self.data["ballotpedia"]["sections"].items():
                    content_to_search += f" {section_content}"
            
            # Search in infobox
            if "infobox" in self.data["ballotpedia"]:
                for key, value in self.data["ballotpedia"]["infobox"].items():
                    content_to_search += f" {value}"
            
            # Look for Twitter/X handles
            twitter_matches = re.findall(r'(?:twitter\.com\/|x\.com\/|@)([A-Za-z0-9_]+)', content_to_search)
            twitter_accounts.extend([f"https://twitter.com/{handle}" for handle in twitter_matches])
            
            # Look for Facebook pages
            fb_matches = re.findall(r'facebook\.com\/([A-Za-z0-9.]+)', content_to_search)
            facebook_accounts.extend([f"https://facebook.com/{handle}" for handle in fb_matches])
            
            # Look for Instagram handles
            ig_matches = re.findall(r'instagram\.com\/([A-Za-z0-9_.]+)', content_to_search)
            instagram_accounts.extend([f"https://instagram.com/{handle}" for handle in ig_matches])
            
            # Look for YouTube channels
            yt_matches = re.findall(r'youtube\.com\/(user|channel|c)\/([A-Za-z0-9_-]+)', content_to_search)
            youtube_accounts.extend([f"https://youtube.com/{m[0]}/{m[1]}" for m in yt_matches])
            
            # Look for LinkedIn profiles
            li_matches = re.findall(r'linkedin\.com\/in\/([A-Za-z0-9_-]+)', content_to_search)
            linkedin_accounts.extend([f"https://linkedin.com/in/{handle}" for handle in li_matches])
        
        # Deduplicate and store accounts
        if twitter_accounts:
            self.data["social_media"]["twitter"] = list(set(twitter_accounts))
        
        if facebook_accounts:
            self.data["social_media"]["facebook"] = list(set(facebook_accounts))
        
        if instagram_accounts:
            self.data["social_media"]["instagram"] = list(set(instagram_accounts))
        
        if youtube_accounts:
            self.data["social_media"]["youtube"] = list(set(youtube_accounts))
        
        if linkedin_accounts:
            self.data["social_media"]["linkedin"] = list(set(linkedin_accounts))
        
        # Try to scrape content from social media if needed
        # This part could be expanded to use APIs for each platform
        
        logger.info(f"Found social media accounts for {self.name}: Twitter={len(twitter_accounts)}, Facebook={len(facebook_accounts)}, Instagram={len(instagram_accounts)}, YouTube={len(youtube_accounts)}, LinkedIn={len(linkedin_accounts)}")
    
    def scrape_congress_bio(self):
        """Scrape biographical information from Congress.gov"""
        logger.info(f"Scraping congressional biographical information for {self.name}")
        
        # Format name for search
        search_name = quote_plus(self.name)
        search_url = f"https://www.congress.gov/search?q=%7B%22source%22%3A%22members%22%2C%22search%22%3A%22{search_name}%22%7D"
        
        try:
            response = requests.get(search_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for search results
                results = soup.find_all("li", {"class": "compact"})
                if not results:
                    logger.warning(f"No results found on Congress.gov for {self.name}")
                    return
                
                # Find the first result that matches our politician
                member_url = None
                for result in results:
                    name_elem = result.find("span", {"class": "result-heading"})
                    if name_elem and self.name.lower() in name_elem.get_text().lower():
                        link = result.find("a")
                        if link and 'href' in link.attrs:
                            member_url = urljoin("https://www.congress.gov", link['href'])
                            break
                
                if not member_url:
                    logger.warning(f"Could not find member page on Congress.gov for {self.name}")
                    return
                
                # Scrape the member page
                member_response = requests.get(member_url)
                if member_response.status_code == 200:
                    member_soup = BeautifulSoup(member_response.text, 'html.parser')
                    
                    # Basic information
                    self.data["congress_bio"]["url"] = member_url
                    
                    # Get profile information
                    profile_div = member_soup.find("div", {"class": "profile"})
                    if profile_div:
                        # Extract information
                        self.data["congress_bio"]["profile"] = profile_div.get_text(separator="\n").strip()
                    
                    # Extract biography if available
                    bio_div = member_soup.find("div", {"id": "biography"})
                    if bio_div:
                        self.data["congress_bio"]["biography"] = bio_div.get_text(separator="\n").strip()
                    
                    # Extract committee assignments
                    committees_div = member_soup.find("div", {"id": "current-committees"})
                    if committees_div:
                        committees = []
                        committee_items = committees_div.find_all("li")
                        for item in committee_items:
                            committees.append(item.get_text().strip())
                        
                        self.data["congress_bio"]["committees"] = committees
                    
                    logger.info(f"Successfully scraped Congress.gov bio for {self.name}")
            else:
                logger.warning(f"Failed to search Congress.gov: status code {response.status_code}")
        except Exception as e:
            logger.error(f"Error in Congress.gov bio scraping: {str(e)}")
            logger.error(traceback.format_exc())
    
    def scrape_official_websites(self):
        """Scrape politician's official websites"""
        logger.info(f"Scraping official websites for {self.name}")
        
        # Check if we have Ballotpedia or Wikipedia data with links to official sites
        official_sites = []
        
        # Check Ballotpedia infobox for official website
        if "ballotpedia" in self.data and "infobox" in self.data["ballotpedia"]:
            for key, value in self.data["ballotpedia"]["infobox"].items():
                if "website" in key.lower() or "official" in key.lower():
                    # Extract URLs from text
                    urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', value)
                    official_sites.extend(urls)
        
        # Check Wikipedia infobox for official website
        if "wikipedia" in self.data and "infobox" in self.data["wikipedia"]:
            for key, value in self.data["wikipedia"]["infobox"].items():
                if "website" in key.lower() or "official" in key.lower():
                    # Extract URLs from text
                    urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', value)
                    official_sites.extend(urls)
        
        # Deduplicate URLs
        official_sites = list(set(official_sites))
        
        # Scrape content from each official site
        for site_url in official_sites:
            try:
                # Try to scrape with trafilatura first
                downloaded = trafilatura.fetch_url(site_url)
                if downloaded:
                    content = trafilatura.extract(downloaded, include_tables=True, 
                                                include_links=True, include_images=False)
                    
                    if content:
                        self.data["official_websites"][site_url] = {
                            "content": content,
                            "scraped_at": datetime.now().isoformat()
                        }
                        continue
                
                # If trafilatura fails, try with Selenium
                selenium_content = get_text_with_selenium(site_url)
                if selenium_content:
                    self.data["official_websites"][site_url] = {
                        "content": selenium_content,
                        "scraped_at": datetime.now().isoformat()
                    }
            except Exception as e:
                logger.error(f"Error scraping official website {site_url}: {e}")
        
        logger.info(f"Scraped {len(self.data['official_websites'])} official websites for {self.name}")
    
    def scrape_voting_record(self):
        """Scrape voting record data from various sources"""
        logger.info(f"Scraping voting record for {self.name}")
        
        # We'll use data from Congress.gov and ProPublica Congress API if available
        # For now, we'll extract what we can from Ballotpedia and Wikipedia
        
        # Check if we found tables in Ballotpedia that might have voting records
        if "ballotpedia" in self.data and "tables" in self.data["ballotpedia"]:
            voting_tables = []
            
            for table in self.data["ballotpedia"]["tables"]:
                # Look for tables that might contain voting records
                caption = table.get("caption", "").lower()
                headers = [h.lower() for h in table.get("headers", [])]
                
                voting_keywords = ["vote", "voting", "record", "bill", "legislation", "key votes", "roll call"]
                
                if any(keyword in caption for keyword in voting_keywords) or \
                   any(any(keyword in header for keyword in voting_keywords) for header in headers):
                    voting_tables.append(table)
            
            if voting_tables:
                self.data["voting_record"]["ballotpedia"] = voting_tables
        
        # Extract voting records from Wikipedia tables if available
        if "wikipedia" in self.data and "tables" in self.data["wikipedia"]:
            voting_tables = []
            
            for table in self.data["wikipedia"]["tables"]:
                # Look for tables that might contain voting records
                headers = [h.lower() for h in table.get("headers", [])]
                
                voting_keywords = ["vote", "voting", "record", "bill", "legislation", "key votes", "roll call"]
                
                if any(any(keyword in header for keyword in voting_keywords) for header in headers):
                    voting_tables.append(table)
            
            if voting_tables:
                self.data["voting_record"]["wikipedia"] = voting_tables
        
        # Extract voting-related content from sections
        voting_sections = {}
        
        # From Wikipedia
        if "wikipedia" in self.data and "sections" in self.data["wikipedia"]:
            for section_name, section_content in self.data["wikipedia"]["sections"].items():
                if any(keyword in section_name.lower() for keyword in ["vote", "voting", "political positions", "political views", "legislation", "sponsored bills"]):
                    voting_sections[f"wikipedia_{section_name}"] = section_content
        
        # From Ballotpedia
        if "ballotpedia" in self.data and "sections" in self.data["ballotpedia"]:
            for section_name, section_content in self.data["ballotpedia"]["sections"].items():
                if any(keyword in section_name.lower() for keyword in ["vote", "voting", "key votes", "political positions", "political views", "legislation", "sponsored bills"]):
                    voting_sections[f"ballotpedia_{section_name}"] = section_content
        
        if voting_sections:
            self.data["voting_record"]["sections"] = voting_sections
        
        logger.info(f"Completed scraping voting record for {self.name}")
    
    def save_data(self):
        """Save the scraped data to a JSON file"""
        # Create a safe filename from the politician's name
        safe_filename = re.sub(r'[^\w\s-]', '', self.name).strip().lower()
        safe_filename = re.sub(r'[-\s]+', '_', safe_filename)
        
        output_file = os.path.join(self.output_dir, f"{safe_filename}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Data saved to {output_file}")
        return output_file

def main():
    parser = argparse.ArgumentParser(description='Scrape data for a politician')
    parser.add_argument('name', help='The name of the politician to scrape data for')
    parser.add_argument('--skip-news', action='store_true', help='Skip scraping news articles')
    parser.add_argument('--skip-social', action='store_true', help='Skip scraping social media')
    parser.add_argument('--output-dir', help='Custom output directory for data files')
    args = parser.parse_args()
    
    scraper = PoliticianScraper(args.name)
    
    if args.output_dir:
        scraper.output_dir = args.output_dir
        os.makedirs(args.output_dir, exist_ok=True)
    
    if args.skip_news:
        scraper.scrape_wikipedia()
        scraper.scrape_ballotpedia()
        scraper.scrape_congress_bio()
        scraper.scrape_official_websites()
        scraper.scrape_voting_record()
        if not args.skip_social:
            scraper.scrape_social_media()
    elif args.skip_social:
        scraper.scrape_wikipedia()
        scraper.scrape_news()
        scraper.scrape_ballotpedia()
        scraper.scrape_congress_bio()
        scraper.scrape_official_websites()
        scraper.scrape_voting_record()
    else:
        scraper.scrape_all()
    
    scraper.save_data()

if __name__ == "__main__":
    main() 