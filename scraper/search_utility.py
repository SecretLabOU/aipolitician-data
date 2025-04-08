#!/usr/bin/env python3
import argparse
import json
import os
import logging
import glob
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
from pathlib import Path
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PoliticianDataSearch:
    """
    Search utility for enhanced politician data, demonstrating RAG capabilities.
    """
    def __init__(self, data_dir=None):
        """Initialize the search utility with the data directory"""
        if data_dir is None:
            self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                       "data", "formatted")
        else:
            self.data_dir = data_dir
            
        self.politicians = []
        self.tokenizer = None
        self.model = None
        
    def load_embedding_model(self):
        """Load the embedding model for semantic search"""
        try:
            # Use the same model as in the formatter for compatibility
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            
            logger.info(f"Loading embedding model: {model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            logger.info("Embedding model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            return False
            
    def load_politician_data(self):
        """Load all enhanced politician data files"""
        json_files = glob.glob(os.path.join(self.data_dir, "formatted_*.json"))
        
        if not json_files:
            logger.warning(f"No formatted politician data files found in {self.data_dir}")
            return False
            
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    politician_data = json.load(f)
                    self.politicians.append(politician_data)
                    logger.info(f"Loaded data for {politician_data.get('name', 'Unknown')}")
            except Exception as e:
                logger.error(f"Error loading {file_path}: {str(e)}")
                
        logger.info(f"Loaded data for {len(self.politicians)} politicians")
        return len(self.politicians) > 0
        
    def generate_query_embedding(self, query_text):
        """Generate an embedding for a search query"""
        if not query_text:
            return None
            
        # Ensure model is loaded
        if self.tokenizer is None or self.model is None:
            if not self.load_embedding_model():
                logger.error("Could not load embedding model")
                return None
                
        try:
            # Tokenize and get embedding
            inputs = self.tokenizer([query_text], padding=True, truncation=True, 
                                  max_length=512, return_tensors="pt")
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                
            # Mean pooling
            attention_mask = inputs['attention_mask']
            token_embeddings = outputs.last_hidden_state
            
            # Token vectors, removing padding
            input_mask_expanded = attention_mask[0].unsqueeze(-1).expand(
                token_embeddings[0].size()).float()
            
            # Sum the token vectors and divide by the number of tokens
            sum_embeddings = torch.sum(token_embeddings[0] * input_mask_expanded, 0)
            sum_mask = torch.sum(input_mask_expanded, 0)
            
            # Avoid division by zero
            sum_mask = torch.clamp(sum_mask, min=1e-9)
            
            # Calculate mean
            embedding = (sum_embeddings / sum_mask).numpy()
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            return None
            
    def cosine_similarity(self, embedding1, embedding2):
        """Calculate cosine similarity between two embeddings"""
        if embedding1 is None or embedding2 is None:
            return 0.0
            
        try:
            # Convert to numpy arrays if they're lists
            if isinstance(embedding1, list):
                embedding1 = np.array(embedding1)
            if isinstance(embedding2, list):
                embedding2 = np.array(embedding2)
                
            # Calculate similarity
            similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0
            
    def search(self, query, top_k=5):
        """
        Perform semantic search across politician data
        
        Args:
            query: The search query
            top_k: Number of top results to return
            
        Returns:
            List of search results with politician name, content, and relevance score
        """
        if not self.politicians:
            if not self.load_politician_data():
                return []
                
        # Get query embedding
        query_embedding = self.generate_query_embedding(query)
        if query_embedding is None:
            logger.error("Failed to generate query embedding")
            return []
            
        all_results = []
        
        # Search across all politicians
        for politician in self.politicians:
            politician_name = politician.get("name", "Unknown")
            
            # Search entries
            if "entries" in politician:
                entry_results = self.search_entries(
                    politician, query, query_embedding
                )
                for result in entry_results:
                    result["politician"] = politician_name
                    all_results.append(result)
        
        # Sort by relevance and get top results
        sorted_results = sorted(all_results, key=lambda x: x.get("relevance", 0), reverse=True)
        return sorted_results[:top_k]
    
    def search_entries(self, politician, query, query_embedding):
        """Search within politician entries"""
        results = []
        
        # Get entries
        entries = politician.get("entries", [])
        
        if not entries:
            return []
            
        # Process each entry
        for entry in entries:
            entry_text = entry.get("text", "")
            if not entry_text:
                continue
                
            # Generate embedding for entry text
            entry_embedding = self.generate_query_embedding(entry_text[:512])  # Limit to first 512 chars
            
            if entry_embedding is None:
                continue
                
            # Calculate similarity
            similarity = self.cosine_similarity(query_embedding, entry_embedding)
            
            # Only include if similarity is above threshold
            if similarity > 0.2:
                # Create a snippet around relevant text
                snippet = self.create_content_snippet(entry_text, query)
                
                results.append({
                    "type": entry.get("type", "unknown"),
                    "content": snippet if snippet else entry_text[:200] + "...",
                    "relevance": similarity,
                    "source": entry.get("source_url", "")
                })
                
        return results
        
    def search_news_mentions(self, politician, query, query_embedding):
        """Search within news mentions"""
        results = []
        
        # Get news mentions and embeddings
        news_mentions = politician.get("content", {}).get("news_mentions", [])
        news_embeddings = politician.get("semantic_index", {}).get("news_embeddings", [])
        
        # Make sure we have both news and embeddings
        if not news_mentions or not news_embeddings or len(news_mentions) != len(news_embeddings):
            return []
            
        # Compare each news item's embedding to the query
        for i, (news, embedding) in enumerate(zip(news_mentions, news_embeddings)):
            if embedding is None:
                continue
                
            similarity = self.cosine_similarity(query_embedding, embedding)
            
            # Only include if similarity is above threshold
            if similarity > 0.5:
                # Extract title and snippet
                title = news.get("title", "")
                content = news.get("content", "")
                
                # Create a snippet around relevant text
                snippet = self.create_content_snippet(content, query)
                
                results.append({
                    "type": "news",
                    "title": title,
                    "content": snippet if snippet else content[:200] + "...",
                    "relevance": similarity,
                    "source": news.get("source", ""),
                    "url": news.get("url", ""),
                    "published_date": news.get("published_date", "")
                })
                
        return results
        
    def search_statements(self, politician, query, query_embedding):
        """Search within statements"""
        results = []
        
        # Get statements and embeddings
        statements = politician.get("content", {}).get("statements", [])
        statement_embeddings = politician.get("semantic_index", {}).get("statement_embeddings", [])
        
        # Make sure we have both statements and embeddings
        if not statements or not statement_embeddings or len(statements) != len(statement_embeddings):
            return []
            
        # Compare each statement's embedding to the query
        for i, (statement, embedding) in enumerate(zip(statements, statement_embeddings)):
            if embedding is None:
                continue
                
            similarity = self.cosine_similarity(query_embedding, embedding)
            
            # Only include if similarity is above threshold
            if similarity > 0.5:
                results.append({
                    "type": "statement",
                    "content": statement.get("text", ""),
                    "relevance": similarity,
                    "source": statement.get("source", "")
                })
                
        return results
        
    def search_speeches(self, politician, query, query_embedding):
        """Search within speeches"""
        results = []
        
        # Get speeches and embeddings
        speeches = politician.get("content", {}).get("speeches", [])
        speech_embeddings = politician.get("semantic_index", {}).get("speech_embeddings", [])
        
        # Make sure we have both speeches and embeddings
        if not speeches or not speech_embeddings or len(speeches) != len(speech_embeddings):
            return []
            
        # Compare each speech's embedding to the query
        for i, (speech, embedding) in enumerate(zip(speeches, speech_embeddings)):
            if embedding is None:
                continue
                
            similarity = self.cosine_similarity(query_embedding, embedding)
            
            # Only include if similarity is above threshold
            if similarity > 0.5:
                # Extract text and create snippet
                text = speech.get("text", "")
                snippet = self.create_content_snippet(text, query)
                
                results.append({
                    "type": "speech",
                    "content": snippet if snippet else text[:200] + "...",
                    "relevance": similarity,
                    "source": speech.get("source", "")
                })
                
        return results
        
    def search_bio(self, politician, query, query_embedding):
        """Search biographical information"""
        bio_text = politician.get("biographical_summary", "")
        bio_embedding = politician.get("semantic_index", {}).get("bio_embedding")
        
        if not bio_text or not bio_embedding:
            return None
            
        similarity = self.cosine_similarity(query_embedding, bio_embedding)
        
        # Only include if similarity is above threshold
        if similarity > 0.5:
            snippet = self.create_content_snippet(bio_text, query)
            
            return {
                "type": "bio",
                "content": snippet if snippet else bio_text[:200] + "...",
                "relevance": similarity
            }
            
        return None
        
    def create_content_snippet(self, content, query, snippet_size=200):
        """Create a snippet of content around the query terms"""
        if not content or not query:
            return ""
            
        # Convert to lowercase for case-insensitive matching
        content_lower = content.lower()
        query_terms = query.lower().split()
        
        # Find positions of all query terms
        term_positions = []
        for term in query_terms:
            if len(term) < 3:  # Skip short terms
                continue
                
            positions = [m.start() for m in re.finditer(r'\b' + re.escape(term) + r'\b', content_lower)]
            term_positions.extend(positions)
            
        if not term_positions:
            return ""
            
        # Get the position closest to the middle of the content
        middle_pos = len(content) // 2
        closest_pos = min(term_positions, key=lambda pos: abs(pos - middle_pos))
        
        # Create snippet around the position
        start = max(0, closest_pos - snippet_size // 2)
        end = min(len(content), start + snippet_size)
        
        # Adjust start to avoid cutting words
        if start > 0:
            while start > 0 and content[start] != ' ':
                start -= 1
            start += 1  # Move past the space
            
        # Adjust end to avoid cutting words
        if end < len(content):
            while end < len(content) and content[end] != ' ':
                end += 1
                
        snippet = content[start:end]
        
        # Add ellipsis if needed
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
            
        return snippet
        
    def keyword_search(self, query, top_k=5):
        """
        Perform keyword-based search as a fallback
        
        This serves as a baseline comparison for the semantic search
        """
        if not self.politicians:
            if not self.load_politician_data():
                return []
                
        all_results = []
        query_lower = query.lower()
        
        # Search across all politicians
        for politician in self.politicians:
            politician_name = politician.get("name", "Unknown")
            
            # Search entries
            if "entries" in politician:
                for entry in politician["entries"]:
                    text = entry.get("text", "").lower()
                    
                    # Check if query terms are in text
                    query_terms = query_lower.split()
                    matches = sum(1 for term in query_terms if len(term) > 2 and term in text)
                    relevance = matches / len(query_terms) if query_terms else 0
                    
                    if relevance > 0.3:
                        snippet = self.create_content_snippet(entry.get("text", ""), query)
                        
                        all_results.append({
                            "type": entry.get("type", "unknown"),
                            "politician": politician_name,
                            "content": snippet if snippet else entry.get("text", "")[:200] + "...",
                            "relevance": relevance,
                            "source": entry.get("source_url", "")
                        })
        
        # Sort by relevance and get top results
        sorted_results = sorted(all_results, key=lambda x: x.get("relevance", 0), reverse=True)
        return sorted_results[:top_k]
                    
def main():
    parser = argparse.ArgumentParser(description='Search formatted politician data')
    parser.add_argument('query', help='The search query')
    parser.add_argument('--dir', help='Directory containing formatted politician data')
    parser.add_argument('--keyword', action='store_true', help='Use keyword search instead of semantic search')
    parser.add_argument('--top', type=int, default=5, help='Number of top results to return')
    args = parser.parse_args()
    
    search_util = PoliticianDataSearch(data_dir=args.dir)
    
    if args.keyword:
        results = search_util.keyword_search(args.query, top_k=args.top)
        search_type = "keyword"
    else:
        results = search_util.search(args.query, top_k=args.top)
        search_type = "semantic"
        
    print(f"\nSearch results for: '{args.query}' (using {search_type} search)\n")
    
    if not results:
        print("No results found.")
        return
        
    for i, result in enumerate(results):
        print(f"Result {i+1} - {result.get('politician', 'Unknown')} - Relevance: {result.get('relevance', 0):.2f}")
        print(f"Type: {result.get('type', 'Unknown')}")
        
        if "title" in result:
            print(f"Title: {result['title']}")
            
        print(f"Content: {result.get('content', '')}")
        
        if "source" in result:
            print(f"Source: {result.get('source', '')}")
            
        if "url" in result:
            print(f"URL: {result.get('url', '')}")
            
        print()
        
if __name__ == "__main__":
    main() 