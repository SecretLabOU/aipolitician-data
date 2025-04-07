# scripts/query_data.py
import chromadb
from chromadb.config import Settings

def main():
    client = chromadb.Client(
        Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="/opt/chroma_db"
        )
    )
    
    collection = client.get_collection("politicians")
    
    # Example: retrieve the top 3 docs most relevant to a question about healthcare
    results = collection.query(
        query_texts=["What did John Doe say about healthcare?"],
        n_results=3
    )
    
    # The result is a dict with keys: 'ids', 'embeddings', 'metadatas', 'documents'
    print("Query Results:\n", results)
    
if __name__ == "__main__":
    main()
