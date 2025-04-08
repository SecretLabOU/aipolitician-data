# AI Politician Data Scraper

A comprehensive tool for collecting, processing, and storing politician data from Wikipedia and news sources. This data is structured for use in AI language models, enabling the creation of politically informed AI agents.

## Overview

This project scrapes biographical information, statements, and speeches of politicians from:
- **Wikipedia** - For biographical data, political positions, and speeches
- **News API** - For recent news articles and statements

The data is processed with NLP tools and saved in a format ready for both human analysis and machine learning applications.

## Project Structure

```
aipolitician-data/
├── README.md                   # This documentation
├── .gitignore                  # Git ignore file for the entire project
├── .env.example                # Example environment variables file
├── diagnostic.py               # Diagnostic tool for troubleshooting
├── scraper/                    # Main scraper code
│   ├── scraper/                # Scrapy spiders and components
│   │   ├── spiders/            # Individual scrapers
│   │   │   ├── wikipedia_spider.py  # Wikipedia scraper
│   │   │   └── news_api_spider.py   # News API scraper
│   │   ├── pipelines.py        # Data processing pipeline
│   │   ├── items.py            # Data item definitions
│   │   └── settings.py         # Scrapy settings
│   ├── run.py                  # Main runner script
│   ├── simple_scrape.py        # Simplified alternative scraper
│   ├── comprehensive_scrape.sh # Script for comprehensive data collection
│   ├── requirements.txt        # Python dependencies
│   └── setup.sh                # Setup script for dependencies
├── data/                       # Data storage directory
│   └── sample_politician.json  # Sample data file
└── scripts/                    # Utility scripts
    ├── setup_chroma.py         # Set up ChromaDB for vector storage
    ├── ingest_data.py          # Process and store data in ChromaDB
    └── query_data.py           # Query the stored data
```

## Setup

### Option 1: Using Conda (Recommended)

Conda provides an isolated environment with all the necessary dependencies:

```bash
# Create a new conda environment
conda create -n aipolitician python=3.11 -y

# Activate the environment
conda activate aipolitician

# Install required packages
pip install scrapy requests python-dotenv spacy

# Download the spaCy language model
python -m spacy download en_core_web_sm
```

### Option 2: Using pip with venv

```bash
# Create a virtual environment
python -m venv venv

# Activate the environment
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate

# Install dependencies
pip install -r scraper/requirements.txt

# Download the spaCy language model
python -m spacy download en_core_web_sm
```

### Option 3: Quick setup script

For Unix-based systems, a setup script is provided:

```bash
# Navigate to the scraper directory
cd scraper

# Make the script executable
chmod +x setup.sh

# Run the setup script
./setup.sh
```

## API Keys

For better news data collection, sign up for a free API key at [NewsAPI.org](https://newsapi.org/)

1. Create a `.env` file in the project root (or copy from the example):
   ```bash
   cp scraper/.env.example .env
   ```

2. Add your API key to the `.env` file:
   ```
   NEWS_API_KEY=your_actual_api_key_here
   ```

## Running the Scraper

### Basic Usage

```bash
# Navigate to the scraper directory
cd scraper

# Run the scraper with a specific politician
python run.py --politician "Politician Name"
```

### Command-line Options

```
Required:
--politician "Name"     Name of the politician to scrape data for

Optional:
--api-key KEY           NewsAPI key (will use from .env if not provided)
--check-only            Only check dependencies, don't run scrapers
--no-news               Skip the NewsAPI spider
--max-pages N           Maximum number of news pages to fetch (default: 10)
--time-span N           Time span in days to fetch news for (default: 365)
--follow-links true|false  Follow links from Wikipedia to related pages (default: true)
--max-links N           Maximum number of related links to follow (default: 5)
--comprehensive         Use maximum settings for comprehensive data collection
```

### Comprehensive Data Collection

For maximum data collection, use the comprehensive mode:

```bash
# Using the flag
python run.py --politician "Politician Name" --comprehensive

# Or using the convenience script
./comprehensive_scrape.sh "Politician Name"
```

If you're using a conda environment, make sure to activate it first:

```bash
# Activate your conda environment
conda activate aipolitician

# Then run the comprehensive script
./comprehensive_scrape.sh "Politician Name"
```

This uses optimized settings:
- 100 maximum news pages
- 10-year time span for news
- Following up to 10 related Wikipedia links
- All data collection features enabled

### Examples

Basic collection:
```bash
python run.py --politician "Barack Obama"
```

With custom settings:
```bash
python run.py --politician "Joe Biden" --max-pages 50 --time-span 1825 --follow-links true --max-links 8
```

Minimal collection (Wikipedia only):
```bash
python run.py --politician "Angela Merkel" --no-news
```

### Simplified Version

If you're having trouble with dependencies, a simplified version is available that only requires `requests`:

```bash
# Install minimal dependency
pip install requests

# Run the simplified scraper
python simple_scrape.py --politician "Politician Name"
```

## Data Format

The scraper produces JSON files in the `data/` directory with this structure:

```json
{
  "id": "politician-name-20240407",
  "name": "Politician Name",
  "source_url": "https://en.wikipedia.org/wiki/Politician_Name",
  "full_name": "Full Politician Name",
  "date_of_birth": "YYYY-MM-DD",
  "political_affiliation": "Political Party",
  "raw_content": "Biographical text...",
  "speeches": [
    "Speech 1 text...",
    "Speech 2 text..."
  ],
  "statements": [
    "Statement 1 text...",
    "Statement 2 text..."
  ],
  "timestamp": "YYYY-MM-DDThh:mm:ss"
}
```

## What Makes This Scraper Special

1. **Comprehensive Data Collection**: The enhanced scraper can follow links to related Wikipedia pages and collect data from multiple news pages.

2. **Intelligent Text Processing**: Uses spaCy for natural language processing to clean and extract meaningful content.

3. **Configurable Depth and Breadth**: You can control how much data to collect through various parameters.

4. **Source Attribution**: Content from related pages is clearly labeled with the source.

5. **Fallback Mechanisms**: Works even without all dependencies, with graceful degradation.

## Troubleshooting

### SpaCy Warning

If you see "spaCy is not available" warnings:
1. Check if you're using the correct environment: `conda activate aipolitician`
2. Verify spaCy installation: `python -m spacy info`
3. Reinstall if needed: `pip install spacy && python -m spacy download en_core_web_sm`

### No Data Collected

If no data is found:
1. Check that the `.env` file is in the correct location
2. Validate your NewsAPI key
3. Try with a well-known politician name (e.g., "Joe Biden", "Donald Trump")
4. Run the diagnostic tool: `python diagnostic.py`

### Conda Environment Issues

If you see "package not found" errors when running scripts, but the packages are installed in your conda environment:
1. Make sure you've activated your conda environment: `conda activate aipolitician`
2. Run scripts with the full Python path: `$CONDA_PREFIX/bin/python script.py`
3. For shell scripts like comprehensive_scrape.sh, activate the conda environment first, then run the script

### Permission Denied

If you see permission errors when running shell scripts:
1. Make scripts executable: `chmod +x comprehensive_scrape.sh`
2. Try running with sudo if needed (not recommended on shared systems)

## Tools Used

1. **Scrapy**: A powerful web scraping framework that handles multi-page requests efficiently
2. **spaCy**: An advanced natural language processing library for text cleaning and analysis
3. **requests**: A simple HTTP library for the simplified scraper
4. **python-dotenv**: For securely loading API keys from environment variables
5. **ChromaDB** (optional): For vector storage and retrieval of processed data

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [NewsAPI](https://newsapi.org/) for providing the news data API
- [Wikipedia](https://www.wikipedia.org/) for the biographical data
- The open-source community for the tools that make this project possible

