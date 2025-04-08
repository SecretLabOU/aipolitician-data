#!/usr/bin/env python
"""
Environment checker for the AI Politician Scraper
This script verifies that all dependencies are correctly installed and available.
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

def check_spacy():
    """Check if spaCy is properly installed and the language model is available."""
    print(f"Python interpreter: {sys.executable}")
    
    # Check if spaCy is installed
    spacy_spec = importlib.util.find_spec("spacy")
    if spacy_spec is None:
        print("spaCy is not installed.")
        return False
    
    print("spaCy is installed.")
    
    # Try to import spaCy
    try:
        import spacy
        print(f"spaCy version: {spacy.__version__}")
        
        # Check if the language model is installed
        try:
            nlp = spacy.load("en_core_web_sm")
            print("spaCy language model 'en_core_web_sm' is installed and loaded successfully.")
            return True
        except OSError:
            print("spaCy language model 'en_core_web_sm' is not installed.")
            
            # Attempt to install the model
            try:
                print("Attempting to download spaCy model...")
                from spacy.cli import download
                download("en_core_web_sm")
                # Try loading again
                nlp = spacy.load("en_core_web_sm")
                print("Downloaded and loaded spaCy model successfully.")
                return True
            except Exception as e:
                print(f"Failed to download spaCy model: {e}")
                return False
                
    except ImportError as e:
        print(f"Failed to import spaCy: {e}")
        return False

def check_scrapy():
    """Check if Scrapy is properly installed."""
    scrapy_spec = importlib.util.find_spec("scrapy")
    if scrapy_spec is None:
        print("Scrapy is not installed.")
        return False
    
    try:
        import scrapy
        print(f"Scrapy version: {scrapy.__version__}")
        
        # Check if scrapy can be called as a module
        try:
            result = subprocess.run(
                [sys.executable, "-m", "scrapy", "version"], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                print("Scrapy module is working correctly.")
                return True
            else:
                print(f"Scrapy module test failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"Failed to run scrapy module: {e}")
            return False
    except ImportError as e:
        print(f"Failed to import scrapy: {e}")
        return False

def check_data_directory():
    """Check if the data directory exists and is writable."""
    script_dir = Path(__file__).resolve().parent
    root_dir = script_dir.parent
    data_dir = root_dir / 'data'
    
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script directory: {script_dir}")
    print(f"Root directory: {root_dir}")
    print(f"Data directory path: {data_dir}")
    
    # Check if data directory exists
    if not data_dir.exists():
        print("Data directory does not exist. Creating it...")
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
            print("Data directory created successfully.")
        except Exception as e:
            print(f"Failed to create data directory: {e}")
            return False
    
    # Check if data directory is writable
    try:
        test_file = data_dir / "test_write.tmp"
        with open(test_file, "w") as f:
            f.write("Test write")
        test_file.unlink()  # Delete the test file
        print("Data directory is writable.")
        return True
    except Exception as e:
        print(f"Data directory is not writable: {e}")
        return False

def main():
    """Run all environment checks."""
    print("=" * 50)
    print("AI Politician Scraper Environment Check")
    print("=" * 50)
    
    spacy_ok = check_spacy()
    scrapy_ok = check_scrapy()
    data_dir_ok = check_data_directory()
    
    print("\nCheck summary:")
    print(f"spaCy and language model: {'✓ OK' if spacy_ok else '✗ FAILED'}")
    print(f"Scrapy: {'✓ OK' if scrapy_ok else '✗ FAILED'}")
    print(f"Data directory: {'✓ OK' if data_dir_ok else '✗ FAILED'}")
    
    if spacy_ok and scrapy_ok and data_dir_ok:
        print("\nEnvironment is properly set up! You can run:")
        print("python run.py --politician \"Politician Name\"")
        return 0
    else:
        print("\nEnvironment check failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 