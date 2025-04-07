# AI Politician Data Scraper

This scraper collects data about politicians from Wikipedia and news sources, processes the text using spaCy, and stores it in JSON format compatible with the AI Politician project.

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Download the spaCy language model:

```bash
python -m spacy download en_core_web_sm
```

## Usage

The scraper can be run using the provided run.py script:

```bash
python run.py --politician "Politician Name"
```

Optional parameters:
- `--api-key YOUR_API_KEY`: Add a NewsAPI API key for better news article access

Example:
```bash
python run.py --politician "Barack Obama"
```

## Data Format

The scraper collects data and saves it to the `../data/` directory in JSON format. The data structure follows this pattern:

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

## Components

- `wikipedia_spider.py`: Scrapes politician data from Wikipedia
- `news_api_spider.py`: Collects recent news articles mentioning the politician
- `pipelines.py`: Processes the scraped data using spaCy for text cleaning
- `run.py`: Main script to orchestrate the scraping process 