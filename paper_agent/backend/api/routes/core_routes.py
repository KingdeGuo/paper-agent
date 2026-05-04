"""Core Research Intelligence API — essential discovery and organization."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends

from backend.services.core_research import core_intelligence

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/research/cluster", summary="Cluster papers by topic")
async def cluster_papers(max_papers: int = 50):
    """Auto-cluster papers by research topic using AI."""
    return await core_intelligence.cluster_papers(max_papers)


@router.get("/research/cluster", summary="Get paper clusters")
async def get_clusters(max_papers: int = 50):
    return await core_intelligence.cluster_papers(max_papers)


@router.post("/research/search-quote", summary="Search for a quote/claim")
async def search_quote(quote: str, max_results: int = 5):
    """Find which paper a specific quote or claim comes from."""
    return await core_intelligence.search_quote(quote, max_results)


@router.post("/research/auto-tag/{document_id}", summary="Auto-tag a paper")
async def auto_tag_paper(document_id: str):
    """Extract meaningful tags from a paper using AI."""
    return await core_intelligence.auto_tag_paper(document_id)


@router.post("/research/auto-tag-all", summary="Auto-tag all untagged papers")
async def auto_tag_all(max_docs: int = 20):
    return await core_intelligence.auto_tag_all(max_docs)


@router.get("/research/summary-card/{document_id}", summary="Generate paper summary card")
async def summary_card(document_id: str):
    """Generate a structured one-page paper summary."""
    return await core_intelligence.generate_summary_card(document_id)


@router.get("/research/reading-history", summary="Get reading history")
async def reading_history(days: int = 90):
    """Get detailed reading history with analytics."""
    return await core_intelligence.get_reading_history(days)


@router.get("/research/recommend-by-topic", summary="Recommend papers by topic")
async def recommend_by_topic(topic: str, max_results: int = 10):
    """Recommend papers by research topic."""
    return await core_intelligence.recommend_by_topic(topic, max_results=max_results)


@router.get("/research/read-next/{document_id}", summary="Recommend papers to read next")
async def read_next(document_id: str, max_results: int = 5):
    """Recommend papers based on a paper you liked."""
    return await core_intelligence.recommend_what_to_read_next(document_id, max_results)


@router.get("/research/citation-context/{citing_id}/{cited_id}", summary="Get citation context")
async def citation_context(citing_id: str, cited_id: str):
    """Find the context around why a paper cites another."""
    return await core_intelligence.get_citation_context(citing_id, cited_id)


@router.get("/research/concepts", summary="Extract concepts across papers")
async def extract_concepts(document_id: str = None, max_docs: int = 20):
    """Extract key concepts and build a concept map."""
    return await core_intelligence.extract_concepts(document_id, max_docs)


@router.get("/research/concept-graph", summary="Build concept knowledge graph")
async def concept_graph(document_ids: str = None):
    """Build a visual D3.js knowledge graph from extracted concepts."""
    ids = [d.strip() for d in document_ids.split(",")] if document_ids else None
    return await core_intelligence.build_concept_graph(ids)
