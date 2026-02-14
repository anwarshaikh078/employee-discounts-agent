"""
Hybrid Search Engine - PRODUCTION STABLE
Simple, reliable, no external dependencies
"""

import logging
from typing import List, Tuple, Dict
from .keyword_engine import KeywordSearchEngine

logger = logging.getLogger(__name__)

class HybridSearchEngine:
    """Simple, stable search engine"""
    
    def __init__(self):
        """Initialize search engine"""
        self.keyword_engine = KeywordSearchEngine()
        logger.info("🔍 Search Engine initialized (Keyword-based)")
    
    def add_document(self, doc_id: str, name: str, text: str):
        """Add document to search index"""
        self.keyword_engine.add_document(doc_id, name, text)
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Search documents
        Returns: [(doc_id, relevance_score), ...]
        """
        logger.info(f"🔍 Searching: '{query}'")
        
        # Get keyword search results
        results = self.keyword_engine.search(query)
        
        # Sort by score
        ranked = sorted(results.items(), key=lambda x: x[1], reverse=True)
        
        logger.info(f"✅ Found {len(ranked)} results")
        return ranked[:top_k]
    
    def get_stats(self) -> Dict:
        """Get search engine statistics"""
        return {
            'type': 'keyword-based',
            'total_documents': len(self.keyword_engine.documents),
            'total_keywords': len(self.keyword_engine.inverted_index),
            'status': 'production-stable'
        }