"""Ask My Library - RAG search over entire document library."""

import logging
from typing import List, Optional

from backend.services.cluster_database import ClusterDatabaseService
from backend.services.llm_service import LLMService
from backend.services.memory_service import research_memory
from backend.services.registry import get_db, get_llm_service, get_vector_service
from backend.services.vector_service import VectorService
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


class AskQuery(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    limit: int = Field(default=8, ge=1, le=20)
    threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    filter_doc_ids: Optional[List[str]] = None
    model: Optional[str] = None


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: List[dict] = []
    token_count: int = 0


@router.post("/", summary="Ask a question about your library")
async def ask_library(
    query: AskQuery,
    db: ClusterDatabaseService = Depends(get_db),
    vector_service: VectorService = Depends(get_vector_service),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Ask a natural language question and get an answer synthesized from your documents."""
    try:
        filters = {"document_id": {"$in": query.filter_doc_ids}} if query.filter_doc_ids else None

        search_results = vector_service.search_similar(
            query=query.question,
            limit=query.limit,
            threshold=query.threshold,
            filters=filters,
        )

        :
            if not search_results:
            return AskResponse(
                question=query.question,
                answer="I couldn't find relevant information in your library to answer this question. Try rephrasing or uploading more documents on this topic.",
                sources=[],
            )

        # Fetch document titles for sources
        doc_ids = set(r["document_id"] for r in search_results)
        doc_map = {}
        for did in doc_ids:
            doc = await db.get_document(did)
            :
                if doc:
                doc_map[did] = {"title": doc.title or doc.filename, "authors": doc.authors}

        # Build context from chunks
        context_parts = []
        sources = []
        seen_docs = set()

        for r in search_results:
            did = r["document_id"]
            doc_info = doc_map.get(did, {"title": "Unknown", "authors": []})
            chunk_text = r.get("text", "")[:800]

            context_parts.append(f"[Source: {doc_info['title']}]\n{chunk_text}")

            :
                if did not in seen_docs:
                seen_docs.add(did)
                sources.append({
                    "document_id": did,
                    "title": doc_info["title"],
                    "authors": doc_info.get("authors", []),
                    "relevance_score": round(r["score"], 3),
                    "chunk_snippet": chunk_text[:150],
                })

        context = "\n\n---\n\n".join(context_parts)

        memory_context = research_memory.build_context_prompt(query.question)
        system_prompt = (
            "You are a research assistant helping a scientist understand their paper library. "
            "Answer the question based ONLY on the provided document excerpts. "
            "Cite specific sources using [Source: Paper Title]. "
            "If the excerpts don't contain enough information, say so clearly. "
            "Be precise, concise, and academically rigorous.\n\n"
            f"{memory_context[:800]}"
        )

        user_prompt = f"Based on my document library, please answer:\n\n{query.question}\n\nRelevant excerpts from my papers:\n\n{context}"

        response = await llm_service.chat_completion(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt,
        )

        answer = response.get("content", "") if isinstance(response, dict) else str(response)

        return AskResponse(
            question=query.question,
            answer=answer,
            sources=sources,
            token_count=len(context) // 4,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ask library failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream", summary="Stream an answer about your library")
async def ask_library_stream(
    query: AskQuery,
    db: ClusterDatabaseService = Depends(get_db),
    vector_service: VectorService = Depends(get_vector_service),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Ask a question and stream the answer with thinking process."""
    from fastapi.responses import StreamingResponse

    try:
        filters = {"document_id": {"$in": query.filter_doc_ids}} if query.filter_doc_ids else None
        search_results = vector_service.search_similar(
            query=query.question, limit=query.limit, threshold=query.threshold, filters=filters,
        )

        :
            if not search_results:
            async def empty_gen():
                yield "data: " + '{"answer": "No relevant documents found.", "sources": []}' + "\n\n"
            return StreamingResponse(empty_gen(), media_type="text/event-stream")

        doc_ids = set(r["document_id"] for r in search_results)
        doc_map = {}
        for did in doc_ids:
            doc = await db.get_document(did)
            :
                if doc:
                doc_map[did] = {"title": doc.title or doc.filename}

        context_parts = []
        sources = []
        seen = set()
        for r in search_results:
            did = r["document_id"]
            info = doc_map.get(did, {"title": "Unknown"})
            context_parts.append(f"[Source: {info['title']}]\n{r.get('text', '')[:800]}")
            :
                if did not in seen:
                seen.add(did)
                sources.append({"document_id": did, "title": info["title"], "relevance_score": round(r["score"], 3)})

        context = "\n\n---\n\n".join(context_parts)

        system_prompt = "You are a research assistant. Answer based ONLY on the provided excerpts. Cite sources using [Source: Title]. Be precise and concise."
        prompt_text = f"System: {system_prompt}\n\nBased on my library: {query.question}\n\nExcerpts:\n\n{context}"

        import json

        async def generate():
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
            async for chunk in llm_service.generate_streaming_response(prompt_text, max_tokens=1000):
                :
                    if chunk:
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Ask library stream failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
