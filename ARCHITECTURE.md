# AI Politician Data - Architecture & Pipeline Documentation

## Overview

This document provides a comprehensive explanation of the data pipeline, ingestion process, storage mechanisms, and tools used in the AI Politician Data project. The system is designed to collect, process, and store politician data from multiple sources for use in AI language models and analysis.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA COLLECTION LAYER                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐              ┌──────────────────┐        │
│  │  Wikipedia Spider │              │  News API Spider │        │
│  │   (Scrapy)       │              │    (Scrapy)      │        │
│  └────────┬─────────┘              └────────┬─────────┘        │
│           │                                   │                  │
└───────────┼───────────────────────────────────┼──────────────────┘
            │                                   │
            │         ┌─────────────────────────┘
            │         │
            ▼         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA PROCESSING LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              PoliticianPipeline (pipelines.py)            │ │
│  │                                                            │ │
│  │  • Text cleaning (spaCy NLP)                              │ │
│  │  • Content normalization                                  │ │
│  │  • Metadata extraction                                    │ │
│  │  • ID generation                                          │ │
│  │  • Timestamp assignment                                   │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
└───────────────────────────────────┬───────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATA STORAGE LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐              ┌──────────────────┐        │
│  │   JSON Files     │              │   ChromaDB       │        │
│  │  (File System)   │              │ (Vector Store)   │        │
│  │                  │              │                  │        │
│  │  data/           │◄─────────────│  /opt/chroma_db  │        │
│  │  *.json          │   ingestion  │                  │        │
│  └──────────────────┘              └──────────────────┘        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Pipeline Flow

### Phase 1: Data Collection

The data collection phase uses Scrapy spiders to gather information from multiple sources:

#### 1.1 Wikipedia Spider (`wikipedia_spider.py`)
**Purpose**: Collects biographical data, political positions, and speeches from Wikipedia

**Process**:
1. Accepts a politician name as input
2. Constructs Wikipedia URL and navigates to the politician's page
3. Falls back to search if direct URL doesn't exist
4. Extracts structured data:
   - Full name
   - Date of birth
   - Political affiliation
   - Biographical content
   - Speeches and quotes
5. Optionally follows related links (configurable depth)
6. Marks visited URLs to avoid cycles
7. Emits `PoliticianItem` objects with collected data

**Key Features**:
- Configurable link following (`follow_links`, `max_links`)
- Intelligent URL resolution and fallback
- Related page content collection with source attribution
- Cycle detection to prevent infinite loops

#### 1.2 News API Spider (`news_api_spider.py`)
**Purpose**: Collects recent news articles, statements, and quotes from news sources

**Process**:
1. Accepts politician name and API key (optional)
2. Queries NewsAPI.org for articles about the politician
3. Configurable parameters:
   - Time span (days to look back)
   - Maximum pages to fetch
   - API key from environment or parameter
4. Extracts statements and quotes from news articles
5. Paginates through results up to configured maximum
6. Emits data to processing pipeline

**Key Features**:
- Flexible API key configuration (environment or parameter)
- Graceful fallback without API key (limited access)
- Configurable time range and pagination
- Rate limiting awareness

### Phase 2: Data Processing

All collected data passes through the `PoliticianPipeline` class for processing:

#### 2.1 Text Processing (`pipelines.py`)

**Pipeline Operations**:

1. **Text Cleaning with NLP**:
   - Uses spaCy (`en_core_web_sm` model) when available
   - Removes URLs, email addresses
   - Normalizes whitespace
   - Removes citation brackets (e.g., [1], [2])
   - Filters non-relevant tokens
   - Falls back to regex-based cleaning if spaCy unavailable

2. **Content Structuring**:
   - Processes raw biographical content
   - Organizes speeches into list format
   - Structures statements into separate entries
   - Maintains source attribution

3. **Metadata Management**:
   - Generates unique IDs from politician name + timestamp
   - Adds collection timestamps (ISO 8601 format)
   - Preserves source URLs
   - Maintains data provenance

4. **Data Validation**:
   - Ensures required fields are present
   - Validates data types
   - Handles missing optional fields gracefully

**Data Item Structure** (`items.py`):
```python
PoliticianItem:
  - id: Unique identifier (name-YYYYMMDD)
  - name: Politician name
  - full_name: Complete name
  - source_url: Origin URL
  - date_of_birth: Birth date
  - political_affiliation: Party/affiliation
  - raw_content: Cleaned biographical text
  - speeches: List of speech texts
  - statements: List of statement texts
  - timestamp: Collection time (ISO 8601)
```

### Phase 3: Data Storage

The system uses a dual-storage approach:

#### 3.1 Primary Storage: JSON Files

**Location**: `data/` directory

**Format**: One JSON file per politician
- Filename: `{politician-id}-{timestamp}.json`
- Structure: Direct serialization of PoliticianItem
- Encoding: UTF-8 with non-ASCII support
- Pretty-printed with 2-space indentation

**Advantages**:
- Human-readable format
- Easy version control
- Simple backup and sharing
- Direct file system access
- No database dependencies

**Usage**:
```bash
# Files are automatically created during scraping
python run.py --politician "Barack Obama"
# Creates: data/barack-obama-20240407.json
```

#### 3.2 Secondary Storage: ChromaDB (Vector Store)

**Location**: `/opt/chroma_db/`

**Purpose**: Enables semantic search and AI-powered querying

**Architecture**:
- **ChromaDB**: Embedding database for vector similarity search
- **Collection**: "politicians" - stores all politician data
- **Documents**: Text chunks (speeches, statements, content)
- **Metadata**: Associated politician information
- **Embeddings**: Automatically generated vector representations

**Storage Strategy**:

The ingestion process (`ingest_data.py`) stores data in a granular format:

1. **Raw Content**: Single document per politician
   - ID: `{politician_id}_raw`
   - Type: `raw_content`
   - Metadata: Full politician information

2. **Speeches**: Separate documents per speech
   - ID: `{politician_id}_speech_{index}`
   - Type: `speech`
   - Enables fine-grained semantic search

3. **Statements**: Separate documents per statement
   - ID: `{politician_id}_statement_{index}`
   - Type: `statement`
   - Optimized for quote retrieval

**Benefits**:
- Semantic similarity search
- Natural language queries
- Context-aware retrieval
- Efficient large-scale querying
- AI/ML ready format

## Tools and Technologies

### Core Framework

#### 1. Scrapy (Web Scraping Framework)
**Version**: Latest stable
**Purpose**: Foundation for web scraping infrastructure

**Features Used**:
- Spider classes for structured scraping
- Item pipelines for data processing
- Middleware for request/response handling
- Built-in rate limiting and politeness
- Automatic retry mechanisms
- Concurrent request handling
- URL deduplication

**Why Scrapy**:
- Production-ready scraping framework
- Handles complex scraping scenarios
- Excellent documentation and community
- Built-in best practices (robots.txt, rate limiting)
- Extensible architecture

### Natural Language Processing

#### 2. spaCy (NLP Library)
**Model**: `en_core_web_sm` (English language model)
**Purpose**: Advanced text processing and cleaning

**Features Used**:
- Tokenization
- Entity recognition (URLs, emails)
- Text normalization
- Token filtering
- Linguistic analysis

**Why spaCy**:
- Fast and efficient
- Pre-trained models
- Industrial-strength NLP
- Easy integration
- Graceful degradation (optional dependency)

### Data Storage

#### 3. ChromaDB (Vector Database)
**Purpose**: Semantic search and AI-ready storage

**Features Used**:
- Automatic embedding generation
- Persistent storage
- Collection management
- Metadata filtering
- Similarity search
- Vector retrieval

**Configuration** (`chroma_config.py`):
- Persistent client with disk storage
- Centralized configuration
- Permission checking
- Error handling
- Collection management utilities

**Why ChromaDB**:
- Open source and free
- Easy to set up
- Automatic embeddings
- Optimized for AI applications
- Python-native API

### Utilities

#### 4. python-dotenv
**Purpose**: Environment variable management

**Usage**:
- Secure API key storage
- Configuration management
- Environment separation

#### 5. requests
**Purpose**: HTTP library for simplified scraping

**Usage**:
- Alternative scraper (`simple_scrape.py`)
- Fallback when Scrapy unavailable
- Direct API calls

## Data Ingestion Workflow

### Complete Workflow Example

```bash
# Step 1: Scrape politician data
cd scraper
python run.py --politician "Joe Biden" --comprehensive

# Output:
# - data/joe-biden-20240407.json (JSON file)

# Step 2: Set up ChromaDB (one-time setup)
cd ../scripts
python setup_chroma.py

# Output:
# - Creates /opt/chroma_db/
# - Initializes "politicians" collection

# Step 3: Ingest data into ChromaDB
python ingest_data.py ../data/joe-biden-20240407.json

# Output:
# - Stores documents in ChromaDB
# - Generates embeddings automatically
# - Creates searchable vector store

# Step 4: Query the data
python query_data.py

# Output:
# - Returns relevant documents
# - Semantic similarity search
# - Context-aware results
```

### Ingestion Process Details

**Input**: JSON file from scraping phase

**Process** (`ingest_data.py`):
1. Load JSON file
2. Connect to ChromaDB
3. Create or get "politicians" collection
4. Extract base metadata (politician info)
5. Ingest raw content as single document
6. Iterate through speeches, create individual documents
7. Iterate through statements, create individual documents
8. Assign unique IDs to each document
9. Attach comprehensive metadata
10. Automatic embedding generation by ChromaDB
11. Persist to disk

**Output**: Vector database ready for queries

## Configuration and Customization

### Scraping Configuration

**Command-line Parameters**:
```bash
--politician "Name"        # Required: Politician to scrape
--api-key KEY             # Optional: NewsAPI key
--check-only              # Dependency check only
--no-news                 # Skip news collection
--max-pages N             # News pages to fetch (default: 10)
--time-span N             # Days to look back (default: 365)
--follow-links true/false # Follow Wikipedia links (default: true)
--max-links N             # Max related links (default: 5)
--comprehensive           # Maximum collection settings
```

**Environment Configuration** (`.env`):
```
NEWS_API_KEY=your_api_key_here
```

### Pipeline Configuration

**Scrapy Settings** (`settings.py`):
- User agent configuration
- Download delays
- Concurrent requests
- Pipeline priorities
- Middleware activation

### Storage Configuration

**ChromaDB Settings** (`chroma_config.py`):
```python
DB_DIR = "/opt/chroma_db"  # Database location
Settings(anonymized_telemetry=False)  # Privacy settings
```

## Data Flow Diagram

```
User Input
    │
    ├─► politician name
    ├─► configuration options
    └─► API keys (optional)
         │
         ▼
    run.py (orchestrator)
         │
         ├─────────────────────┬─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
  Wikipedia Spider       News API Spider       Settings/Config
         │                     │                     │
         └──────────┬──────────┘                     │
                    │                                │
                    ▼                                │
            Scrapy Framework ◄───────────────────────┘
                    │
                    │ (yields items)
                    ▼
         PoliticianPipeline
                    │
                    ├─► Text cleaning (spaCy)
                    ├─► Metadata generation
                    ├─► ID generation
                    └─► Timestamp assignment
                         │
                         ▼
                  JSON Serialization
                         │
                         ▼
                 File System Write
                         │
                         └─► data/{politician-id}.json
                                      │
                                      │ (manual step)
                                      ▼
                              ingest_data.py
                                      │
                                      ├─► Parse JSON
                                      ├─► Split into documents
                                      └─► Add metadata
                                           │
                                           ▼
                                      ChromaDB
                                           │
                                           ├─► Generate embeddings
                                           ├─► Store vectors
                                           └─► Persist to disk
                                                    │
                                                    ▼
                                            /opt/chroma_db/
                                                    │
                                                    │ (queries)
                                                    ▼
                                              query_data.py
                                                    │
                                                    └─► Semantic search results
```

## Performance Considerations

### Scraping Performance

**Rate Limiting**:
- Respects robots.txt
- Configurable download delays
- Concurrent request limits
- Polite crawling defaults

**Optimization**:
- Direct URL access (Wikipedia)
- Pagination control (News API)
- Link following limits
- Visited URL tracking

### Processing Performance

**Text Processing**:
- Optional spaCy for speed/features tradeoff
- Fallback to regex for basic cleaning
- Batch processing where applicable

**Storage Performance**:
- Direct file I/O for JSON
- Efficient ChromaDB indexing
- Automatic embedding generation
- Incremental ingestion support

## Error Handling and Resilience

### Graceful Degradation

**Missing Dependencies**:
- Continues without spaCy (basic text cleaning)
- Fallback without News API key
- Simplified scraper alternative available

**Network Issues**:
- Automatic retries (Scrapy)
- Request timeout handling
- Fallback URLs (Wikipedia search)

**Storage Issues**:
- Directory creation with permission checks
- Write permission validation
- Atomic file operations

### Monitoring and Debugging

**Logging**:
- Scrapy built-in logging
- Pipeline processing logs
- Storage operation logs
- Error tracking

**Diagnostic Tools**:
- `diagnostic.py`: System health check
- `diagnose_chroma.py`: ChromaDB validation
- Dependency checking in `run.py`

## Extension Points

### Adding New Data Sources

1. Create new spider in `scraper/scraper/spiders/`
2. Inherit from `scrapy.Spider`
3. Yield `PoliticianItem` objects
4. Add to orchestration in `run.py`

### Custom Processing

1. Modify `PoliticianPipeline` in `pipelines.py`
2. Add new processing methods
3. Update item structure if needed
4. Maintain backward compatibility

### Alternative Storage

1. Implement new storage backend
2. Create ingestion script similar to `ingest_data.py`
3. Maintain JSON as interchange format
4. Add configuration in respective modules

## Security Considerations

### API Keys

- Stored in `.env` files (not committed to git)
- Loaded via python-dotenv
- Never hardcoded in source
- Can be passed as command-line arguments (not recommended)

### Data Privacy

- Public data sources only (Wikipedia, News APIs)
- Respects robots.txt
- Rate-limited to avoid abuse
- No personal identifiable information storage beyond public records

### File System Security

- Permission checking before operations
- Configurable storage locations
- Atomic write operations
- No arbitrary file access

## Maintenance and Operations

### Regular Maintenance

**Data Updates**:
- Re-scrape periodically for fresh data
- Update timestamp tracking
- Archive old data if needed

**Dependency Updates**:
- Update Python packages regularly
- Re-download spaCy models if needed
- Monitor Scrapy changes

**Database Maintenance**:
- Monitor ChromaDB size
- Clean up old collections if needed
- Backup vector database

### Troubleshooting Guide

**No Data Collected**:
1. Verify politician name spelling
2. Check API keys in `.env`
3. Run `diagnostic.py`
4. Check network connectivity

**spaCy Warnings**:
1. Verify correct Python environment
2. Check spaCy installation
3. Download language model
4. Falls back to basic cleaning automatically

**ChromaDB Issues**:
1. Check directory permissions
2. Verify disk space
3. Run `diagnose_chroma.py`
4. Check database path configuration

## Future Enhancements

### Potential Improvements

1. **Real-time Updates**: WebSocket or polling for live data
2. **Additional Sources**: Social media, government records
3. **Advanced NLP**: Sentiment analysis, entity extraction
4. **Deduplication**: Cross-source duplicate detection
5. **API Layer**: REST API for data access
6. **Visualization**: Dashboard for data exploration
7. **Automated Scheduling**: Cron jobs for regular updates
8. **Distributed Scraping**: Multi-node deployment

## Conclusion

The AI Politician Data project implements a robust, scalable pipeline for collecting, processing, and storing political data. The architecture balances simplicity with power, using industry-standard tools (Scrapy, spaCy, ChromaDB) while maintaining flexibility through modular design. The dual-storage approach (JSON + ChromaDB) provides both human-readable archives and AI-ready semantic search capabilities.

The system is designed for:
- **Reliability**: Error handling and graceful degradation
- **Scalability**: Efficient processing and storage
- **Maintainability**: Clear separation of concerns
- **Extensibility**: Easy addition of new sources or storage backends
- **Usability**: Simple command-line interface with sensible defaults

For questions or contributions, please refer to the main README.md and project documentation.
