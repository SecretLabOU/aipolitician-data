import json
import os
import datetime
import re
from pathlib import Path

# Try to import spacy, but provide a fallback if it fails
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    print("Warning: spaCy is not available. Text processing will be limited.")
    SPACY_AVAILABLE = False

class PoliticianPipeline:
    """Pipeline for processing and saving politician data"""
    
    def __init__(self):
        # Create data directory if it doesn't exist
        self.data_dir = Path(__file__).resolve().parents[2] / 'data'
        self.data_dir.mkdir(exist_ok=True)
        
        # Load spaCy model for text processing if available
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                print("Loaded spaCy model successfully.")
            except OSError:
                try:
                    print("Downloading spaCy model...")
                    from spacy.cli import download
                    download("en_core_web_sm")
                    self.nlp = spacy.load("en_core_web_sm")
                    print("Downloaded and loaded spaCy model successfully.")
                except Exception as e:
                    print(f"Could not download spaCy model: {str(e)}")
                    print("Falling back to basic text processing.")
    
    def process_item(self, item, spider):
        """Process the scraped item and save it to a JSON file"""
        # Clean text content
        if 'raw_content' in item:
            item['raw_content'] = self.clean_text(item['raw_content'])
        
        # Process speeches list
        if 'speeches' in item and isinstance(item['speeches'], list):
            item['speeches'] = [self.clean_text(speech) for speech in item['speeches'] if speech]
        
        # Process statements list
        if 'statements' in item and isinstance(item['statements'], list):
            item['statements'] = [self.clean_text(statement) for statement in item['statements'] if statement]
        
        # Generate ID from politician name if not provided
        if not item.get('id'):
            item['id'] = self.generate_id_from_name(item.get('name', 'unknown'))
        
        # Add timestamp if not provided
        if not item.get('timestamp'):
            item['timestamp'] = datetime.datetime.now().isoformat()
        
        # Save to file
        filename = f"{item['id']}.json"
        filepath = self.data_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dict(item), f, ensure_ascii=False, indent=2)
        
        spider.logger.info(f"Saved politician data to {filepath}")
        return item
    
    def clean_text(self, text):
        """Clean and normalize text using spaCy if available, otherwise use basic cleaning"""
        if not text:
            return ""
        
        # Basic cleanup
        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
        text = text.strip()
        
        # Use spaCy for more advanced text cleaning if available
        if self.nlp:
            try:
                doc = self.nlp(text)
                # Remove emails, URLs, and other non-relevant information
                cleaned_tokens = [token.text for token in doc if not token.like_email and not token.like_url]
                return " ".join(cleaned_tokens)
            except Exception as e:
                print(f"Error during spaCy processing: {str(e)}")
                # Fall back to basic cleaning if spaCy fails
                
        # Fallback: just use regex for basic cleaning
        # Remove citation brackets like [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)
        # Try to remove URLs with a simple regex
        text = re.sub(r'https?://\S+', '', text)
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        return text
    
    def generate_id_from_name(self, name):
        """Generate a URL-friendly ID from the politician's name"""
        # Convert to lowercase and replace spaces with hyphens
        name_id = name.lower().replace(' ', '-')
        
        # Remove special characters
        name_id = re.sub(r'[^a-z0-9-]', '', name_id)
        
        # Add timestamp to ensure uniqueness
        timestamp = datetime.datetime.now().strftime("%Y%m%d")
        return f"{name_id}-{timestamp}" 