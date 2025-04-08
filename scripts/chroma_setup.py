#!/usr/bin/env python3
"""
Setup script for the ChromaDB database with NumPy 2.0 compatibility.
This is the primary setup script for the ChromaDB database.
"""

from chroma_config_patched import get_chroma_client, print_collections, DB_DIR
import os
import sys

def setup_database():
    """Set up the ChromaDB database with initial test data."""
    # Get the client from the shared config
    client = get_chroma_client()
    
    # Create or get the collection
    politicians_collection = client.get_or_create_collection("politicians")
    
    # Add a test doc (optional)
    politicians_collection.add(
        documents=["This is a test doc for John Doe."],
        ids=["test_john_doe_001"],
        metadatas=[{"politician_id": "john-doe-123"}]
    )
    
    print("Chroma setup complete. Test doc added.")
    print(f"Database location: {DB_DIR}")
    
    # List available collections
    print_collections(client)
    
    return True

def main():
    print("Setting up ChromaDB with NumPy 2.0 compatibility.")
    
    # Create the database directory if it doesn't exist
    os.makedirs(DB_DIR, exist_ok=True)
    
    # Run the setup
    setup_result = setup_database()
    
    if setup_result:
        print("\nSetup completed successfully!")
        print("\nNext steps:")
        print("1. Run scripts/ingest_data_patched.py to add politician data")
        print("2. Run scripts/query_data_patched.py to query the database")
    else:
        print("\nSetup failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 