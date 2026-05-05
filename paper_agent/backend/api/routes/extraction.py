"""Data extraction: extract tables, figures, key findings from papers."""

import json
import logging
import re as regex

from backend.services.registry import get_db, get_llm_service
from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/extract/{document_id}/findings", summary="Extract key findings")
async def extract_findings(document_id: str, db=Depends(get_db), llm_service=Depends(get_llm_service)):
    """Extract structured key findings from a paper."""
    doc = await db.get_document(document_id)
    if not doc:
        return {"error": "Not found"}
    text = (doc.abstract or "") + "\n" + (doc.summary or "")
    if not text:
        return {"findings": [], "message": "No text available"}
    try:
        resp = await llm_service.chat_completion(
            messages=[{"role": "user", "content": f"Extract structured key findings from this paper. Output JSON: {{\"research_question\": \"...\", \"methodology\": \"...\", \"key_findings\": [\"...\"], \"limitations\": [\"...\"], \"contributions\": [\"...\"]}}\n\n{text[:2000]}"}],
            system_prompt="You are a structured data extraction system. Output valid JSON only.",
        )
        content = resp.get("content", "{}") if isinstance(resp, dict) else str(resp)
        match = regex.search(r'\{.*\}', content, regex.DOTALL)
        data = json.loads(match.group()) if match else {}
    except Exception:
        data = {"key_findings": [], "limitations": [], "contributions": []}

    return {"document_id": document_id, "title": doc.title, **data}


@router.get("/extract/{document_id}/methods", summary="Extract methodology details")
async def extract_methods(document_id: str, db=Depends(get_db), llm_service=Depends(get_llm_service)):
    """Extract methodology details from a paper."""
    doc = await db.get_document(document_id)
    if not doc:
        return {"error": "Not found"}
    text = (doc.abstract or "")[:2000]
    try:
        resp = await llm_service.chat_completion(
            messages=[{"role": "user", "content": f"Extract methodology details. Output JSON: {{\"framework\": \"...\", \"dataset\": \"...\", \"metrics\": [\"...\"], \"baselines\": [\"...\"], \"code_available\": bool}}\n\n{text}"}],
            system_prompt="You are a methodology extraction system. Output valid JSON only.",
        )
        content = resp.get("content", "{}") if isinstance(resp, dict) else str(resp)
        match = regex.search(r'\{.*\}', content, regex.DOTALL)
        data = json.loads(match.group()) if match else {}
    except Exception:
        data = {}
    return {"document_id": document_id, **data}


@router.post("/extract/compare", summary="Compare findings across papers")
async def compare_findings(document_ids: list[str], aspect: str = "methodology", db=Depends(get_db), llm_service=Depends(get_llm_service)):
    """Compare a specific aspect across multiple papers."""
    docs = []
    for did in document_ids[:5]:
        doc = await db.get_document(did)
        if doc:
            docs.append(f"Paper: {doc.title} ({doc.year})\nAbstract: {(doc.abstract or '')[:500]}")

    if len(docs) < 2:
        return {"error": "Need at least 2 papers"}
    try:
        resp = await llm_service.chat_completion(
            messages=[{"role": "user", "content": f"Compare the following papers on '{aspect}'. Create a comparison table in markdown. Highlight similarities and differences.\n\n{chr(10).join(docs)}"}],
            system_prompt="You are a research comparison system. Output structured markdown.",
        )
        comparison = resp.get("content", "") if isinstance(resp, dict) else str(resp)
    except Exception:
        comparison = "Comparison unavailable."
    return {"aspect": aspect, "papers_compared": len(docs), "comparison": comparison}
