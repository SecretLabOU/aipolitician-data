# scripts/setup_chroma.py

import chromadb
from chromadb.config import Settings

def main():
    # The new config approach for local persistent storage:
    client = chromadb.Client(
        Settings(
            # Optional: turn off telemetry if you want
            anonymized_telemetry=False,
            # Just specify the folder path
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
    
    # Data is automatically persisted when using persist_directory
    print("Chroma setup complete. Test doc added.")

if __name__ == "__main__":
    main()
