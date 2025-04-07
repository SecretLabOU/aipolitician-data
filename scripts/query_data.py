# scripts/query_data.py
import sys
from chromadb.errors import NotFoundError
from chroma_config import get_chroma_client, print_collections, DB_DIR

def main():
    # Get the client from the shared config
    client = get_chroma_client()
    
    try:
        # Try to get the collection
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
        
        # List available collections to help troubleshoot
        print_collections(client)
        
        # Try to recreate the collection as a fallback
        print("\nAttempting to create the collection as a fallback...")
        try:
            politicians_collection = client.create_collection("politicians")
            print("Created empty 'politicians' collection. Please run ingest_data.py to add data.")
        except Exception as e:
            print(f"Failed to create collection: {e}")
        
        sys.exit(1)

if __name__ == "__main__":
    main()
