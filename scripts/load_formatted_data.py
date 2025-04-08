#!/usr/bin/env python3
"""
Script to load formatted data and generate embeddings without using Chroma.
This script is compatible with NumPy 2.0.
"""

import os
import json
import argparse
import glob
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Constants
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 1000  # Maximum number of texts to embed at once

class PoliticianDataLoader:
    """Load and process politician data without using Chroma."""
    
    def __init__(self, output_dir: str, embedding_model_name: str = DEFAULT_EMBEDDING_MODEL):
        """Initialize with an output directory and embedding model."""
        self.output_dir = output_dir
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.stats = {
            "processed_files": 0,
            "documents_added": 0,
            "skipped_files": 0,
        }
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Embed a list of texts using the embedding model."""
        return self.embedding_model.encode(texts, convert_to_numpy=True)
    
    def process_file(self, file_path: str) -> Tuple[int, List[Dict[str, Any]]]:
        """Process a single JSON file and generate embeddings."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                print(f"Warning: {file_path} does not contain a list. Skipping.")
                return 0, []
            
            processed_data = []
            for entry in data:
                if not isinstance(entry, dict) or 'text' not in entry:
                    continue
                    
                text = entry['text']
                if not text or not isinstance(text, str):
                    continue
                
                metadata = {k: v for k, v in entry.items() if k != 'text'}
                processed_data.append({
                    'text': text,
                    'metadata': metadata
                })
            
            # Process in chunks to avoid memory issues
            all_processed = []
            for i in range(0, len(processed_data), CHUNK_SIZE):
                chunk = processed_data[i:i+CHUNK_SIZE]
                texts = [item['text'] for item in chunk]
                
                # Generate embeddings
                embeddings = self.embed_texts(texts)
                
                # Add embeddings to the data
                for j, item in enumerate(chunk):
                    item['embedding'] = embeddings[j].tolist()  # Convert to list for JSON serialization
                    all_processed.append(item)
            
            return len(all_processed), all_processed
                
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            self.stats["skipped_files"] += 1
            return 0, []
    
    def save_embeddings(self, data: List[Dict[str, Any]], output_file: str):
        """Save embeddings and metadata to a JSON file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_data(self, input_glob: str):
        """Process data files matching the glob pattern."""
        files = glob.glob(input_glob)
        
        if not files:
            print(f"No files found matching '{input_glob}'")
            return
        
        print(f"Found {len(files)} files to process")
        
        # Clear stats
        self.stats = {
            "processed_files": 0,
            "documents_added": 0,
            "skipped_files": 0,
        }
        
        all_processed_data = []
        
        # Process each file with a progress bar
        for file_path in tqdm(files, desc="Processing files"):
            count, processed_data = self.process_file(file_path)
            
            if count > 0:
                self.stats["processed_files"] += 1
                self.stats["documents_added"] += count
                all_processed_data.extend(processed_data)
            else:
                self.stats["skipped_files"] += 1
        
        # Save all embeddings to a single file
        output_file = os.path.join(self.output_dir, "embeddings.json")
        self.save_embeddings(all_processed_data, output_file)
        
        # Print summary
        print("\nSummary:")
        print(f"Total files processed: {self.stats['processed_files']}")
        print(f"Total documents added: {self.stats['documents_added']}")
        print(f"Files skipped: {self.stats['skipped_files']}")
        print(f"Embeddings saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Load formatted politician data and generate embeddings")
    parser.add_argument("input", help="Input files glob pattern (e.g., 'data/formatted/*.json')")
    parser.add_argument("--output-dir", "-o", default="data/embeddings", 
                        help="Output directory for storing embeddings")
    parser.add_argument("--model", "-m", default=DEFAULT_EMBEDDING_MODEL,
                        help=f"Embedding model name (default: {DEFAULT_EMBEDDING_MODEL})")
    
    args = parser.parse_args()
    
    loader = PoliticianDataLoader(
        output_dir=args.output_dir,
        embedding_model_name=args.model
    )
    
    loader.load_data(args.input)

if __name__ == "__main__":
    main() 