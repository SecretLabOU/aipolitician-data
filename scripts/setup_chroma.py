# scripts/setup_chroma.py

from chroma_config import get_chroma_client, print_collections, DB_DIR

def main():
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

if __name__ == "__main__":
    main()
