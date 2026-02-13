"""
RAG Tools for Employee Discounts
Handles PDF processing, indexing, and semantic search
NOW SUPPORTS REAL PDF FILES
"""

import os
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path
import re

logger = logging.getLogger(__name__)

class PDFProcessor:
    """PDF text extraction - supports both TXT and PDF files"""
    
    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        """
        Extract text from file (supports .txt and .pdf)
        """
        try:
            if file_path.endswith('.txt'):
                # Simple text file
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            
            elif file_path.endswith('.pdf'):
                # PDF file - uses PyPDF library
                try:
                    from pypdf import PdfReader
                    
                    pdf_reader = PdfReader(file_path)
                    text = ""
                    
                    # Extract text from all pages
                    for page_num, page in enumerate(pdf_reader.pages):
                        try:
                            page_text = page.extract_text()
                            if page_text:
                                text += f"\n--- Page {page_num + 1} ---\n"
                                text += page_text
                        except Exception as e:
                            logger.warning(f"Could not extract page {page_num + 1} from {file_path}: {e}")
                    
                    return text if text else ""
                
                except ImportError:
                    logger.error("PyPDF not installed. Install with: pip install pypdf")
                    return ""
            
            else:
                logger.warning(f"Unsupported file type: {file_path}")
                return ""
        
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return ""

class SimpleEmbedding:
    """Simple embedding using keyword matching"""
    
    @staticmethod
    def create_embedding(text: str) -> dict:
        """Create simple embedding from text"""
        words = text.lower().split()
        embedding = {}
        for word in words:
            if len(word) > 3:
                embedding[word] = embedding.get(word, 0) + 1
        return embedding
    
    @staticmethod
    def cosine_similarity(embedding1: dict, embedding2: dict) -> float:
        """Calculate similarity between embeddings"""
        if not embedding1 or not embedding2:
            return 0.0
        
        keys1 = set(embedding1.keys())
        keys2 = set(embedding2.keys())
        
        if not keys1 or not keys2:
            return 0.0
        
        overlap = len(keys1.intersection(keys2))
        max_size = max(len(keys1), len(keys2))
        return overlap / max_size if max_size > 0 else 0.0

class RAGTools:
    """Retrieval-Augmented Generation Tools with improved search"""
    
    def __init__(self, pdf_directory: str = "./pdfs"):
        self.pdf_directory = pdf_directory
        self.pdf_index = {}
        self.embeddings = {}
        self.metadata = {}
        
        os.makedirs(pdf_directory, exist_ok=True)
        self._initialize_index_sync()
    
    def _initialize_index_sync(self):
        """Initialize PDF index synchronously - supports both .txt and .pdf"""
        logger.info("📚 Initializing RAG index...")
        
        # Find both .txt and .pdf files
        pdf_files = list(Path(self.pdf_directory).glob("*.pdf"))
        txt_files = list(Path(self.pdf_directory).glob("*.txt"))
        all_files = pdf_files + txt_files
        
        logger.info(f"Found {len(all_files)} files ({len(pdf_files)} PDFs + {len(txt_files)} TXT)")
        
        for file_path in all_files:
            try:
                # Extract text from file
                content = PDFProcessor.extract_text_from_file(str(file_path))
                
                if not content.strip():
                    logger.warning(f"⚠️  No text extracted from {file_path.name}")
                    continue
                
                filename = file_path.name
                self.pdf_index[filename] = content
                self.embeddings[filename] = SimpleEmbedding.create_embedding(content)
                self.metadata[filename] = self._extract_metadata(content)
                
                logger.info(f"✅ Indexed: {filename}")
                
            except Exception as e:
                logger.error(f"Error indexing {file_path}: {e}")
        
        logger.info(f"✅ RAG index ready with {len(self.pdf_index)} documents")
    
    def _extract_metadata(self, content: str) -> Dict:
        """Extract metadata from content"""
        lines = content.split('\n')
        
        return {
            'name': lines[0] if lines else 'Unknown',
            'discount': self._extract_discount(content),
            'category': self._extract_category(content),
            'code': self._extract_code(content),
            'how_to_use': self._extract_how_to_use(content),
            'bonus': self._extract_bonus(content),
        }
    
    def _extract_discount(self, content: str) -> str:
        """Extract discount percentage"""
        patterns = [
            r'(\d+)%\s*(?:off|discount)',
            r'(?:save|get)\s*(\d+)%',
            r'(\d+)%',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return f"{match.group(1)}%"
        return "N/A"
    
    def _extract_category(self, content: str) -> str:
        """Determine category from content"""
        categories = {
            'Travel': ['hotel', 'flight', 'airline', 'travel', 'booking', 'hertz', 'expedia', 'delta', 'southwest'],
            'Dining': ['restaurant', 'food', 'cafe', 'dining', 'meal', 'starbucks', 'olive', 'chipotle'],
            'Retail': ['store', 'shop', 'clothing', 'retail', 'target', 'best buy', 'home depot', 'amazon'],
            'Tech': ['software', 'tech', 'app', 'computer', 'apple', 'microsoft', 'adobe'],
            'Entertainment': ['movie', 'show', 'ticket', 'entertainment', 'netflix', 'disney', 'amc'],
            'Health & Wellness': ['gym', 'wellness', 'health', 'fitness', 'spa', 'cvs'],
            'Finance': ['bank', 'insurance', 'investment', 'charles schwab', 'state farm'],
        }
        
        content_lower = content.lower()
        for category, keywords in categories.items():
            if any(keyword in content_lower for keyword in keywords):
                return category
        return 'Other'
    
    def _extract_code(self, content: str) -> Optional[str]:
        """Extract discount code"""
        patterns = [
            r'(?:code|ID)[\s:]*([A-Z0-9\-]+)',
            r'(?:enter|use|apply)[\s:]*([A-Z0-9\-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                code = match.group(1)
                if len(code) > 2:
                    return code
        return None
    
    def _extract_how_to_use(self, content: str) -> str:
        """Extract how to use instructions"""
        if 'how to' in content.lower():
            lines = content.lower().split('\n')
            for i, line in enumerate(lines):
                if 'how to' in line or 'to book' in line or 'to use' in line:
                    instruction = ' '.join(lines[i:min(i+3, len(lines))])
                    return instruction[:200]
        
        if 'hotel' in content.lower() or 'booking' in content.lower():
            return 'Visit website or call to book with discount code'
        elif 'restaurant' in content.lower() or 'dining' in content.lower():
            return 'Present offer at restaurant or book online'
        
        return 'Contact provider for discount details'
    
    def _extract_bonus(self, content: str) -> Optional[str]:
        """Extract bonus benefits"""
        patterns = [
            r'(?:bonus|extra|additional)[\s:]*([^.\n]+)',
            r'plus[\s:]*([^.\n]+)',
            r'receive[\s:]*([^.\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    async def search_pdfs(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        IMPROVED Search with proper full-text matching
        Works with both TXT and PDF files
        Handles natural language queries by filtering stop words
        """
        logger.info(f"🔍 Searching for: '{query}'")
        
        # Remove punctuation from query
        import string
        query_clean = query.translate(str.maketrans('', '', string.punctuation))
        query_lower = query_clean.lower()
        
        # Extract key terms - remove common stop words
        stop_words = {'i', 'do', 'have', 'any', 'the', 'a', 'an', 'and', 'or', 'for', 'in', 'on', 'at', 'to', 'is', 'are', 'be', 'been', 'being', 'am', 'was', 'were', 'has', 'had', 'having', 'does', 'did', 'doing', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'will', 'shall', 'that', 'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'as', 'if', 'about', 'of', 'by', 'with', 'from', 'up', 'out', 'it', 'its', 'they', 'them', 'their', 'theirs', 'this', 'these', 'those', 'my', 'we', 'you', 'he', 'she', 'him', 'her', 'hers', 'yours', 'ours'}
        query_words = set(word for word in query_lower.split() if len(word) > 2 and word not in stop_words)
        
        # If no key words found after filtering, use all words
        if not query_words:
            query_words = set(word for word in query_lower.split() if len(word) > 2)
        
        logger.info(f"📍 Keywords to search: {query_words}")
        results_with_scores = []
        
        # Score each discount
        for filename, metadata in self.metadata.items():
            name = metadata['name'].lower()
            category = metadata['category'].lower()
            
            score = 0.0
            
            # 1. EXACT NAME MATCH (highest priority) - 100 points
            if name == query_lower or query_lower in name:
                score = 100.0
                logger.info(f"✅ Exact match: {metadata['name']}")
            
            # 2. NAME CONTAINS QUERY - 80 points
            elif query_lower in name:
                score = 80.0
                logger.info(f"✅ Name match: {metadata['name']}")
            
            # 3. WORD MATCHING - check if any keyword is in the name
            else:
                for keyword in query_words:
                    if keyword in name:
                        score = 60.0
                        logger.info(f"⭐ Keyword match '{keyword}': {metadata['name']}")
                        break
            
            if score > 0:
                results_with_scores.append((filename, metadata, score))
        
        # Sort by score (highest first)
        results_with_scores.sort(key=lambda x: x[2], reverse=True)
        
        # Format results
        results = []
        for filename, metadata, score in results_with_scores[:top_k]:
            item = dict(metadata)
            item['source'] = filename
            item['relevance_score'] = score
            results.append(item)
        
        logger.info(f"✅ Found {len(results)} relevant discounts (top matches first)")
        return results
    
    async def search_pdfs_smart(self, query: str, top_k: int = 10) -> list:
        """Smart search (alias for improved search)"""
        return await self.search_pdfs(query, top_k)
    
    def get_all_discounts_metadata(self) -> List[Dict]:
        """Get metadata for all loaded discounts"""
        results = []
        for filename, metadata in self.metadata.items():
            item = dict(metadata)
            item['source'] = filename
            results.append(item)
        return results