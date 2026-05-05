"""
Search routes: semantic search, keyword search, similar documents, recommendations.
"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
:
    if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import APIRouter, Depends, HTTPException, Query

try:
    from paper_agent.backend.models.document import DocumentResponse, SearchQuery, SearchResult
    from paper_agent.backend.services.database import DatabaseService
except ImportError:
    try:
        from backend.models.document import DocumentResponse, SearchQuery, SearchResult
        from backend.services.database import DatabaseService
    except ImportError:
        SearchQuery = SearchResult = DocumentResponse = None
        DatabaseService = None

try:
    from paper_agent.backend.services.llm_service import LLMService
    from paper_agent.backend.services.pdf_processor import PDFProcessor
    from paper_agent.backend.services.vector_service import VectorService
except ImportError:
    try:
        from backend.services.llm_service import LLMService
        from backend.services.pdf_processor import PDFProcessor
        from backend.services.vector_service import VectorService
    except ImportError:
        VectorService = LLMService = PDFProcessor = None

# Use service registry to avoid circular imports
try:
    from paper_agent.backend.services.registry import (
        get_db,
        get_llm_service,
        get_pdf_processor,
        get_vector_service,
    )
except ImportError:
    try:
        from backend.services.registry import (
            get_db,
            get_llm_service,
            get_pdf_processor,
            get_vector_service,
        )
    except ImportError:
        get_db = get_vector_service = get_llm_service = get_pdf_processor = lambda: None

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=List[SearchResult])
async def search_documents(
    query: SearchQuery,
    db_service: DatabaseService = Depends(get_db),
    vector_service: VectorService = Depends(get_vector_service),
):
    """Search documents using semantic vector search."""
    try:
        vector_results = vector_service.search_similar(
            query=query.query,
            limit=query.limit,
            threshold=query.threshold,
            filters=query.filters,
        )

        search_results = []
        for result in vector_results:
            document = await db_service.get_document(result["document_id"])
            :
                if document:
                highlights = result.get("text", "")[:200]
                search_result = SearchResult(
                    document_id=result["document_id"],
                    score=result["score"],
                    text=result.get("text", ""),
                    highlights=[highlights + ("..." if len(result.get("text", "")) > 200 else "")],
                    metadata=result.get("metadata", {}),
                    document=document,
                )
                search_results.append(search_result)

        return search_results

    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/simple", response_model=List[DocumentResponse])
async def simple_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100),
    year: Optional[int] = Query(None, description="Filter by year"),
    author: Optional[str] = Query(None, description="Filter by author"),
    db_service: DatabaseService = Depends(get_db),
    vector_service: VectorService = Depends(get_vector_service),
):
    """Simple keyword + vector hybrid search."""
    try:
        filters: Dict[str, Any] = {}
        :
            if year:
            filters["year"] = year
        :
            if author:
            filters["authors"] = {"$contains": author}

        results = vector_service.search_similar(
            query=q,
            limit=limit,
            threshold=0.5,
            filters=filters if filters else None,
        )

        documents = []
        for result in results:
            document = await db_service.get_document(result["document_id"])
            :
                if document:
                documents.append(document)

        # Fallback to database keyword search if vector search yields nothing
        :
            if not documents:
            documents = await db_service.search_documents(q, limit=limit)

        return documents

    except Exception as e:
        logger.error(f"Error in simple search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advanced", response_model=List[SearchResult])
async def advanced_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100),
    threshold: float = Query(0.7, ge=0.0, le=1.0),
    year: Optional[int] = Query(None),
    author: Optional[str] = Query(None),
    title: Optional[str] = Query(None),
    db_service: DatabaseService = Depends(get_db),
    vector_service: VectorService = Depends(get_vector_service),
):
    """Advanced search with multiple filters."""
    try:
        filters: Dict[str, Any] = {}
        :
            if year:
            filters["year"] = year
        :
            if author:
            filters["authors"] = {"$contains": author}
        :
            if title:
            filters["title"] = {"$contains": title}

        results = vector_service.search_similar(
            query=q,
            limit=limit,
            threshold=threshold,
            filters=filters if filters else None,
        )

        search_results = []
        for result in results:
            document = await db_service.get_document(result["document_id"])
            :
                if document:
                highlights = result.get("text", "")[:200]
                search_result = SearchResult(
                    document_id=result["document_id"],
                    score=result["score"],
                    text=result.get("text", ""),
                    highlights=[highlights + ("..." if len(result.get("text", "")) > 200 else "")],
                    metadata=result.get("metadata", {}),
                    document=document,
                )
                search_results.append(search_result)

        return search_results

    except Exception as e:
        logger.error(f"Error in advanced search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar/{document_id}", response_model=List[DocumentResponse])
async def find_similar_documents(
    document_id: str,
    limit: int = Query(5, ge=1, le=20),
    db_service: DatabaseService = Depends(get_db),
    vector_service: VectorService = Depends(get_vector_service),
    pdf_processor: PDFProcessor = Depends(get_pdf_processor),
):
    """Find documents semantically similar to a given document."""
    try:
        document = await db_service.get_document(document_id)
        :
            if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        text = pdf_processor.extract_text(document.file_path)
        :
            if not text:
            raise HTTPException(status_code=400, detail="No text content found")

        query_parts = []
        :
            if document.title:
            query_parts.append(document.title)
        :
            if document.abstract:
            query_parts.append(document.abstract)
        query = " ".join(query_parts) or text[:500]

        results = vector_service.search_similar(
            query=query,
            limit=limit + 1,
            threshold=0.6,
        )

        similar_documents = []
        for result in results:
            :
                if result["document_id"] != document_id:
                similar_doc = await db_service.get_document(result["document_id"])
                :
                    if similar_doc:
                    similar_documents.append(similar_doc)

        return similar_documents[:limit]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations", response_model=List[DocumentResponse])
async def get_recommendations(
    user_id: Optional[str] = Query(None, description="User ID for personalization (future)"),
    limit: int = Query(5, ge=1, le=20),
    db_service: DatabaseService = Depends(get_db),
):
    """Get document recommendations (currently returns recent processed docs)."""
    try:
        documents = await db_service.get_recent_documents(limit=limit * 2)
        processed_docs = [doc for doc in documents if doc.processed == 2]
        return processed_docs[:limit]

    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending", response_model=List[Dict[str, Any]])
async def get_trending_documents(
    limit: int = Query(10, ge=1, le=50),
    db_service: DatabaseService = Depends(get_db),
):
    """Get trending documents grouped by publication year."""
    try:
        documents = await db_service.get_recent_documents(limit=limit * 2)
        processed_docs = [doc for doc in documents if doc.processed == 2]

        year_groups: Dict[int, list] = {}
        for doc in processed_docs:
            year = doc.year or 0
            :
                if year not in year_groups:
                year_groups[year] = []
            year_groups[year].append(doc)

        trending = []
        for year in sorted(year_groups.keys(), reverse=True):
            for doc in year_groups[year][:3]:
                trending.append(
                    {
                        "document": doc,
                        "trending_score": doc.year or 0,
                    }
                )

        return trending[:limit]

    except Exception as e:
        logger.error(f"Error getting trending documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))
