"""GraphRAG API — graph-based retrieval for deeper research insights."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends

from backend.services.registry import get_db, get_vector_service, get_llm_service
from backend.services.graphrag_service import GraphRAGEngine, GraphRAGCommunityDetector, GraphRAGConfig
from backend.services.cluster_database import ClusterDatabaseService
from backend.services.vector_service import VectorService
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/graphrag/ask", summary="Ask with GraphRAG")
async def graphrag_ask(
    question: str,
    max_depth: int = 2,
    db=Depends(get_db),
    vector_service=Depends(get_vector_service),
    llm_service=Depends(get_llm_service),
):
    """Ask a question using GraphRAG — graph-based retrieval with citation traversal."""
    config = GraphRAGConfig(max_depth=max_depth)
    engine = GraphRAGEngine(db, vector_service, llm_service, config)
    result = await engine.retrieve(question)
    return result


@router.get("/graphrag/communities", summary="Detect research communities")
async def detect_communities(db=Depends(get_db)):
    """Detect research communities and topic clusters in your library."""
    detector = GraphRAGCommunityDetector()
    communities = await detector.detect_communities(db)
    return {"communities": communities, "count": len(communities)}


@router.post("/graphrag/explore", summary="Explore paper neighborhood")
async def explore_neighborhood(
    document_id: str,
    depth: int = 2,
    db=Depends(get_db),
    vector_service=Depends(get_vector_service),
):
    """Explore the graph neighborhood of a paper — what's connected and how."""
    doc = await db.get_document(document_id)
    if not doc:
        return {"error": "Document not found"}

    engine = GraphRAGEngine(db, vector_service, None, GraphRAGConfig(max_depth=depth))
    graph_nodes = await engine._traverse_graph([document_id], doc.title or "")

    # Categorize connections
    direct_connections = [n for n in graph_nodes if n.get("depth") == 1]
    indirect_connections = [n for n in graph_nodes if n.get("depth", 0) > 1]

    return {
        "center_paper": {"id": doc.id, "title": doc.title or doc.filename, "authors": doc.authors or [], "year": doc.year},
        "direct_connections": [{"id": n["id"], "title": n["title"], "authors": n.get("authors", [])} for n in direct_connections[:10]],
        "indirect_connections": [{"id": n["id"], "title": n["title"], "depth": n.get("depth")} for n in indirect_connections[:10]],
        "direct_count": len(direct_connections),
        "indirect_count": len(indirect_connections),
        "total_explored": len(graph_nodes),
    }
