"""
Keyword-based Search Engine - PRODUCTION STABLE
Fast, reliable keyword matching with inverted index
"""

import logging
import string
from typing import List, Dict

logger = logging.getLogger(__name__)

class KeywordSearchEngine:
    """Production-grade keyword search"""
    
    def __init__(self):
        self.inverted_index = {}  # {keyword: set(doc_ids)}
        self.documents = {}  # {doc_id: {name, text, keywords}}
        self.document_count = 0
    
    def add_document(self, doc_id: str, name: str, text: str):
        """Add document to index"""
        keywords = self._tokenize_and_clean(text)
        
        self.documents[doc_id] = {
            'name': name,
            'text': text,
            'keywords': set(keywords)
        }
        
        # Build inverted index
        for keyword in set(keywords):
            if keyword not in self.inverted_index:
                self.inverted_index[keyword] = set()
            self.inverted_index[keyword].add(doc_id)
        
        self.document_count += 1
        logger.info(f"✅ Indexed: {name}")
    
    def _tokenize_and_clean(self, text: str) -> List[str]:
        """Clean and tokenize text into keywords"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Split into tokens
        tokens = text.split()
        
        # Filter: keep tokens >= 2 chars
        keywords = [t for t in tokens if len(t) >= 2]
        
        return keywords
    
    def search(self, query: str) -> Dict[str, float]:
        """
        Search for documents matching query keywords
        Returns {doc_id: relevance_score}
        """
        # Extract keywords from query
        query_keywords = self._tokenize_and_clean(query)
        
        if not query_keywords:
            logger.warning(f"No keywords in query: {query}")
            return {}
        
        logger.info(f"Query keywords: {query_keywords}")
        
        doc_scores = {}
        
        # For each query keyword, find matching documents
        for keyword in query_keywords:
            # Direct match
            if keyword in self.inverted_index:
                for doc_id in self.inverted_index[keyword]:
                    doc_scores[doc_id] = doc_scores.get(doc_id, 0) + 10.0
            
            # Substring match (e.g., "coffee" matches "starbucks" if it contains "coffee")
            for doc_id, doc_info in self.documents.items():
                if keyword in doc_info['text'].lower():
                    doc_scores[doc_id] = doc_scores.get(doc_id, 0) + 1.0
        
        # Normalize scores
        if doc_scores:
            max_score = max(doc_scores.values())
            doc_scores = {doc_id: (score / max_score) for doc_id, score in doc_scores.items()}
        
        logger.info(f"Found {len(doc_scores)} matching documents")
        return doc_scores