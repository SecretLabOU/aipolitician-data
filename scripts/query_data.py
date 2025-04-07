# scripts/query_data.py
import chromadb
from chromadb.config import Settings
import sys
import os
from chromadb.errors import NotFoundError

# Database directory path
DB_DIR = "/opt/chroma_db"

def check_directory_access(directory):
    """Check if the directory exists and is readable."""
    # Check if directory exists
    if not os.path.exists(directory):
        print(f"Error: Database directory {directory} does not exist.")
        print("Please run setup_chroma.py first to create the database.")
        return False
    
    # Check if directory is readable
    if not os.access(directory, os.R_OK):
        print(f"Error: No read permission for directory {directory}")
        print(f"Please fix permissions with: sudo chmod +r {directory}")
        return False
    
    return True

def main():
    # First, check directory access
    if not check_directory_access(DB_DIR):
        sys.exit(1)
    
    client = chromadb.Client(
        Settings(
            persist_directory=DB_DIR
        )
    )
    
    try:
        collection = client.get_collection("politicians")
        
        # Example: retrieve the top 3 docs most relevant to a question about healthcare
        results = collection.query(
            query_texts=["What did John Doe say about healthcare?"],
            n_results=3
        )
        
        # The result is a dict with keys: 'ids', 'embeddings', 'metadatas', 'documents'
        print("Query Results:\n", results)
    
    except NotFoundError:
        print("Error: Collection 'politicians' not found in the database.")
        print("\nPossible solutions:")
        print("1. Run the ingest_data.py script first to create the collection and add data.")
        print("2. Check that you're using the correct database path (/opt/chroma_db).")
        print("3. Ensure you have write permissions to the database directory.")
        print("\nAvailable collections:")
        try:
            collections = client.list_collections()
            if collections:
                for coll in collections:
                    print(f" - {coll.name}")
            else:
                print(" (No collections found)")
        except Exception as e:
            print(f"Could not list collections: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
