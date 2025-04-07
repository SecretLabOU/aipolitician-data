# scripts/ingest_data.py
import json
import chromadb
from chromadb.config import Settings
import os
import sys

# Get the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the project root directory (parent of scripts)
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Default data file path - will be overridden by command line argument if provided
DEFAULT_DATA_FILE = os.path.join(PROJECT_ROOT, "data", "sample_politician.json")

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

def get_chroma_client():
    return chromadb.Client(
        Settings(
            persist_directory=DB_DIR
        )
    )

def ingest_politician(entry: dict, collection):
    """
    Store each relevant piece of text as a separate document.
    """
    politician_id = entry["id"]
    
    # Common metadata for all docs referencing this politician
    base_metadata = {
        "politician_id": politician_id,
        "politician_name": entry.get("name", ""),
        "political_affiliation": entry.get("political_affiliation", ""),
        "date_of_birth": entry.get("date_of_birth", ""),
        # ... any other universal fields
    }

    # 1) raw_content
    if "raw_content" in entry and entry["raw_content"]:
        collection.add(
            documents=[entry["raw_content"]],
            ids=[f"{politician_id}_raw"],
            metadatas=[{
                **base_metadata,
                "type": "raw_content",
                "source_url": entry.get("source_url", ""),   # or store a list if multiple
                "timestamp": entry.get("timestamp", "")
            }]
        )

    # 2) speeches
    speeches = entry.get("speeches", [])
    for idx, speech_text in enumerate(speeches):
        doc_id = f"{politician_id}_speech_{idx}"
        metadata = {
            **base_metadata,
            "type": "speech",
            "source_url": entry.get("source_url", ""),
            "timestamp": entry.get("timestamp", "")
        }
        # If each speech came from a different URL, store that logic separately.
        
        collection.add(
            documents=[speech_text],
            ids=[doc_id],
            metadatas=[metadata]
        )

    # 3) statements
    statements = entry.get("statements", [])
    for idx, statement_text in enumerate(statements):
        doc_id = f"{politician_id}_statement_{idx}"
        metadata = {
            **base_metadata,
            "type": "statement",
            "source_url": entry.get("source_url", ""),
            "timestamp": entry.get("timestamp", "")
        }
        
        collection.add(
            documents=[statement_text],
            ids=[doc_id],
            metadatas=[metadata]
        )

    # Similarly for sponsored_bills, voting_record, etc., if you want them as text docs:
    # ...
    
def main():
    # First, check directory access
    if not check_directory_access(DB_DIR):
        sys.exit(1)
    
    client = get_chroma_client()
    politicians_collection = client.get_or_create_collection("politicians")
    
    # Use command line argument if provided, otherwise use default
    data_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DATA_FILE
    
    # Check if file exists
    if not os.path.exists(data_file):
        print(f"Error: Data file not found: {data_file}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Script directory: {SCRIPT_DIR}")
        print(f"Project root: {PROJECT_ROOT}")
        sys.exit(1)
    
    # Load data file
    try:
        with open(data_file, "r") as f:
            entry = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {data_file}")
        sys.exit(1)

    # Ingest into Chroma
    ingest_politician(entry, politicians_collection)

    # Data is automatically persisted when using persist_directory
    print(f"Ingested data from {data_file} successfully!")
    print(f"Database location: {DB_DIR}")

if __name__ == "__main__":
    main()
