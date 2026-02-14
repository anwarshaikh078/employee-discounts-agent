"""
Vector-based Semantic Search Engine
Uses sentence embeddings for semantic similarity
"""

import logging
import numpy as np
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class VectorSearchEngine:
    """Semantic search using sentence embeddings (optional)"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', lazy_load: bool = True):
        """
        Initialize embeddings model
        lazy_load: If True, load model on first search (faster startup)
        """
        self.model_name = model_name
        self.model = None
        self.documents = {}
        self.embeddings_ready = False
        self.lazy_load = lazy_load
        
        if not lazy_load:
            self._load_model()
    
    def _load_model(self):
        """Load embeddings model"""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embeddings model: {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            self.embeddings_ready = True
            logger.info(f"✅ Embeddings model loaded: {self.model_name}")
        except ImportError:
            logger.warning("⚠️  sentence-transformers not installed")
            self.embeddings_ready = False
        except Exception as e:
            logger.error(f"Failed to load embeddings model: {e}")
            self.embeddings_ready = False
    
    def add_document(self, doc_id: str, name: str, text: str):
        """Add document with embeddings"""
        self.documents[doc_id] = {
            'name': name,
            'text': text,
            'embedding': None
        }
        logger.info(f"📝 Added: {name} (embeddings will load on first search)")
    
    def search(self, query: str, threshold: float = 0.1) -> Dict[str, float]:
        """Search using semantic similarity"""
        # Lazy load model on first search
        if self.lazy_load and self.model is None and not self.embeddings_ready:
            try:
                logger.info("⏳ Loading embeddings model on first search...")
                self._load_model()
            except Exception as e:
                logger.error(f"Failed to load embeddings on search: {e}")
                return {}
        
        if not self.embeddings_ready or self.model is None:
            logger.warning("Embeddings not available, skipping semantic search")
            return {}
        
        try:
            query_embedding = self.model.encode(query)
            doc_scores = {}
            
            for doc_id, doc_data in self.documents.items():
                if doc_data['embedding'] is None:
                    # Lazy embed documents
                    try:
                        doc_data['embedding'] = self.model.encode(doc_data['text'])
                    except Exception as e:
                        logger.warning(f"Could not embed {doc_id}: {e}")
                        continue
                
                similarity = self._cosine_similarity(
                    query_embedding,
                    doc_data['embedding']
                )
                
                if similarity > threshold:
                    doc_scores[doc_id] = similarity
            
            logger.info(f"🧠 Semantic: {len(doc_scores)} matched")
            return doc_scores
            
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return {}
    
    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
    
    def get_similar_documents(self, doc_id: str, top_k: int = 5) -> Dict[str, float]:
        """Find similar documents"""
        if doc_id not in self.documents or self.model is None:
            return {}
        
        if self.documents[doc_id]['embedding'] is None:
            return {}
        
        doc_embedding = self.documents[doc_id]['embedding']
        scores = {}
        
        for other_id, other_data in self.documents.items():
            if other_id == doc_id:
                continue
            
            if other_data['embedding'] is None:
                continue
            
            similarity = self._cosine_similarity(doc_embedding, other_data['embedding'])
            if similarity > 0:
                scores[other_id] = similarity
        
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return dict(ranked[:top_k])
    
    def get_stats(self) -> Dict:
        """Get stats"""
        return {
            'model': self.model_name,
            'embeddings_ready': self.embeddings_ready,
            'total_documents': len(self.documents)
        }