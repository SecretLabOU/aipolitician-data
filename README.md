# AI Politician Data

This repository contains tools for scraping, formatting, and querying data about politicians for use in AI applications.

## Project Structure

- **scraper/**: Contains scripts for scraping politician data from various sources
  - `politician_scraper.py`: Main scraper for politician data
  - `search_utility.py`: Utility for searching politician data without using ChromaDB

- **formatter/**: Contains scripts for formatting raw politician data
  - `data_formatter.py`: Formats raw data into a structure suitable for RAG applications
  - `requirements.txt`: Specific requirements for the formatter component
  - `setup.sh`: Setup script for the formatter component

- **scripts/**: Contains scripts for loading and querying data
  - `chroma_patched.py`: Compatibility patch for ChromaDB to work with NumPy 2.0
  - `chroma_config_patched.py`: Configuration for ChromaDB with NumPy 2.0 compatibility
  - `chroma_setup.py`: Script to set up ChromaDB
  - `ingest_data_patched.py`: Script to ingest formatted data into ChromaDB
  - `query_data_patched.py`: Script to query data from ChromaDB
  - `diagnose_chroma.py`: Diagnostic script for ChromaDB
  - `load_formatted_data.py`: Script to load formatted data without using ChromaDB

- **data/**: Contains data directories
  - `politicians/`: Raw politician data
  - `formatted/`: Formatted politician data
  - `chroma_db/`: ChromaDB database

## Getting Started

1. **Setup dependencies**:
   ```
   # Install requirements
   pip install -r requirements.txt
   
   # Set up the formatter
   chmod +x formatter/setup.sh
   ./formatter/setup.sh
   ```

2. **Scrape politician data**:
   ```
   python scraper/politician_scraper.py "Politician Name"
   ```

3. **Format the data**:
   ```
   python formatter/data_formatter.py
   ```

4. **Set up ChromaDB and load data**:
   ```
   # One-step setup
   chmod +x setup_chroma_db.sh
   ./setup_chroma_db.sh
   
   # Or run individual steps
   python scripts/chroma_setup.py
   python scripts/ingest_data_patched.py data/formatted/formatted_*.json
   ```

5. **Query the data**:
   ```
   python scripts/query_data_patched.py --query "What are Bernie Sanders' views on healthcare?" --politician "Bernie Sanders" --results 3
   ```

## ChromaDB Compatibility

This project includes a patch for ChromaDB to work with NumPy 2.0. The patch adds back deprecated NumPy types that were removed in NumPy 2.0.

- If you encounter any issues with ChromaDB, run the diagnostic script:
  ```
  python scripts/diagnose_chroma.py
  ```

## Alternative Data Loading

If you prefer not to use ChromaDB, you can use the `load_formatted_data.py` script to generate embeddings:

```
python scripts/load_formatted_data.py data/formatted/*.json --output-dir data/embeddings
```

## Example Queries

- Basic query:
  ```
  python scripts/query_data_patched.py --query "healthcare"
  ```

- Query with filters:
  ```
  python scripts/query_data_patched.py --query "economy" --politician "Elizabeth Warren" --type "wikipedia_content"
  ```

- Query with more results:
  ```
  python scripts/query_data_patched.py --query "foreign policy" --results 5
  ``` 