#!/usr/bin/env python3
import argparse
import json
import os
import logging
import glob
import re
import uuid
import dateutil.parser
from datetime import datetime
import spacy
import nltk
from nltk.tokenize import sent_tokenize

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure NLTK resources are downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class PoliticianDataFormatter:
    """
    Formats the raw politician data into a structure suitable for RAG applications.
    """
    def __init__(self, input_dir=None, output_dir=None):
        """Initialize the formatter with input and output directories"""
        if input_dir is None:
            self.input_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                        "data", "politicians")
        else:
            self.input_dir = input_dir
            
        if output_dir is None:
            self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                         "data", "formatted")
        else:
            self.output_dir = output_dir
            
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize SpaCy NLP
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded SpaCy en_core_web_sm model")
        except:
            logger.warning("SpaCy model not found. Downloading en_core_web_sm...")
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Downloaded and loaded SpaCy en_core_web_sm model")
    
    def process_all_files(self):
        """Process all politician data files in the input directory"""
        input_files = glob.glob(os.path.join(self.input_dir, "*.json"))
        
        if not input_files:
            logger.warning(f"No politician data files found in {self.input_dir}")
            return False
            
        logger.info(f"Found {len(input_files)} politician data files to process")
        
        for file_path in input_files:
            try:
                # Load the source data
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                
                # Process the data
                formatted_data = self.format_politician_data(raw_data)
                
                if formatted_data:
                    # Generate output filename
                    basename = os.path.basename(file_path)
                    output_file = os.path.join(self.output_dir, f"formatted_{basename}")
                    
                    # Save the formatted data
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(formatted_data, f, indent=2, ensure_ascii=False)
                    
                    logger.info(f"Successfully processed {basename} -> {output_file}")
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
        
        return True
    
    def format_politician_data(self, raw_data):
        """
        Transform raw politician data into the structured format for RAG
        
        Args:
            raw_data: The raw politician data from the scraper
            
        Returns:
            A dictionary with the structured data suitable for RAG
        """
        if not raw_data:
            return None
            
        # Generate a unique ID for the politician
        politician_name = raw_data.get("name", "Unknown")
        safe_name = re.sub(r'[^\w\s-]', '', politician_name).lower().replace(' ', '-')
        politician_id = f"{safe_name}-{uuid.uuid4().hex[:8]}"
        
        # Extract basic information
        formatted_data = {
            "id": politician_id,
            "name": politician_name,
            "date_of_birth": self.extract_birth_date(raw_data),
            "political_affiliation": self.extract_political_affiliation(raw_data),
            "positions": self.extract_positions(raw_data),
            "entries": []
        }
        
        # Add basic biographical information
        self.add_biographical_entries(formatted_data, raw_data)
        
        # Add news articles
        self.add_news_entries(formatted_data, raw_data)
        
        # Add Wikipedia content
        self.add_wikipedia_entries(formatted_data, raw_data)
        
        # Add Ballotpedia content
        self.add_ballotpedia_entries(formatted_data, raw_data)
        
        # Add voting record information
        self.add_voting_record_entries(formatted_data, raw_data)
        
        # Add speeches
        self.add_speech_entries(formatted_data, raw_data)
        
        # Add social media information
        self.add_social_media_entries(formatted_data, raw_data)
        
        logger.info(f"Created {len(formatted_data['entries'])} entries for {politician_name}")
        
        return formatted_data
    
    def extract_birth_date(self, raw_data):
        """Extract the politician's date of birth from the raw data"""
        # Try Wikipedia infobox
        if "wikipedia" in raw_data and "infobox" in raw_data["wikipedia"]:
            infobox = raw_data["wikipedia"]["infobox"]
            for key in ["Born", "Date of birth", "Birth date"]:
                if key in infobox:
                    try:
                        # Extract date using dateutil parser
                        text = infobox[key]
                        
                        # Use NLP to find dates
                        doc = self.nlp(text)
                        for ent in doc.ents:
                            if ent.label_ == "DATE":
                                try:
                                    date = dateutil.parser.parse(ent.text, fuzzy=True)
                                    # Only return if it's likely a birth date (not just a year)
                                    if date.year < 2010 and date.year > 1900:
                                        return date.strftime("%Y-%m-%d")
                                except:
                                    pass
                    except:
                        pass
        
        # Try Ballotpedia
        if "ballotpedia" in raw_data and "sections" in raw_data["ballotpedia"]:
            if "Biography" in raw_data["ballotpedia"]["sections"]:
                bio = raw_data["ballotpedia"]["sections"]["Biography"]
                doc = self.nlp(bio)
                for ent in doc.ents:
                    if ent.label_ == "DATE":
                        try:
                            date = dateutil.parser.parse(ent.text, fuzzy=True)
                            if date.year < 2010 and date.year > 1900:
                                return date.strftime("%Y-%m-%d")
                        except:
                            pass
        
        return None
    
    def extract_political_affiliation(self, raw_data):
        """Extract the politician's political affiliation"""
        # Try Wikipedia infobox
        if "wikipedia" in raw_data and "infobox" in raw_data["wikipedia"]:
            infobox = raw_data["wikipedia"]["infobox"]
            for key in ["Party", "Political party"]:
                if key in infobox:
                    return infobox[key]
        
        # Try Ballotpedia
        if "ballotpedia" in raw_data and "infobox" in raw_data["ballotpedia"]:
            infobox = raw_data["ballotpedia"]["infobox"]
            for key in ["Party", "Political party", "Affiliation"]:
                if key in infobox:
                    return infobox[key]
        
        return None
    
    def extract_positions(self, raw_data):
        """Extract positions held by the politician"""
        positions = []
        
        # Try Wikipedia infobox
        if "wikipedia" in raw_data and "infobox" in raw_data["wikipedia"]:
            infobox = raw_data["wikipedia"]["infobox"]
            for key in ["Office", "Offices held", "Title", "Position"]:
                if key in infobox:
                    positions.append(infobox[key])
        
        # Try Ballotpedia
        if "ballotpedia" in raw_data and "sections" in raw_data["ballotpedia"]:
            if "Career" in raw_data["ballotpedia"]["sections"]:
                career = raw_data["ballotpedia"]["sections"]["Career"]
                # Extract positions using NLP
                doc = self.nlp(career)
                for sent in doc.sents:
                    if re.search(r'\b(elected|appointed|served as|position|office)\b', sent.text, re.IGNORECASE):
                        positions.append(sent.text.strip())
        
        return positions
    
    def add_biographical_entries(self, formatted_data, raw_data):
        """Add biographical information entries"""
        # Wikipedia summary
        if "wikipedia" in raw_data and "summary" in raw_data["wikipedia"]:
            summary = raw_data["wikipedia"]["summary"]
            formatted_data["entries"].append({
                "type": "biography",
                "text": summary,
                "source_url": raw_data["wikipedia"].get("url", ""),
                "timestamp": raw_data.get("scraped_at", datetime.now().isoformat())
            })
        
        # Ballotpedia Biography
        if "ballotpedia" in raw_data and "sections" in raw_data["ballotpedia"]:
            if "Biography" in raw_data["ballotpedia"]["sections"]:
                bio = raw_data["ballotpedia"]["sections"]["Biography"]
                formatted_data["entries"].append({
                    "type": "biography",
                    "text": bio,
                    "source_url": raw_data["ballotpedia"].get("url", ""),
                    "timestamp": raw_data.get("scraped_at", datetime.now().isoformat())
                })
        
        # Congressional bio
        if "congress_bio" in raw_data and "bio" in raw_data["congress_bio"]:
            bio = raw_data["congress_bio"]["bio"]
            formatted_data["entries"].append({
                "type": "biography",
                "text": bio,
                "source_url": raw_data["congress_bio"].get("url", ""),
                "timestamp": raw_data.get("scraped_at", datetime.now().isoformat())
            })
    
    def add_news_entries(self, formatted_data, raw_data):
        """Add news article entries"""
        if "news_articles" in raw_data:
            for article in raw_data["news_articles"]:
                # Get title and content
                title = article.get("title", "")
                content = article.get("content", article.get("description", ""))
                
                if content:
                    formatted_data["entries"].append({
                        "type": "news_article",
                        "text": f"{title}\n\n{content}",
                        "source_url": article.get("url", ""),
                        "timestamp": article.get("published_date", raw_data.get("scraped_at", datetime.now().isoformat()))
                    })
    
    def add_wikipedia_entries(self, formatted_data, raw_data):
        """Add Wikipedia content as entries"""
        if "wikipedia" in raw_data and "content" in raw_data["wikipedia"]:
            # Split the full content into chunks of reasonable size
            full_content = raw_data["wikipedia"]["content"]
            
            # Use NLTK sentence tokenization
            sentences = sent_tokenize(full_content)
            
            # Create chunks of about 1000 characters each
            chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) < 1000:
                    current_chunk += sentence + " "
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + " "
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            # Add each chunk as a separate entry
            for i, chunk in enumerate(chunks):
                formatted_data["entries"].append({
                    "type": "wikipedia_content",
                    "text": chunk,
                    "source_url": raw_data["wikipedia"].get("url", ""),
                    "chunk_index": i,
                    "timestamp": raw_data.get("scraped_at", datetime.now().isoformat())
                })
        
        # Add individual sections if available
        if "wikipedia" in raw_data and "sections" in raw_data["wikipedia"]:
            for section_name, content in raw_data["wikipedia"]["sections"].items():
                if content:
                    formatted_data["entries"].append({
                        "type": "wikipedia_section",
                        "section_name": section_name,
                        "text": content,
                        "source_url": raw_data["wikipedia"].get("url", ""),
                        "timestamp": raw_data.get("scraped_at", datetime.now().isoformat())
                    })
    
    def add_ballotpedia_entries(self, formatted_data, raw_data):
        """Add Ballotpedia content as entries"""
        if "ballotpedia" in raw_data and "sections" in raw_data["ballotpedia"]:
            for section_name, content in raw_data["ballotpedia"]["sections"].items():
                if content:
                    formatted_data["entries"].append({
                        "type": "ballotpedia_section",
                        "section_name": section_name,
                        "text": content,
                        "source_url": raw_data["ballotpedia"].get("url", ""),
                        "timestamp": raw_data.get("scraped_at", datetime.now().isoformat())
                    })
    
    def add_voting_record_entries(self, formatted_data, raw_data):
        """Add voting record information as entries"""
        if "voting_record" in raw_data and "sections" in raw_data["voting_record"]:
            for section_key, content in raw_data["voting_record"]["sections"].items():
                if content:
                    # Clean up the section name
                    section_name = section_key.replace("ballotpedia_", "").replace("wikipedia_", "")
                    
                    formatted_data["entries"].append({
                        "type": "voting_record",
                        "section_name": section_name,
                        "text": content,
                        "timestamp": raw_data.get("scraped_at", datetime.now().isoformat())
                    })
    
    def add_speech_entries(self, formatted_data, raw_data):
        """Add speech entries"""
        if "speeches" in raw_data and isinstance(raw_data["speeches"], list):
            for speech in raw_data["speeches"]:
                if "text" in speech:
                    formatted_data["entries"].append({
                        "type": "speech",
                        "text": speech["text"],
                        "title": speech.get("title", "Untitled Speech"),
                        "date": speech.get("date", ""),
                        "source_url": speech.get("source", ""),
                        "timestamp": raw_data.get("scraped_at", datetime.now().isoformat())
                    })
    
    def add_social_media_entries(self, formatted_data, raw_data):
        """Add social media information"""
        if "social_media" in raw_data:
            for platform, urls in raw_data["social_media"].items():
                if isinstance(urls, list):
                    for url in urls:
                        formatted_data["entries"].append({
                            "type": "social_media",
                            "platform": platform,
                            "text": f"{formatted_data['name']}'s {platform} account: {url}",
                            "source_url": url,
                            "timestamp": raw_data.get("scraped_at", datetime.now().isoformat())
                        })
                elif isinstance(urls, str):
                    formatted_data["entries"].append({
                        "type": "social_media",
                        "platform": platform,
                        "text": f"{formatted_data['name']}'s {platform} account: {urls}",
                        "source_url": urls,
                        "timestamp": raw_data.get("scraped_at", datetime.now().isoformat())
                    })

def main():
    parser = argparse.ArgumentParser(description='Format politician data for RAG')
    parser.add_argument('--input', help='Directory containing raw politician data')
    parser.add_argument('--output', help='Directory for formatted output')
    parser.add_argument('--single', help='Process a single file instead of all files in the directory')
    args = parser.parse_args()
    
    formatter = PoliticianDataFormatter(input_dir=args.input, output_dir=args.output)
    
    if args.single:
        # Process a single file
        try:
            with open(args.single, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            formatted_data = formatter.format_politician_data(raw_data)
            
            if formatted_data:
                # Generate output filename
                basename = os.path.basename(args.single)
                output_file = os.path.join(formatter.output_dir, f"formatted_{basename}")
                
                # Save the formatted data
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(formatted_data, f, indent=2, ensure_ascii=False)
                
                print(f"Successfully processed {basename} -> {output_file}")
        except Exception as e:
            print(f"Error processing {args.single}: {str(e)}")
    else:
        # Process all files in the directory
        formatter.process_all_files()

if __name__ == "__main__":
    main() 