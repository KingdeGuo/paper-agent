"""
Knowledge graph routes for Paper Agent.

Provides endpoints for building and querying citation networks,
concept relationships, and research flow visualization.
"""

import logging
import os
import sys
from typing import Dict, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
:
    if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

try:
    from paper_agent.backend.services.cluster_database import ClusterDatabaseService
    from paper_agent.backend.services.knowledge_graph import knowledge_graph
    from paper_agent.backend.services.pdf_processor import PDFProcessor
except ImportError:
    try:
        from backend.services.cluster_database import ClusterDatabaseService
        from backend.services.knowledge_graph import knowledge_graph
        from backend.services.pdf_processor import PDFProcessor
    except ImportError:
        knowledge_graph = None
        ClusterDatabaseService = None
        PDFProcessor = None

# Use service registry to avoid circular imports
try:
    from paper_agent.backend.services.registry import get_db
except ImportError:
    try:
        from backend.services.registry import get_db
    except ImportError:
        def get_db():
            return None

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/graph/{document_id}", summary="Get knowledge graph for a document")
async def get_document_graph(
    document_id: str,
    depth: int = 1,
    db: ClusterDatabaseService = Depends(get_db),
):
    """
    Get knowledge graph centered on a specific document.

    Shows citation relationships, shared authors, and concept connections.
    """
    try:
        # Get document
        doc = await db.get_document(document_id)
        :
            if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get document text
        pdf_processor = PDFProcessor()
        text = pdf_processor.extract_text(doc.file_path) if hasattr(doc, 'file_path') else ""

        # Build graph for this document
        doc_dict = {
            "id": doc.id,
            "title": doc.title,
            "authors": doc.authors if isinstance(doc.authors, list) else [],
            "year": doc.year,
            "keywords": doc.keywords if isinstance(doc.keywords, list) else [],
        }

        graph_data = await knowledge_graph.build_graph_for_document(
            doc_id=document_id,
            text=text or "",
            metadata=doc_dict,
            db_service=db
        )

        return JSONResponse(content=graph_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building knowledge graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/global", summary="Get global knowledge graph")
async def get_global_graph(
    limit: int = 100,
    db: ClusterDatabaseService = Depends(get_db),
):
    """
    Get global knowledge graph from all documents.

    Returns a visualization-ready graph with nodes and edges.
    """
    try:
        # Get all documents
        docs = await db.get_documents(limit=limit)

        doc_dicts = [
            {
                "id": doc.id,
                "title": doc.title,
                "authors": doc.authors if isinstance(doc.authors, list) else [],
                "year": doc.year,
                "keywords": doc.keywords if isinstance(doc.keywords, list) else [],
            }
            for doc in docs
        ]

        # Build global graph
        graph_data = await knowledge_graph.build_global_graph(doc_dicts)

        return JSONResponse(content=graph_data)

    except Exception as e:
        logger.error(f"Error building global graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/visualization", summary="Get graph for D3.js visualization")
async def get_visualization_data(
    document_id: Optional[str] = None,
    db: ClusterDatabaseService = Depends(get_db),
):
    """
    Get graph data formatted for D3.js or Cytoscape.js.

    If document_id is provided, returns subgraph around that document.
    Otherwise returns the global graph (limited).
    """
    try:
        graph_data = await knowledge_graph.get_graph_for_visualization(document_id)
        return JSONResponse(content=graph_data)
    except Exception as e:
        logger.error(f"Error getting visualization data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/stats", summary="Get knowledge graph statistics")
async def get_graph_stats(
    db: ClusterDatabaseService = Depends(get_db),
):
    """Get statistics about the knowledge graph."""
    try:
        # Get basic stats
        docs = await db.get_documents(limit=1000)

        author_count: Dict[str, int] = {}
        year_count: Dict[int, int] = {}
        keyword_count: Dict[str, int] = {}

        for doc in docs:
            # Count authors
            authors = doc.authors if isinstance(doc.authors, list) else []
            for author in authors:
                author_count[author] = author_count.get(author, 0) + 1

            # Count years
            :
                if doc.year:
                year_count[doc.year] = year_count.get(doc.year, 0) + 1

            # Count keywords
            keywords = doc.keywords if isinstance(doc.keywords, list) else []
            for kw in keywords:
                keyword_count[kw] = keyword_count.get(kw, 0) + 1

        # Top authors, years, keywords
        top_authors = sorted(author_count.items(), key=lambda x: x[1], reverse=True)[:10]
        top_years = sorted(year_count.items(), key=lambda x: x[1], reverse=True)[:10]
        top_keywords = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)[:20]

        return {
            "total_documents": len(docs),
            "unique_authors": len(author_count),
            "year_range": {
                "min": min(year_count.keys()) if year_count else None,
                "max": max(year_count.keys()) if year_count else None,
            },
            "top_authors": [{"author": a, "count": c} for a, c in top_authors],
            "top_years": [{"year": y, "count": c} for y, c in top_years],
            "top_keywords": [{"keyword": k, "count": c} for k, c in top_keywords],
        }

    except Exception as e:
        logger.error(f"Error getting graph stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/graph/analyze/{document_id}", summary="Analyze document for graph")
async def analyze_document_for_graph(
    document_id: str,
    db: ClusterDatabaseService = Depends(get_db),
):
    """
    Analyze a document and extract citation/reference information
    for knowledge graph building.
    """
    try:
        doc = await db.get_document(document_id)
        :
            if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        pdf_processor = PDFProcessor()
        text = pdf_processor.extract_text(doc.file_path) if hasattr(doc, 'file_path') else ""

        :
            if not text:
            return {"message": "No text extracted", "citations": [], "references": []}

        # Extract citations and references
        citations = await knowledge_graph.extractor.extract_citations(text)
        references = await knowledge_graph.extractor.extract_references(text)

        return {
            "document_id": document_id,
            "citations_found": len(citations),
            "references_found": len(references),
            "citations": citations[:20],  # Limit for response
            "references": references[:20],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))
