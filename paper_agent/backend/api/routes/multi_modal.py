"""Multi-Modal Support — extract and index figures, tables, and images from papers."""

import logging
import json
import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text as sa_text

from backend.services.registry import get_db, get_llm_service
from backend.services.cluster_database import ClusterDatabaseService
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/multimodal/extract/{document_id}", summary="Extract figures and tables")
async def extract_figures_tables(document_id: str, db=Depends(get_db), llm_service=Depends(get_llm_service)):
    """Extract descriptions of figures, tables, and key visual elements from a paper."""
    doc = await db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    text = (doc.abstract or "") + " " + (doc.summary or "")
    if not text:
        return {"elements": [], "message": "No text available for analysis"}

    try:
        resp = await llm_service.chat_completion(
            messages=[{"role": "user", "content": f"Analyze this paper and identify all figures, tables, and visual elements mentioned. For each, describe: what it shows, key data points, and its purpose. Output as JSON array.\n\nPaper: {doc.title}\nAbstract: {text[:1500]}"}],
            system_prompt="You extract structured descriptions of visual elements from academic papers. Output valid JSON array: [{{\"type\": \"figure|table|algorithm|equation\", \"label\": \"Fig 1\", \"description\": \"...\", \"key_insight\": \"...\"}}]",
        )
        content = resp.get("content", "[]") if isinstance(resp, dict) else str(resp)
        match = re.search(r'\[.*\]', content, re.DOTALL)
        elements = json.loads(match.group()) if match else []
    except Exception as e:
        elements = [{"type": "error", "description": f"Extraction failed: {e}"}]

    return {
        "document_id": document_id,
        "title": doc.title or doc.filename,
        "elements": elements[:15],
        "count": len(elements[:15]),
    }


@router.post("/multimodal/extract-batch", summary="Extract from multiple papers")
async def extract_batch(document_ids: List[str], db=Depends(get_db), llm_service=Depends(get_llm_service)):
    """Extract visual elements from multiple papers at once."""
    results = []
    for did in document_ids[:5]:
        try:
            result = await extract_figures_tables(did, db=db, llm_service=llm_service)
            results.append(result)
        except Exception as e:
            results.append({"document_id": did, "error": str(e)})
    return {"papers": len(results), "results": results}


@router.get("/multimodal/data-tables/{document_id}", summary="Extract data tables")
async def extract_data_tables(document_id: str, db=Depends(get_db), llm_service=Depends(get_llm_service)):
    """Extract numerical data and results tables from a paper."""
    doc = await db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    text = (doc.abstract or "")[:2000]
    try:
        resp = await llm_service.chat_completion(
            messages=[{"role": "user", "content": f"Extract all numerical results, data tables, and experimental results from this paper. Output as structured JSON with table name, columns, and rows. Include metrics, baselines, and key numbers.\n\nPaper: {doc.title}\nAbstract: {text[:1500]}"}],
            system_prompt="You extract numerical data from academic papers. Output JSON: {{\"tables\": [{{\"name\": \"...\", \"columns\": [...], \"rows\": [[...]], \"key_finding\": \"...\"}}]}}",
        )
        content = resp.get("content", "{}") if isinstance(resp, dict) else str(resp)
        match = re.search(r'\{.*\}', content, re.DOTALL)
        data = json.loads(match.group()) if match else {}
    except Exception as e:
        data = {"error": str(e)}

    return {
        "document_id": document_id,
        "title": doc.title or doc.filename,
        **data,
    }
