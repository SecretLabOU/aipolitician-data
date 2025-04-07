# scripts/test_chroma_full.py
"""
Test script that performs all operations (setup, ingest, query) in a single script
to verify that Chroma is working properly when all operations are in the same process.
"""

import os
import json
import sys
from chroma_config import get_chroma_client, DB_DIR

# Get the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the project root directory (parent of scripts)
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
# Default data file path
DEFAULT_DATA_FILE = os.path.join(PROJECT_ROOT, "data", "sample_politician.json")

def main():
    print("=== Chroma Full Test ===")
    print(f"Database directory: {DB_DIR}")
    
    # Step 1: Get client (using PersistentClient from config)
    print("\nStep 1: Getting Chroma client...")
    client = get_chroma_client()
    
    # Step 2: Create collection
    print("\nStep 2: Creating collection...")
    politicians_collection = client.get_or_create_collection("politicians")
    
    # Add a test doc
    print("\nStep 3: Adding test document...")
    politicians_collection.add(
        documents=["This is a test doc for John Doe."],
        ids=["test_john_doe_001"],
        metadatas=[{"politician_id": "john-doe-123"}]
    )
    
    # Step 4: List collections to verify
    print("\nStep 4: Listing collections...")
    collections = client.list_collections()
    print("Available collections:")
    for coll in collections:
        print(f" - {coll.name}")
    
    # Step 5: Load and ingest data
    print("\nStep 5: Loading and ingesting data...")
    data_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DATA_FILE
    
    if not os.path.exists(data_file):
        print(f"Error: Data file not found: {data_file}")
        sys.exit(1)
    
    try:
        with open(data_file, "r") as f:
            entry = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {data_file}")
        sys.exit(1)
    
    # Ingest the politician data
    print("\nStep 6: Ingesting politician data...")
    politician_id = entry["id"]
    
    # Common metadata
    base_metadata = {
        "politician_id": politician_id,
        "politician_name": entry.get("name", ""),
        "political_affiliation": entry.get("political_affiliation", ""),
    }
    
    # Add raw content if available
    if "raw_content" in entry and entry["raw_content"]:
        print("  - Adding raw content...")
        politicians_collection.add(
            documents=[entry["raw_content"]],
            ids=[f"{politician_id}_raw"],
            metadatas=[{
                **base_metadata,
                "type": "raw_content",
            }]
        )
    
    # Add speeches if available
    speeches = entry.get("speeches", [])
    if speeches:
        print(f"  - Adding {len(speeches)} speeches...")
        for idx, speech_text in enumerate(speeches):
            doc_id = f"{politician_id}_speech_{idx}"
            politicians_collection.add(
                documents=[speech_text],
                ids=[doc_id],
                metadatas=[{
                    **base_metadata,
                    "type": "speech",
                }]
            )
    
    # Verify collection after ingestion
    print("\nStep 7: Verifying collection after ingestion...")
    collections = client.list_collections()
    print("Available collections:")
    for coll in collections:
        print(f" - {coll.name}")
    
    # Get the collection again explicitly
    print("\nStep 8: Getting the collection again...")
    try:
        collection = client.get_collection("politicians")
        print("Collection 'politicians' found.")
        
        # Count documents in collection
        count = len(collection.get()["ids"])
        print(f"Collection contains {count} documents.")
    except Exception as e:
        print(f"Error getting collection: {e}")
    
    # Query the collection
    print("\nStep 9: Querying the collection...")
    try:
        results = politicians_collection.query(
            query_texts=["What did the politician say about healthcare?"],
            n_results=3
        )
        
        print("Query Results:")
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                print(f"\nResult {i+1}:")
                print(f"Document: {doc[:100]}..." if len(doc) > 100 else f"Document: {doc}")
                print(f"ID: {results['ids'][0][i]}")
                if results['metadatas'] and results['metadatas'][0]:
                    print(f"Metadata: {results['metadatas'][0][i]}")
        else:
            print("No results found.")
    except Exception as e:
        print(f"Error querying collection: {e}")
    
    print("\nFull test complete.")

if __name__ == "__main__":
    main() 