# Define item pipelines here
import os
import json
import logging
from datetime import datetime
from pathlib import Path

class PoliticianDataPipeline:
    """
    Pipeline for processing politician data.
    1. Cleans and processes the text data
    2. Saves the results to JSON files in the data directory
    """
    
    def __init__(self):
        # Get the project root directory
        self.project_dir = Path(__file__).parent.parent.parent
        self.data_dir = self.project_dir / 'data'
        
        # Create data directory if it doesn't exist
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True)
            
        # Set up logging
        self.logger = logging.getLogger('PoliticianDataPipeline')
    
    def process_item(self, item, spider):
        """Process each scraped item."""
        # Ensure key fields are present
        if not item.get('name'):
            self.logger.warning("Item missing required 'name' field. Skipping.")
            return item
            
        # Generate ID if not present
        if not item.get('id'):
            normalized_name = item.get('name', '').lower().replace(' ', '-')
            current_date = datetime.now().strftime('%Y%m%d')
            item['id'] = f"{normalized_name}-{current_date}"
            
        # Add timestamp
        if not item.get('timestamp'):
            item['timestamp'] = datetime.now().isoformat()
            
        # Clean text fields
        self._clean_text_fields(item)
        
        # Save to JSON file
        self._save_to_json(item)
        
        return item
    
    def _clean_text_fields(self, item):
        """Clean and normalize text fields in the item."""
        # Clean text values (basic normalization)
        for field in ['raw_content', 'full_name', 'political_affiliation']:
            if field in item and item[field] and isinstance(item[field], str):
                # Remove excessive whitespace
                item[field] = ' '.join(item[field].split())
                
        # Clean list fields
        for field in ['speeches', 'statements', 'public_tweets', 'interviews', 
                      'press_releases', 'voting_record', 'sponsored_bills']:
            if field in item and item[field]:
                # Ensure it's a list
                if not isinstance(item[field], list):
                    item[field] = [item[field]]
                    
                # Clean each text item in the list
                item[field] = [' '.join(text.split()) for text in item[field] if text]
                
                # Remove empty items
                item[field] = [text for text in item[field] if text]
    
    def _save_to_json(self, item):
        """Save the processed item to a JSON file."""
        try:
            # Convert item to dict
            item_dict = dict(item)
            
            # Define file path
            file_path = self.data_dir / f"{item['id']}.json"
            
            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(item_dict, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"Saved data for {item.get('name')} to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving data: {e}")
            
        return item 