#!/bin/bash

# setup_chroma_db.sh - A script to set up the ChromaDB environment with NumPy 2.0 compatibility patches
# This script handles the entire process of setting up ChromaDB, loading formatted politician data,
# and running a test query to verify everything works.

set -e  # Exit on any error

echo "===== Setting up ChromaDB environment with NumPy 2.0 compatibility patches ====="

# Make all Python scripts executable
echo "Making Python scripts executable..."
chmod +x scripts/chroma_patched.py
chmod +x scripts/chroma_setup.py
chmod +x scripts/ingest_data_patched.py
chmod +x scripts/query_data_patched.py
chmod +x scripts/diagnose_chroma.py

# Create the data directory for ChromaDB if it doesn't exist
echo "Creating ChromaDB data directory..."
mkdir -p data/chroma_db

# Verify the NumPy patch works
echo "Testing NumPy patch..."
cd scripts
python -c "import chroma_patched; print('NumPy patch successful!')"
cd ..

# Step 1: Set up ChromaDB
echo ""
echo "===== Step 1: Setting up ChromaDB ====="
cd scripts
python chroma_setup.py
cd ..

# Step 2: Ingest formatted politician data into ChromaDB
echo ""
echo "===== Step 2: Ingesting politician data into ChromaDB ====="
cd scripts
# Instead of using shell glob which might not work consistently across platforms,
# let Python handle finding the formatted data files
python ingest_data_patched.py --data-pattern="../data/formatted/formatted_*.json"
cd ..

# Step 3: Run a test query to verify the setup
echo ""
echo "===== Step 3: Running a test query ====="
cd scripts
python query_data_patched.py --query "What are Bernie Sanders' views on healthcare?" --politician "Bernie Sanders" --results 3
cd ..

echo ""
echo "===== ChromaDB setup complete! ====="
echo "You can now use the following scripts to interact with the database:"
echo "  - scripts/query_data_patched.py: Query the database"
echo "  - scripts/ingest_data_patched.py: Ingest additional data"
echo "  - scripts/diagnose_chroma.py: Diagnose and troubleshoot database issues"
echo ""
echo "Example query:"
echo "  python scripts/query_data_patched.py --query \"What does Elizabeth Warren think about financial regulation?\" --politician \"Elizabeth Warren\"" 