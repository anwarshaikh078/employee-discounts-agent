"""
RAG Tools - PRODUCTION STABLE
PDF processing, indexing, and search
"""

import os
import logging
import re
from typing import List, Dict, Optional
from pathlib import Path

from search.hybrid_search import HybridSearchEngine

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Extract text from files"""
    
    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        """Extract text from .txt or .pdf files"""
        try:
            if file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            elif file_path.endswith('.pdf'):
                try:
                    from pypdf import PdfReader
                    pdf_reader = PdfReader(file_path)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    return text
                except ImportError:
                    logger.error("PyPDF not installed")
                    return ""
            return ""
        except Exception as e:
            logger.error(f"Error extracting {file_path}: {e}")
            return ""

class RAGTools:
    """Retrieval-Augmented Generation Tools"""
    
    def __init__(self, pdf_directory: str = "./pdfs"):
        self.pdf_directory = pdf_directory
        self.pdf_index = {}
        self.metadata = {}
        self.search_engine = HybridSearchEngine()
        
        os.makedirs(pdf_directory, exist_ok=True)
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize document index"""
        logger.info("📚 Initializing document index...")
        
        # Find all PDF and TXT files
        pdf_files = list(Path(self.pdf_directory).glob("*.pdf"))
        txt_files = list(Path(self.pdf_directory).glob("*.txt"))
        all_files = sorted(pdf_files + txt_files)
        
        logger.info(f"Found {len(all_files)} documents")
        
        for file_path in all_files:
            try:
                content = PDFProcessor.extract_text_from_file(str(file_path))
                
                if not content.strip():
                    logger.warning(f"No content: {file_path.name}")
                    continue
                
                filename = file_path.name
                self.pdf_index[filename] = content
                self.metadata[filename] = self._extract_metadata(content)
                
                # Add to search engine
                self.search_engine.add_document(
                    filename,
                    self.metadata[filename]['name'],
                    content
                )
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
        
        logger.info(f"✅ Index ready with {len(self.pdf_index)} documents")
    
    def _extract_metadata(self, content: str) -> Dict:
        """Extract discount information from content"""
        lines = content.split('\n')
        name = lines[0] if lines else 'Unknown'
        
        return {
            'name': name,
            'discount': self._extract_discount(content),
            'category': self._extract_category(content),
            'code': self._extract_code(content),
            'how_to_use': self._extract_how_to_use(content),
            'bonus': self._extract_bonus(content),
        }
    
    def _extract_discount(self, content: str) -> str:
        """Extract discount percentage"""
        patterns = [r'(\d+)%\s*(?:off|discount)', r'(?:save|get)\s*(\d+)%', r'(\d+)%']
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return f"{match.group(1)}%"
        return "N/A"
    
    def _extract_category(self, content: str) -> str:
        """Determine category"""
        categories = {
            'Travel': ['hotel', 'flight', 'airline', 'travel', 'hertz', 'expedia', 'delta', 'southwest'],
            'Dining': ['restaurant', 'food', 'cafe', 'dining', 'starbucks', 'olive', 'chipotle'],
            'Retail': ['store', 'shop', 'retail', 'target', 'best buy', 'home depot', 'amazon'],
            'Tech': ['software', 'tech', 'apple', 'microsoft', 'adobe'],
            'Entertainment': ['movie', 'netflix', 'disney', 'amc'],
            'Health & Wellness': ['gym', 'wellness', 'fitness', 'spa', 'cvs'],
            'Finance': ['bank', 'insurance', 'schwab', 'state farm'],
        }
        content_lower = content.lower()
        for cat, keywords in categories.items():
            if any(kw in content_lower for kw in keywords):
                return cat
        return 'Other'
    
    def _extract_code(self, content: str) -> Optional[str]:
        """Extract discount code"""
        patterns = [r'(?:code|ID)[\s:]*([A-Z0-9\-]+)', r'(?:enter|use)[\s:]*([A-Z0-9\-]+)']
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
                if 'how to' in line:
                    return ' '.join(lines[i:min(i+2, len(lines))])[:150]
        
        if 'hotel' in content.lower():
            return 'Visit website or call to book with discount code'
        elif 'restaurant' in content.lower() or 'dining' in content.lower():
            return 'Present offer at restaurant or book online'
        elif 'shopping' in content.lower() or 'retail' in content.lower():
            return 'Shop online or in-store with code'
        
        return 'Contact provider for discount details'
    
    def _extract_bonus(self, content: str) -> Optional[str]:
        """Extract bonus benefits"""
        patterns = [r'(?:bonus|extra|additional)[\s:]*([^.\n]+)', r'plus[\s:]*([^.\n]+)']
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    async def search_pdfs(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Search documents
        Returns list of matching discounts with metadata
        """
        logger.info(f"🔍 Searching: '{query}'")
        
        # Search using keyword engine
        results_ranked = self.search_engine.search(query, top_k=top_k)
        
        results = []
        for doc_id, score in results_ranked:
            metadata = self.metadata[doc_id]
            item = dict(metadata)
            item['source'] = doc_id
            item['relevance_score'] = round(score, 3)
            results.append(item)
            logger.info(f"✅ {metadata['name']} (score: {score:.2f})")
        
        logger.info(f"✅ Total: {len(results)} results")
        return results
    
    async def search_pdfs_smart(self, query: str, top_k: int = 10) -> List[Dict]:
        """Alias for search_pdfs"""
        return await self.search_pdfs(query, top_k)
    
    def get_all_discounts_metadata(self) -> List[Dict]:
        """Get all discounts"""
        results = []
        for filename, metadata in self.metadata.items():
            item = dict(metadata)
            item['source'] = filename
            results.append(item)
        return results