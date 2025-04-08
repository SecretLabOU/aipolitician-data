import json
import os
from datetime import datetime
from itemadapter import ItemAdapter


class AipoliticianPipeline:
    def __init__(self):
        self.items = {}
        self.output_dir = 'output/politicians'
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Add metadata
        adapter['scraped_at'] = datetime.now().isoformat()
        
        # Generate a unique ID if not already present
        if not adapter.get('id'):
            adapter['id'] = self._generate_id(adapter)
        
        # Store the item for later
        self.items[adapter['id']] = dict(adapter)
        
        return item
    
    def _generate_id(self, adapter):
        """Generate a unique ID based on name and source"""
        name = adapter.get('name', '')
        source = adapter.get('source_type', '')
        return f"{name.lower().replace(' ', '_')}_{source}".strip('_')
    
    def close_spider(self, spider):
        """Save all items to individual JSON files when spider closes"""
        for item_id, item in self.items.items():
            # Save to individual JSON file
            filename = os.path.join(self.output_dir, f"{item_id}.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(item, f, ensure_ascii=False, indent=2)
        
        # Also save an index file with all items
        index_file = os.path.join(self.output_dir, 'index.json')
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.items.values()), f, ensure_ascii=False, indent=2) 