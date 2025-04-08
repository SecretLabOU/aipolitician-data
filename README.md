# AI Politician Data

This repository contains tools for scraping, formatting, and querying data about politicians for use in AI applications.

## Project Structure

- **scraper/**: Contains scripts for scraping politician data from various sources
  - `politician_scraper.py`: Main scraper for politician data
  - `search_utility.py`: Utility for searching politician data without using ChromaDB

- **formatter/**: Contains scripts for formatting raw politician data
  - `data_formatter.py`: Formats raw data into a structure suitable for RAG applications

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

### Using the All-in-One Setup Script

The easiest way to get started is to use the all-in-one setup script that handles the complete pipeline:

```bash
# Make the script executable
chmod +x setup_politician.sh

# Run the setup script with a politician name
./setup_politician.sh "Bernie Sanders"
```

This script will:
1. Create and configure a Conda environment
2. Install all dependencies
3. Set up the ChromaDB database
4. Scrape data for the specified politician
5. Format the data
6. Load the data into ChromaDB
7. Run a test query to verify everything works

### Manual Steps

If you prefer to run the steps manually:

1. **Setup dependencies**:
   ```bash
   # Install requirements
   pip install -r requirements.txt
   
   # Download required NLP models
   python -m spacy download en_core_web_sm
   python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
   ```

2. **Scrape politician data**:
   ```bash
   python scraper/politician_scraper.py "Politician Name"
   ```

3. **Format the data**:
   ```bash
   python formatter/data_formatter.py --single data/politicians/politician_name.json
   ```

4. **Set up ChromaDB and load data**:
   ```bash
   # Setup ChromaDB
   python scripts/chroma_setup.py
   
   # Ingest the formatted data
   python scripts/ingest_data_patched.py data/formatted/formatted_*.json
   ```

5. **Query the data**:
   ```bash
   python scripts/query_data_patched.py --query "What are Bernie Sanders' views on healthcare?" --politician "Bernie Sanders" --results 3
   ```

## ChromaDB Compatibility

This project includes a patch for ChromaDB to work with NumPy 2.0. The patch adds back deprecated NumPy types that were removed in NumPy 2.0.

- If you encounter any issues with ChromaDB, run the diagnostic script:
  ```bash
  python scripts/diagnose_chroma.py
  ```

## Alternative Data Loading

If you prefer not to use ChromaDB, you can use the `load_formatted_data.py` script to generate embeddings:

```bash
python scripts/load_formatted_data.py data/formatted/*.json --output-dir data/embeddings
```

## Example Queries

- Basic query:
  ```bash
  python scripts/query_data_patched.py --query "healthcare"
  ```

- Query with filters:
  ```bash
  python scripts/query_data_patched.py --query "economy" --politician "Elizabeth Warren" --type "wikipedia_content"
  ```

- Query with more results:
  ```bash
  python scripts/query_data_patched.py --query "foreign policy" --results 5
  ``` 