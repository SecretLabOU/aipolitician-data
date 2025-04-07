# scripts/ingest_data.py
import json
import chromadb
from chromadb.config import Settings
import os

# Adjust or remove if you have multiple data files or a DB to fetch data from:
DATA_FILE = os.path.join("data", "sample_politician.json")

def get_chroma_client():
    return chromadb.Client(
        Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="/opt/chroma_db"
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
    client = get_chroma_client()
    politicians_collection = client.get_or_create_collection("politicians")
    
    # Load data file (for example, a single JSON).
    # If you have multiple politicians, you might store them in a list, or read multiple files.
    with open(DATA_FILE, "r") as f:
        entry = json.load(f)

    # Ingest into Chroma
    ingest_politician(entry, politicians_collection)

    # Persist to disk
    client.persist()
    print(f"Ingested data from {DATA_FILE} successfully!")

if __name__ == "__main__":
    main()
