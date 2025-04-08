# scripts/query_data.py
import sys
import argparse
from chromadb.errors import NotFoundError
from chroma_config import get_chroma_client, print_collections, DB_DIR

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Query the politicians database.")
    parser.add_argument("--query", "-q", type=str, default="What did the politician say about healthcare?",
                        help="Query text to search for")
    parser.add_argument("--results", "-n", type=int, default=3,
                        help="Number of results to return")
    parser.add_argument("--politician", "-p", type=str,
                        help="Filter by politician name")
    parser.add_argument("--type", "-t", type=str,
                        help="Filter by document type (e.g., speech, statement, raw_content)")
    return parser.parse_args()

def main():
    # Parse arguments
    args = parse_arguments()
    
    # Get the client from the shared config
    client = get_chroma_client()
    
    try:
        # Try to get the collection
        collection = client.get_collection("politicians")
        
        # Build query parameters
        query_params = {
            "query_texts": [args.query],
            "n_results": args.results
        }
        
        # Add filters if specified
        where_clause = {}
        if args.politician:
            where_clause["politician_name"] = args.politician
        if args.type:
            where_clause["type"] = args.type
        
        if where_clause:
            query_params["where"] = where_clause
            print(f"Using filters: {where_clause}")
        
        # Execute the query
        results = collection.query(**query_params)
        
        # The result is a dict with keys: 'ids', 'embeddings', 'metadatas', 'documents'
        print("\nQuery Results:")
        
        if not results["documents"] or not results["documents"][0]:
            print("No results found.")
            return
        
        # Display results in a more readable format
        for i, (doc, metadata, doc_id) in enumerate(zip(
            results["documents"][0], 
            results["metadatas"][0],
            results["ids"][0]
        )):
            print(f"\n--- Result {i+1} ---")
            print(f"ID: {doc_id}")
            print(f"Politician: {metadata.get('politician_name', 'Unknown')}")
            print(f"Type: {metadata.get('type', 'Unknown')}")
            print(f"Text: {doc[:150]}..." if len(doc) > 150 else f"Text: {doc}")
            print(f"Source: {metadata.get('source_url', 'Unknown')}")
            
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
