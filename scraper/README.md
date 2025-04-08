# AI Politician Data Scraper

This scraper collects data about politicians from Wikipedia and news sources, processes the text using spaCy, and stores it in JSON format compatible with the AI Politician project.

## Setup

### Easy Setup (Recommended)

Use the provided setup script to install all dependencies and download the spaCy language model:

```bash
# Make the script executable first if needed
chmod +x setup.sh
./setup.sh
```

### Manual Setup

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

### Command-line Options

- `--politician "Name"`: Name of the politician to scrape data for (required)
- `--api-key YOUR_API_KEY`: Add a NewsAPI API key for better news article access (optional)
- `--check-only`: Only check if dependencies are installed, don't run the scraper (optional)
- `--no-news`: Skip the news API scraper and only collect data from Wikipedia (optional)

### Examples

Basic usage:
```bash
python run.py --politician "Barack Obama"
```

With a NewsAPI key:
```bash
python run.py --politician "Joe Biden" --api-key "your-api-key-here"
```

Only check dependencies:
```bash
python run.py --check-only --politician "Any Name"
```

Skip news scraping:
```bash
python run.py --politician "Angela Merkel" --no-news
```

## Troubleshooting

If you encounter dependency issues, make sure all required packages are installed:

```bash
pip install numpy
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

The scraper can work even without spaCy installed, but text processing will be more limited.

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

## Simplified Version

If you're having trouble with dependencies, you can use the simplified scraper which only requires `requests`:

```bash
# Install minimal dependencies
pip install requests

# Run the simplified scraper
python simple_scrape.py --politician "Politician Name"
```

This simplified version only collects basic information from Wikipedia and doesn't require spaCy or Scrapy. 