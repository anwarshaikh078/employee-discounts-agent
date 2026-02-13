"""
Three Parallel Agents for Employee Discount Search

Agent 1: PDFSearchAgent - Searches through PDFs using RAG
Agent 2: FilterAgent - Categorizes and filters results
Agent 3: ResponseGeneratorAgent - Generates final response
"""

import asyncio
import logging
from typing import List, Dict, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base agent class following Google ADK patterns"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
    
    @abstractmethod
    async def execute(self, **kwargs):
        """Execute agent logic"""
        pass

class PDFSearchAgent(BaseAgent):
    """
    Agent 1: Searches through PDF documents using RAG
    Returns: List of matching discounts from PDFs
    """
    
    def __init__(self, rag_tools):
        super().__init__("PDFSearchAgent")
        self.rag_tools = rag_tools
    
    async def search(self, query: str, category_filter: Optional[str] = None) -> List[Dict]:
        """
        Search PDFs for matching discounts
        
        Args:
            query: User search query
            category_filter: Optional category to filter by
        
        Returns:
            List of matching discount documents
        """
        self.logger.info(f"🔍 [Agent 1] Searching PDFs for: '{query}'")
        
        try:
            # Use RAG tools to search
            results = await self.rag_tools.search_pdfs(query)
            
            # Filter by category if provided
            if category_filter:
                results = [
                    r for r in results 
                    if r.get('category', '').lower() == category_filter.lower()
                ]
                self.logger.info(f"📁 Filtered to {len(results)} results in '{category_filter}'")
            
            self.logger.info(f"✅ [Agent 1] Found {len(results)} matches")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ [Agent 1] Search error: {str(e)}")
            return []
    
    async def execute(self, **kwargs):
        """Execute for ADK compatibility"""
        return await self.search(**kwargs)

class FilterAgent(BaseAgent):
    """
    Agent 2: Filters, categorizes, and ranks results
    Returns: Organized and ranked discount list
    """
    
    def __init__(self):
        super().__init__("FilterAgent")
        self.categories = {
            "travel": ["hotel", "flight", "airline", "booking", "travel", "hertz", "expedia"],
            "dining": ["restaurant", "food", "cafe", "dining", "meal", "olive", "chipotle", "starbucks"],
            "retail": ["store", "shop", "clothing", "electronics", "target", "best buy", "home depot"],
            "tech": ["software", "tech", "app", "subscription", "apple", "microsoft", "adobe"],
            "entertainment": ["movie", "show", "theater", "ticket", "netflix", "disney", "amc"],
            "health": ["gym", "wellness", "health", "fitness", "spa", "cvs"],
            "finance": ["bank", "insurance", "investment", "investment", "charles schwab", "state farm"],
        }
    
    async def categorize(self, results: List[Dict]) -> List[Dict]:
        """
        Categorize and organize results
        
        Args:
            results: Raw search results from Agent 1
        
        Returns:
            Categorized and ranked results
        """
        self.logger.info(f"📊 [Agent 2] Categorizing {len(results)} results")
        
        try:
            categorized = []
            
            for result in results:
                # Determine category based on content
                category = self._determine_category(result)
                result['category'] = category
                categorized.append(result)
            
            # Sort by relevance (could be enhanced)
            categorized.sort(key=lambda x: x.get('relevance_score', 0.5), reverse=True)
            
            self.logger.info(f"✅ [Agent 2] Categorized {len(categorized)} results")
            return categorized
            
        except Exception as e:
            self.logger.error(f"❌ [Agent 2] Categorization error: {str(e)}")
            return results
    
    def _determine_category(self, result: Dict) -> str:
        """Determine category based on content"""
        content = (result.get('name', '') + ' ' + result.get('how_to_use', '')).lower()
        
        for category, keywords in self.categories.items():
            if any(keyword in content for keyword in keywords):
                return category.title()
        
        return "Other"
    
    async def execute(self, **kwargs):
        """Execute for ADK compatibility"""
        return await self.categorize(**kwargs)

class ResponseGeneratorAgent(BaseAgent):
    """
    Agent 3: Generates final user-friendly response
    Returns: Formatted response with all details
    """
    
    def __init__(self):
        super().__init__("ResponseGeneratorAgent")
    
    async def generate(self, original_query: str, search_results: List[Dict]) -> Dict:
        """
        Generate final response
        
        Args:
            original_query: Original user query
            search_results: Categorized results from Agent 2
        
        Returns:
            Formatted final response
        """
        self.logger.info(f"📝 [Agent 3] Generating response for {len(search_results)} results")
        
        try:
            # Group by category for better presentation
            by_category = {}
            for result in search_results:
                category = result.get('category', 'Other')
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(result)
            
            # Format results
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    'name': result.get('name', 'Unknown'),
                    'discount': result.get('discount', 'N/A'),
                    'category': result.get('category', 'Other'),
                    'code': result.get('code'),
                    'how_to_use': result.get('how_to_use', ''),
                    'bonus': result.get('bonus'),
                    'source': result.get('source', 'PDF Database')
                })
            
            response = {
                'query': original_query,
                'results': formatted_results,
                'total_found': len(formatted_results),
                'by_category': by_category,
                'message': self._generate_message(original_query, len(formatted_results))
            }
            
            self.logger.info(f"✅ [Agent 3] Response generated with {len(formatted_results)} items")
            return response
            
        except Exception as e:
            self.logger.error(f"❌ [Agent 3] Generation error: {str(e)}")
            return {
                'query': original_query,
                'results': search_results,
                'total_found': len(search_results),
                'message': 'Results generated with partial formatting'
            }
    
    def _generate_message(self, query: str, count: int) -> str:
        """Generate friendly message"""
        if count == 0:
            return f"No discounts found for '{query}'. Try a different search!"
        elif count == 1:
            return f"Found 1 discount for '{query}'!"
        else:
            return f"Found {count} discounts matching '{query}'!"
    
    async def execute(self, **kwargs):
        """Execute for ADK compatibility"""
        return await self.generate(**kwargs)

# Helper function to run agents in parallel
async def run_agents_parallel(
    pdf_search_agent: PDFSearchAgent,
    filter_agent: FilterAgent,
    response_generator_agent: ResponseGeneratorAgent,
    query: str,
    category: Optional[str] = None
) -> Dict:
    """
    Run all 3 agents in parallel
    This is the core orchestration pattern
    """
    
    logger.info("⚡ Running 3 agents in parallel...")
    
    # Agent 1: Search PDFs
    search_task = pdf_search_agent.search(query=query, category_filter=category)
    
    # Agents 2 & 3 wait for Agent 1, but we can structure this differently
    # For true parallelism with dependencies, see main.py
    
    results = await search_task
    
    return {
        'search_results': results
    }