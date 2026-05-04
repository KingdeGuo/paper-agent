"""AI Methodology Critic — deep structured methodology analysis of papers."""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text as sa_text

from backend.services.registry import get_db, get_llm_service
from backend.services.cluster_database import ClusterDatabaseService
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)
router = APIRouter()

METHODOLOGY_DIMENSIONS = [
    "research_design",
    "data_collection",
    "sample_size",
    "statistical_methods",
    "validity_threats",
    "reproducibility",
    "ethical_considerations",
    "alternative_approaches",
    "strengths",
    "weaknesses",
]


@router.get("/critic/{document_id}", summary="Full methodology critique")
async def critique_methodology(document_id: str, db=Depends(get_db), llm_service=Depends(get_llm_service)):
    """Perform a deep, structured critique of a paper's methodology."""
    doc = await db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    text = f"Title: {doc.title}\nAuthors: {', '.join(doc.authors or [])}\nYear: {doc.year}\nAbstract: {(doc.abstract or '')[:2000]}"

    if not text.strip():
        return {"error": "No text available for analysis"}

    try:
        resp = await llm_service.chat_completion(
            messages=[{"role": "user", "content": f"Perform a deep methodology critique of this paper. Analyze each dimension and provide a score (1-10) and detailed comment.\n\nPaper:\n{text}\n\nDimensions to analyze:\n" + "\n".join(f"- {d.replace('_', ' ').title()}" for d in METHODOLOGY_DIMENSIONS) + "\n\nOutput as JSON: {{\"dimensions\": [{{\"name\": \"...\", \"score\": N, \"comment\": \"...\"}}], \"overall_score\": N, \"summary\": \"...\", \"key_concerns\": [\"...\"], \"recommendations\": [\"...\"]}}"}],
            system_prompt="You are a senior methodology reviewer. Be rigorous, constructive, and specific. Score on a 1-10 scale. Output valid JSON only.",
        )
        content = resp.get("content", "{}") if isinstance(resp, dict) else str(resp)
        import re
        match = re.search(r'\{.*\}', content, re.DOTALL)
        result = json.loads(match.group()) if match else {}
    except Exception as e:
        result = {"error": f"Analysis failed: {e}"}

    return {
        "document_id": document_id,
        "title": doc.title or doc.filename,
        "critique": result,
    }


@router.post("/critic/compare", summary="Compare methodologies across papers")
async def compare_methodologies(document_ids: list[str], db=Depends(get_db), llm_service=Depends(get_llm_service)):
    """Compare methodologies across multiple papers side by side."""
    if len(document_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 papers")

    docs = []
    for did in document_ids[:5]:
        doc = await db.get_document(did)
        if doc:
            docs.append(doc)

    if len(docs) < 2:
        raise HTTPException(status_code=400, detail="Not enough valid documents")

    prompt = "Compare the methodologies of these papers. Create a comparison table and highlight:\n- Key similarities\n- Key differences\n- Which methodology is more rigorous and why\n- Suggestions for improvement\n\n"
    for i, d in enumerate(docs):
        prompt += f"Paper {i+1}: {d.title} ({d.year})\nAuthors: {', '.join(d.authors or [])}\nAbstract: {(d.abstract or '')[:600]}\n\n"

    try:
        resp = await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a methodology comparison expert. Output structured markdown with tables.",
        )
        comparison = resp.get("content", "") if isinstance(resp, dict) else str(resp)
    except Exception as e:
        comparison = f"Comparison unavailable: {e}"

    return {"papers_compared": len(docs), "comparison": comparison}


@router.get("/critic/checklist/{document_id}", summary="Get methodology checklist")
async def get_methodology_checklist(document_id: str, db=Depends(get_db), llm_service=Depends(get_llm_service)):
    """Generate a methodology quality checklist for a paper."""
    doc = await db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    text = f"Title: {doc.title}\nAbstract: {(doc.abstract or '')[:1500]}"

    checklist_items = [
        "Clearly stated research question/hypothesis",
        "Appropriate study design for the research question",
        "Adequate sample size / statistical power",
        "Valid and reliable measurement instruments",
        "Appropriate statistical methods",
        "Confounding variables addressed",
        "Results are reproducible",
        "Limitations are discussed",
        "Ethical considerations mentioned",
        "Code/data availability stated",
    ]

    try:
        resp = await llm_service.chat_completion(
            messages=[{"role": "user", "content": f"Rate this paper on each methodology checklist item (✅/⚠️/❌). Provide brief justification for each.\n\nPaper:\n{text}\n\nItems:\n" + "\n".join(f"- {item}" for item in checklist_items) + "\n\nOutput as JSON: {{\"items\": [{{\"item\": \"...\", \"status\": \"✅|⚠️|❌\", \"justification\": \"...\"}}], \"overall_quality\": \"high|medium|low\", \"total_score\": N}}"}],
            system_prompt="You are a rigorous methodology reviewer. Be honest and specific. Output valid JSON only.",
        )
        content = resp.get("content", "{}") if isinstance(resp, dict) else str(resp)
        import re
        match = re.search(r'\{.*\}', content, re.DOTALL)
        result = json.loads(match.group()) if match else {}
    except Exception as e:
        result = {"error": str(e)}

    return {"document_id": document_id, "checklist": result}
