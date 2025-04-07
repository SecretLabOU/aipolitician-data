# scripts/setup_chroma.py

import chromadb
from chromadb.config import Settings
import os
import sys

# Database directory path
DB_DIR = "/opt/chroma_db"

def check_directory_access(directory):
    """Check if the directory exists and is writable."""
    # Check if directory exists
    if not os.path.exists(directory):
        try:
            print(f"Directory {directory} does not exist. Attempting to create it...")
            os.makedirs(directory, exist_ok=True)
            print(f"Successfully created directory: {directory}")
        except PermissionError:
            print(f"Error: No permission to create directory {directory}")
            print("Please create the directory manually or use a different path.")
            print(f"You can run: sudo mkdir -p {directory} && sudo chown $USER:$USER {directory}")
            return False
    
    # Check if directory is writable
    if not os.access(directory, os.W_OK):
        print(f"Error: No write permission for directory {directory}")
        print(f"Please fix permissions with: sudo chown $USER:$USER {directory}")
        return False
    
    return True

def main():
    # First, check directory access
    if not check_directory_access(DB_DIR):
        sys.exit(1)
        
    try:
        # The new config approach for local persistent storage:
        client = chromadb.Client(
            Settings(
                # Optional: turn off telemetry if you want
                anonymized_telemetry=False,
                # Just specify the folder path
                persist_directory=DB_DIR
            )
        )
        
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
        collections = client.list_collections()
        print("\nAvailable collections:")
        for coll in collections:
            print(f" - {coll.name}")
            
    except Exception as e:
        print(f"Error setting up Chroma: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
