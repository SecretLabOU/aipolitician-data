#!/usr/bin/env python3
"""
Ingest politician data into ChromaDB using NumPy 2.0 compatibility patch.
"""

import json
import os
import sys
import glob
import argparse
from collections import defaultdict
from chroma_config_patched import get_chroma_client, print_collections, DB_DIR

# Get the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the project root directory (parent of scripts)
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Default data directory path for formatted data
DEFAULT_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "formatted")
DEFAULT_DATA_PATTERN = os.path.join(DEFAULT_DATA_DIR, "formatted_*.json")

def get_text_from_entry(entry, field_path):
    """Extract text from a nested structure using dot notation field path"""
    if not field_path or not entry:
        return None
        
    parts = field_path.split('.')
    current = entry
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    
    return current if isinstance(current, str) else None

def ingest_politician(entry, collection):
    """
    Store each entry from the formatted data as a separate document in ChromaDB.
    
    Returns:
        dict: Statistics about what was ingested
    """
    # Initialize stats
    stats = defaultdict(int)
    
    # Verify required fields
    if "id" not in entry:
        print(f"Error: Missing required field 'id' in entry. Skipping.")
        return stats
    
    politician_id = entry["id"]
    politician_name = entry.get("name", "Unknown")
    
    # Process all entries
    if "entries" in entry and isinstance(entry["entries"], list):
        for idx, item in enumerate(entry["entries"]):
            if not isinstance(item, dict) or "text" not in item or not item["text"]:
                continue
                
            # Generate a unique document ID
            doc_id = f"{politician_id}_entry_{idx}"
            
            # Extract metadata from the item
            metadata = {
                "politician_id": politician_id,
                "politician_name": politician_name,
                "type": item.get("type", "unknown"),
                "source_url": item.get("source_url", ""),
                "timestamp": item.get("timestamp", ""),
            }
            
            # Add specific metadata fields if present
            if "section_name" in item:
                metadata["section_name"] = item["section_name"]
                
            if "platform" in item:
                metadata["platform"] = item["platform"]
                
            # Add the document to ChromaDB
            try:
                collection.add(
                    documents=[item["text"]],
                    ids=[doc_id],
                    metadatas=[metadata]
                )
                stats[item.get("type", "unknown")] += 1
            except Exception as e:
                print(f"Error adding entry {idx} for {politician_name}: {e}")
    
    return stats

def main():
    # Set up argument parser for better command line handling
    parser = argparse.ArgumentParser(description='Ingest politician data into ChromaDB')
    parser.add_argument('files', nargs='*', help='Files to ingest (accepts glob patterns)')
    parser.add_argument('--data-pattern', help='Glob pattern for data files to ingest')
    args = parser.parse_args()
    
    # Get the client from the shared config
    client = get_chroma_client()
    
    # Create or get the collection
    politicians_collection = client.get_or_create_collection("politicians")
    
    # Get data files from command line arguments or use default
    data_files = []
    
    # First check if data-pattern is provided
    if args.data_pattern:
        # Expand the pattern to actual files
        data_files.extend(glob.glob(args.data_pattern))
    
    # Then handle positional arguments which could be individual files or glob patterns
    if args.files:
        for arg in args.files:
            # If the argument is a glob pattern, expand it
            if '*' in arg or '?' in arg:
                expanded_files = glob.glob(arg)
                data_files.extend(expanded_files)
            else:
                data_files.append(arg)
    
    # If no files were specified through either method, use the default pattern
    if not data_files:
        data_files = glob.glob(DEFAULT_DATA_PATTERN)
    
    # Remove duplicates and sort
    data_files = sorted(set(data_files))
    
    if not data_files:
        print(f"Error: No data files found. Tried default pattern: {DEFAULT_DATA_PATTERN}")
        sys.exit(1)
    
    print(f"Will process {len(data_files)} files:")
    for file in data_files:
        print(f"  - {file}")
    
    # Initialize overall statistics
    total_files_processed = 0
    total_documents_added = 0
    overall_stats = defaultdict(int)
    politicians_processed = []
    
    # Process each file
    for data_file in data_files:
        # Check if file exists
        if not os.path.exists(data_file):
            print(f"Error: Data file not found: {data_file}")
            continue
        
        print(f"\nProcessing: {data_file}")
        
        # Load data file
        try:
            with open(data_file, "r") as f:
                entry = json.load(f)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {data_file}")
            continue
        except Exception as e:
            print(f"Error reading {data_file}: {e}")
            continue
        
        # Ingest into Chroma
        politician_name = entry.get("name", "Unknown")
        
        print(f"Ingesting data for: {politician_name}")
        
        stats = ingest_politician(entry, politicians_collection)
        
        # Update statistics
        total_files_processed += 1
        politicians_processed.append(politician_name)
        
        # Count total documents added
        docs_added = sum(stats.values())
        total_documents_added += docs_added
        
        # Update overall stats
        for field, count in stats.items():
            overall_stats[field] += count
        
        print(f"Added {docs_added} documents for {politician_name}")
        for field, count in sorted(stats.items()):
            print(f"  - {field}: {count} items")
    
    # Print overall summary
    print("\n========== Ingestion Summary ==========")
    print(f"Processed {total_files_processed} files")
    print(f"Added {total_documents_added} documents total")
    print(f"Politicians processed: {', '.join(politicians_processed)}")
    print("\nDocuments by type:")
    for field, count in sorted(overall_stats.items()):
        print(f"  - {field}: {count} items")
    
    print(f"\nDatabase location: {DB_DIR}")
    
    # Show the available collections after ingestion
    print("\nChroma Collections:")
    print_collections(client)

if __name__ == "__main__":
    main() 