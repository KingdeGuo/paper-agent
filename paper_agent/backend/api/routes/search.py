import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query

from backend.models.document import SearchQuery, SearchResult, DocumentResponse
from backend.services.database import DatabaseService
from backend.services.vector_service import VectorService
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
db_service = DatabaseService()
vector_service = VectorService()
llm_service = LLMService()

@router.post("/", response_model=List[SearchResult])
async def search_documents(query: SearchQuery):
    """Search documents using semantic search."""
    try:
        # Perform vector search
        vector_results = vector_service.search_similar(
            query=query.query,
            limit=query.limit,
            threshold=query.threshold,
            filters=query.filters
        )
        
        # Get document details
        search_results = []
        for result in vector_results:
            document = await db_service.get_document(result['document_id'])
            if document:
                search_result = SearchResult(
                    document=document,
                    score=result['score'],
                    highlights=[result['text'][:200] + "..." if len(result['text']) > 200 else result['text']]
                )
                search_results.append(search_result)
        
        return search_results
        
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/simple", response_model=List[DocumentResponse])
async def simple_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100),
    year: Optional[int] = Query(None, description="Filter by year"),
    author: Optional[str] = Query(None, description="Filter by author")
):
    """Simple keyword search."""
    try:
        # Build filters
        filters = {}
        if year:
            filters["year"] = year
        if author:
            filters["authors"] = {"$contains": author}
        
        # Perform search
        results = vector_service.search_similar(
            query=q,
            limit=limit,
            threshold=0.5,  # Lower threshold for simple search
            filters=filters if filters else None
        )
        
        # Get documents
        documents = []
        for result in results:
            document = await db_service.get_document(result['document_id'])
            if document:
                documents.append(document)
        
        # If no vector results, fallback to database search
        if not documents:
            documents = await db_service.search_documents(q, limit=limit)
        
        return documents
        
    except Exception as e:
        logger.error(f"Error in simple search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/advanced", response_model=List[SearchResult])
async def advanced_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100),
    threshold: float = Query(0.7, ge=0.0, le=1.0),
    year: Optional[int] = Query(None),
    author: Optional[str] = Query(None),
    title: Optional[str] = Query(None)
):
    """Advanced search with filters."""
    try:
        # Build filters
        filters = {}
        if year:
            filters["year"] = year
        if author:
            filters["authors"] = {"$contains": author}
        if title:
            filters["title"] = {"$contains": title}
        
        # Perform search
        results = vector_service.search_similar(
            query=q,
            limit=limit,
            threshold=threshold,
            filters=filters if filters else None
        )
        
        # Get document details
        search_results = []
        for result in results:
            document = await db_service.get_document(result['document_id'])
            if document:
                search_result = SearchResult(
                    document=document,
                    score=result['score'],
                    highlights=[result['text'][:200] + "..." if len(result['text']) > 200 else result['text']]
                )
                search_results.append(search_result)
        
        return search_results
        
    except Exception as e:
        logger.error(f"Error in advanced search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/similar/{document_id}", response_model=List[DocumentResponse])
async def find_similar_documents(
    document_id: str,
    limit: int = Query(5, ge=1, le=20)
):
    """Find documents similar to a given document."""
    try:
        # Get the document
        document = await db_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get document text
        from backend.services.pdf_processor import PDFProcessor
        pdf_processor = PDFProcessor()
        text = pdf_processor.extract_text(document.file_path)
        
        if not text:
            raise HTTPException(status_code=400, detail="No text content found")
        
        # Use document title and abstract as query
        query = f"{document.title or ''} {document.abstract or ''}"
        if not query.strip():
            query = text[:500]  # Use first 500 chars of text
        
        # Search for similar documents
        results = vector_service.search_similar(
            query=query,
            limit=limit + 1,  # +1 to exclude the document itself
            threshold=0.6
        )
        
        # Get documents, excluding the source document
        similar_documents = []
        for result in results:
            if result['document_id'] != document_id:
                similar_doc = await db_service.get_document(result['document_id'])
                if similar_doc:
                    similar_documents.append(similar_doc)
        
        return similar_documents[:limit]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations", response_model=List[DocumentResponse])
async def get_recommendations(
    user_id: Optional[str] = Query(None, description="User ID for personalized recommendations"),
    limit: int = Query(5, ge=1, le=20)
):
    """Get document recommendations."""
    try:
        # For now, return recent documents as recommendations
        # In a real implementation, this would use user history and ML
        documents = await db_service.get_recent_documents(limit=limit)
        
        # Filter to only include processed documents
        processed_docs = [doc for doc in documents if doc.processed == 2]
        
        return processed_docs
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trending", response_model=List[Dict[str, Any]])
async def get_trending_documents(limit: int = Query(10, ge=1, le=50)):
    """Get trending documents based on recent activity."""
    try:
        # For now, return recent documents sorted by year
        documents = await db_service.get_recent_documents(limit=limit * 2)
        
        # Filter processed documents and sort by year
        processed_docs = [doc for doc in documents if doc.processed == 2]
        
        # Group by year
        year_groups = {}
        for doc in processed_docs:
            year = doc.year or 0
            if year not in year_groups:
                year_groups[year] = []
            year_groups[year].append(doc)
        
        # Create trending list
        trending = []
        for year in sorted(year_groups.keys(), reverse=True):
            for doc in year_groups[year][:3]:  # Max 3 per year
                trending.append({
                    "document": doc,
                    "trending_score": doc.year or 0
                })
        
        return trending[:limit]
        
    except Exception as e:
        logger.error(f"Error getting trending documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
