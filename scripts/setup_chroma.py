# scripts/setup_chroma.py
import chromadb
from chromadb.config import Settings

def main():
    # Configure Chroma to store files in /opt/chroma_db
    client = chromadb.Client(
        Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="/opt/chroma_db"
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
    
    # Persist to disk
    client.persist()
    print("Chroma setup complete. Test doc added.")

if __name__ == "__main__":
    main()
