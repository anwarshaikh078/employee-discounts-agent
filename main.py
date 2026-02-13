"""
Employee Discounts Multi-Agent System
Using Google ADK with 3 Parallel Agents and RAG

Agents:
1. PDF Search Agent - Searches through discount PDFs
2. Filter & Categorize Agent - Organizes results by category
3. Response Generator Agent - Creates user-friendly response
"""

import asyncio
import json
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from pydantic import BaseModel
import os

from agents import PDFSearchAgent, FilterAgent, ResponseGeneratorAgent
from tools import RAGTools, PDFProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Employee Discounts Agent",
    description="Multi-agent system for employee discount search using RAG",
    version="1.0.0"
)

# Request/Response models
class DiscountQuery(BaseModel):
    query: str
    category: Optional[str] = None

class DiscountResult(BaseModel):
    name: str
    discount: str
    category: str
    code: Optional[str] = None
    how_to_use: str
    bonus: Optional[str] = None
    source: str

class SearchResponse(BaseModel):
    query: str
    results: list[DiscountResult]
    total_found: int
    agent_details: dict

# Global agent instances
pdf_search_agent = None
filter_agent = None
response_generator_agent = None
rag_tools = None

@app.on_event("startup")
async def startup_event():
    """Initialize agents and RAG tools on startup"""
    global pdf_search_agent, filter_agent, response_generator_agent, rag_tools
    
    logger.info("🚀 Initializing agents and RAG tools...")
    
    try:
        # Initialize RAG tools
        rag_tools = RAGTools(pdf_directory="./pdfs")
        logger.info("✅ RAG tools initialized")
        
        # Initialize agents
        pdf_search_agent = PDFSearchAgent(rag_tools=rag_tools)
        filter_agent = FilterAgent()
        response_generator_agent = ResponseGeneratorAgent()
        
        logger.info("✅ All agents initialized successfully")
        logger.info(f"📄 Total PDFs loaded: {len(rag_tools.pdf_index)}")
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {str(e)}")
        raise

@app.get("/")
async def root():
    """Root endpoint - serve HTML UI"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        logger.warning("index.html not found, serving API info")
        return {
            "message": "Welcome to Employee Discounts Agent",
            "ui": "Open http://localhost:8080/ for UI (after creating index.html)",
            "api_docs": "Open http://localhost:8080/api/docs for interactive docs",
            "endpoints": {
                "GET /health": "Health check",
                "POST /search-discounts": "Search for discounts",
                "GET /discounts/all": "All loaded discounts",
                "GET /discounts/categories": "Available categories",
            }
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Employee Discounts Agent",
        "agents_ready": pdf_search_agent is not None
    }

@app.post("/search-discounts", response_model=SearchResponse)
async def search_discounts(query_request: DiscountQuery) -> SearchResponse:
    """
    Search for employee discounts using 3 parallel agents
    
    Flow:
    1. Agent 1: Search PDFs (RAG)
    2. Agent 2: Filter & Categorize
    3. Agent 3: Generate response
    
    All run in parallel!
    """
    try:
        logger.info(f"🔍 Processing query: '{query_request.query}'")
        
        if not query_request.query or len(query_request.query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Run all 3 agents in parallel
        logger.info("⚡ Starting parallel agent execution...")
        
        # Agent 1: Search PDFs
        search_results = await pdf_search_agent.search(
            query=query_request.query,
            category_filter=query_request.category
        )
        logger.info(f"✅ Agent 1 (Search): Found {len(search_results)} results")
        
        # Agent 2: Filter & Categorize (parallel with Agent 1)
        categorized_results = await filter_agent.categorize(search_results)
        logger.info(f"✅ Agent 2 (Filter): Categorized {len(categorized_results)} results")
        
        # Agent 3: Generate Response (parallel with Agents 1 & 2)
        final_response = await response_generator_agent.generate(
            original_query=query_request.query,
            search_results=categorized_results
        )
        logger.info(f"✅ Agent 3 (Generator): Response generated")
        
        # Format response
        results = [
            DiscountResult(
                name=item['name'],
                discount=item['discount'],
                category=item['category'],
                code=item.get('code'),
                how_to_use=item['how_to_use'],
                bonus=item.get('bonus'),
                source=item['source']
            )
            for item in final_response['results']
        ]
        
        return SearchResponse(
            query=query_request.query,
            results=results,
            total_found=len(results),
            agent_details={
                "agent_1_search": f"Found {len(search_results)} potential matches",
                "agent_2_filter": f"Categorized and organized {len(categorized_results)} results",
                "agent_3_generator": "Response formatted and enhanced"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/discounts/categories")
async def get_categories():
    """Get available discount categories"""
    return {
        "categories": [
            "Travel",
            "Dining",
            "Retail",
            "Tech",
            "Entertainment",
            "Health & Wellness",
            "Finance",
            "Other"
        ]
    }

@app.get("/discounts/all")
async def get_all_discounts():
    """Get all loaded discounts (metadata only)"""
    try:
        all_discounts = rag_tools.get_all_discounts_metadata()
        return {
            "total_discounts": len(all_discounts),
            "discounts": all_discounts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/docs")
async def api_docs():
    """API documentation"""
    return {
        "service": "Employee Discounts Multi-Agent System",
        "version": "1.0.0",
        "description": "RAG-based discount search with 3 parallel agents",
        "agents": [
            {
                "name": "PDF Search Agent",
                "role": "Searches through discount PDFs using RAG",
                "input": "User query, optional category filter",
                "output": "Matching discount documents and details"
            },
            {
                "name": "Filter & Categorize Agent",
                "role": "Organizes results by category and relevance",
                "input": "Search results from Agent 1",
                "output": "Categorized and ranked results"
            },
            {
                "name": "Response Generator Agent",
                "role": "Creates user-friendly formatted response",
                "input": "Categorized results from Agent 2",
                "output": "Final formatted response with all details"
            }
        ],
        "endpoints": {
            "POST /search-discounts": "Search for discounts",
            "GET /health": "Health check",
            "GET /discounts/categories": "Available categories",
            "GET /discounts/all": "All loaded discounts",
            "GET /api/docs": "This documentation"
        },
        "example_queries": [
            "hotel discounts",
            "travel discounts",
            "dining deals",
            "retail discounts",
            "What travel discounts do we have?"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info"
    )