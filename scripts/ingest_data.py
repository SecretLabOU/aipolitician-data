# scripts/ingest_data.py
import json
import os
import sys
import glob
from collections import defaultdict
from chroma_config import get_chroma_client, print_collections, DB_DIR

# Get the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the project root directory (parent of scripts)
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Default data file path - will be overridden by command line argument if provided
DEFAULT_DATA_FILE = os.path.join(PROJECT_ROOT, "data", "sample_politician.json")

# List of fields that are known to contain lists of text data
# This helps identify fields that should be processed similarly to speeches/statements
TEXT_LIST_FIELDS = [
    "speeches", 
    "statements", 
    "public_tweets", 
    "interviews", 
    "press_releases",
    "voting_record", 
    "sponsored_bills", 
    "quotes", 
    "debates"
]

# Fields to skip entirely (non-text or metadata fields that shouldn't be stored as documents)
SKIP_FIELDS = [
    "id", 
    "name", 
    "full_name", 
    "date_of_birth", 
    "political_affiliation", 
    "timestamp", 
    "source_url", 
    "links"
]

def ingest_politician(entry: dict, collection):
    """
    Store each relevant piece of text as a separate document.
    Dynamically handles various field types in the JSON data.
    
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
    
    # Common metadata for all docs referencing this politician
    base_metadata = {
        "politician_id": politician_id,
        "politician_name": entry.get("name", ""),
        "political_affiliation": entry.get("political_affiliation", ""),
        "date_of_birth": entry.get("date_of_birth", ""),
        # ... any other universal fields
    }

    # 1) raw_content (single text document)
    if "raw_content" in entry and entry["raw_content"]:
        try:
            collection.add(
                documents=[entry["raw_content"]],
                ids=[f"{politician_id}_raw"],
                metadatas=[{
                    **base_metadata,
                    "type": "raw_content",
                    "source_url": entry.get("source_url", ""),
                    "timestamp": entry.get("timestamp", "")
                }]
            )
            stats["raw_content"] += 1
        except Exception as e:
            print(f"Error adding raw_content for {politician_id}: {e}")

    # 2) Process all fields containing lists of text (speeches, statements, tweets, etc.)
    for field_name in entry.keys():
        # Skip non-text fields and already processed fields
        if field_name in SKIP_FIELDS or field_name == "raw_content":
            continue
        
        field_data = entry.get(field_name, [])
        
        # If the field is a list, process each item separately
        if isinstance(field_data, list):
            for idx, text_item in enumerate(field_data):
                if not text_item:  # Skip empty items
                    continue
                    
                # Generate a unique document ID
                doc_id = f"{politician_id}_{field_name}_{idx}"
                
                # Create metadata specific to this item
                metadata = {
                    **base_metadata,
                    "type": field_name,  # Use the field name as the type
                    "source_url": entry.get("source_url", ""),
                    "timestamp": entry.get("timestamp", "")
                }
                
                try:
                    collection.add(
                        documents=[text_item],
                        ids=[doc_id],
                        metadatas=[metadata]
                    )
                    stats[field_name] += 1
                except Exception as e:
                    print(f"Error adding {field_name} item {idx} for {politician_id}: {e}")
        # If the field is a string and not in the skip list, treat it as a single document
        elif isinstance(field_data, str) and field_data.strip():
            doc_id = f"{politician_id}_{field_name}"
            metadata = {
                **base_metadata,
                "type": field_name,
                "source_url": entry.get("source_url", ""),
                "timestamp": entry.get("timestamp", "")
            }
            
            try:
                collection.add(
                    documents=[field_data],
                    ids=[doc_id],
                    metadatas=[metadata]
                )
                stats[field_name] += 1
            except Exception as e:
                print(f"Error adding {field_name} for {politician_id}: {e}")
    
    return stats
    
def main():
    # Get the client from the shared config
    client = get_chroma_client()
    
    # Create or get the collection - use get_or_create to ensure it exists
    politicians_collection = client.get_or_create_collection("politicians")
    
    # Get data files from command line arguments
    data_files = []
    
    # Handle command line arguments which could be individual files or glob patterns
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            # If the argument is a glob pattern, expand it
            if '*' in arg or '?' in arg:
                expanded_files = glob.glob(arg)
                data_files.extend(expanded_files)
            else:
                data_files.append(arg)
    else:
        # Use default if no arguments provided
        data_files = [DEFAULT_DATA_FILE]
    
    # Remove duplicates and sort
    data_files = sorted(set(data_files))
    
    if not data_files:
        print("Error: No data files specified.")
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
        politician_id = entry.get("id", "unknown")
        politician_name = entry.get("name", "Unknown")
        
        print(f"Ingesting data for: {politician_name} (ID: {politician_id})")
        
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
        for field, count in stats.items():
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
