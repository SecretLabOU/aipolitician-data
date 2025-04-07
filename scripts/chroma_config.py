"""
Shared configuration for all Chroma scripts.
This ensures consistency across all scripts.
"""

import os
import sys
import chromadb
from chromadb.config import Settings

# Database directory path - centralized configuration
DB_DIR = "/opt/chroma_db"

def check_directory_access(directory, need_write=True):
    """Check if the directory exists and has proper permissions."""
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
    
    # Check permissions
    has_read = os.access(directory, os.R_OK)
    has_write = os.access(directory, os.W_OK)
    
    if not has_read:
        print(f"Error: No read permission for directory {directory}")
        print(f"Please fix permissions with: sudo chmod +r {directory}")
        return False
    
    if need_write and not has_write:
        print(f"Error: No write permission for directory {directory}")
        print(f"Please fix permissions with: sudo chmod +w {directory}")
        return False
    
    return True

def get_chroma_client():
    """Get a consistent Chroma client with proper error handling."""
    try:
        # Check directory permissions first
        if not check_directory_access(DB_DIR):
            sys.exit(1)
            
        # Create the client
        client = chromadb.Client(
            Settings(
                anonymized_telemetry=False,
                persist_directory=DB_DIR
            )
        )
        
        return client
    except Exception as e:
        print(f"Error creating Chroma client: {str(e)}")
        sys.exit(1)

def print_collections(client):
    """Print all available collections."""
    try:
        collections = client.list_collections()
        print("\nAvailable collections:")
        if collections:
            for coll in collections:
                print(f" - {coll.name}")
        else:
            print(" (No collections found)")
    except Exception as e:
        print(f"Error listing collections: {e}") 