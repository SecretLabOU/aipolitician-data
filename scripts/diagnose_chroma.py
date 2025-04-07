"""
Diagnostic script for Chroma database.
This script performs various checks to help troubleshoot issues with the Chroma database.
"""

import os
import sys
import shutil
from chroma_config import get_chroma_client, print_collections, DB_DIR

def check_db_files():
    """Check if the database files exist and are accessible."""
    print(f"Checking database directory: {DB_DIR}")
    
    if not os.path.exists(DB_DIR):
        print("  - Directory does not exist")
        return False
    
    # Check directory contents
    files = os.listdir(DB_DIR)
    print(f"  - Directory contains {len(files)} files/directories")
    for file in files:
        print(f"    - {file}")
    
    # Expected files/directories in a Chroma DB
    expected = ["chroma.sqlite3", "index"]
    for exp in expected:
        if exp not in files:
            print(f"  - Warning: Expected file/directory '{exp}' not found")
    
    return True

def reset_db():
    """Reset the database by removing all files."""
    response = input(f"Do you want to reset the database at {DB_DIR}? (yes/no): ")
    if response.lower() == "yes":
        try:
            # Save a backup first
            if os.path.exists(DB_DIR):
                backup_dir = f"{DB_DIR}_backup"
                print(f"Creating backup at {backup_dir}")
                shutil.copytree(DB_DIR, backup_dir, dirs_exist_ok=True)
            
            # Clear the directory
            if os.path.exists(DB_DIR):
                shutil.rmtree(DB_DIR)
                os.makedirs(DB_DIR, exist_ok=True)
                print(f"Database at {DB_DIR} has been reset")
            else:
                print(f"Database directory {DB_DIR} doesn't exist, creating it")
                os.makedirs(DB_DIR, exist_ok=True)
                
            return True
        except Exception as e:
            print(f"Error resetting database: {e}")
            return False
    else:
        print("Database reset cancelled")
        return False

def test_collection_creation():
    """Test if we can create and query a collection."""
    try:
        client = get_chroma_client()
        
        # Create a test collection
        test_collection = client.get_or_create_collection("test_collection")
        
        # Add a test document
        test_collection.add(
            documents=["This is a test document for diagnostics."],
            ids=["test_doc_001"],
            metadatas=[{"test": "metadata"}]
        )
        
        # Query the collection
        results = test_collection.query(
            query_texts=["test document"],
            n_results=1
        )
        
        # Verify the results
        if results and results.get("documents") and len(results["documents"][0]) > 0:
            print("Test collection creation and query successful!")
            # Clean up the test collection
            client.delete_collection("test_collection")
            return True
        else:
            print("Test collection query returned no results")
            return False
    except Exception as e:
        print(f"Error testing collection creation: {e}")
        return False

def main():
    print("=== Chroma Database Diagnostic ===")
    
    # Check directory permissions
    print("\n1. Checking directory permissions...")
    if not os.path.exists(DB_DIR):
        print(f"Directory {DB_DIR} doesn't exist")
    else:
        print(f"Read permission: {os.access(DB_DIR, os.R_OK)}")
        print(f"Write permission: {os.access(DB_DIR, os.W_OK)}")
        print(f"Execute permission: {os.access(DB_DIR, os.X_OK)}")
    
    # Check database files
    print("\n2. Checking database files...")
    db_files_exist = check_db_files()
    
    # Create a client and list collections
    print("\n3. Attempting to list collections...")
    try:
        client = get_chroma_client()
        print_collections(client)
    except Exception as e:
        print(f"Error connecting to database: {e}")
    
    # Test collection creation
    print("\n4. Testing collection creation and query...")
    collection_test = test_collection_creation()
    
    # Offer to reset the database if there are issues
    if not db_files_exist or not collection_test:
        print("\n5. Database issues detected. You might want to reset the database.")
        reset_db()
    else:
        print("\n5. No critical issues detected.")
    
    print("\nDiagnostic complete.")

if __name__ == "__main__":
    main() 