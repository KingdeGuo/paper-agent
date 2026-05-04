"""Literature Matrix — cross-paper comparison with AI-extracted dimensions."""

import uuid
import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text as sa_text

from backend.services.registry import get_db, get_llm_service
from backend.services.cluster_database import ClusterDatabaseService
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)
router = APIRouter()


MATRIX_DIMENSIONS = [
    "research_question", "methodology", "dataset", "key_findings",
    "metrics", "baselines", "limitations", "contributions",
    "code_availability", "framework",
]


async def ensure_tables(db):
    async with db.async_session_maker() as session:
        await session.execute(sa_text("""CREATE TABLE IF NOT EXISTS literature_matrix (
            id TEXT PRIMARY KEY, document_id TEXT NOT NULL,
            user_id TEXT DEFAULT 'default', dimensions TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(document_id, user_id)
        )"""))
        await session.commit()


@router.post("/matrix/extract/{document_id}", summary="Extract paper dimensions for matrix")
async def extract_dimensions(document_id: str, db=Depends(get_db), llm_service=Depends(get_llm_service)):
    """Extract structured comparison dimensions from a paper."""
    await ensure_tables(db)
    doc = await db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    text = f"Title: {doc.title}\nAbstract: {(doc.abstract or '')[:1500]}\nSummary: {(doc.summary or '')[:1000]}"
    if len(text.strip()) < 100:
        # Use existing data if no full text
        data = {d: "" for d in MATRIX_DIMENSIONS}
        data["research_question"] = doc.title or ""
        data["methodology"] = "Unknown (no text available)"
        async with db.async_session_maker() as session:
            await session.execute(sa_text(
                "INSERT OR REPLACE INTO literature_matrix (id, document_id, user_id, dimensions) VALUES (:id, :did, 'default', :dims)"),
                {"id": str(uuid.uuid4()), "did": document_id, "dims": json.dumps(data)})
            await session.commit()
        return {"document_id": document_id, "dimensions": data}

    try:
        resp = await llm_service.chat_completion(
            messages=[{"role": "user", "content": f"Extract the following dimensions from this paper. Output as JSON object with these keys: {', '.join(MATRIX_DIMENSIONS)}. If a dimension is not found, use empty string.\n\n{text[:2500]}"}],
            system_prompt="You extract structured data from academic papers. Output valid JSON only. Be concise and factual.",
        )
        content = resp.get("content", "{}") if isinstance(resp, dict) else str(resp)
        import re
        match = re.search(r'\{.*\}', content, re.DOTALL)
        data = json.loads(match.group()) if match else {}
        # Ensure all dimensions exist
        for d in MATRIX_DIMENSIONS:
            if d not in data:
                data[d] = ""
    except Exception as e:
        logger.warning(f"Extraction failed: {e}")
        data = {d: "" for d in MATRIX_DIMENSIONS}

    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT OR REPLACE INTO literature_matrix (id, document_id, user_id, dimensions) VALUES (:id, :did, 'default', :dims)"),
            {"id": str(uuid.uuid4()), "did": document_id, "dims": json.dumps(data)})
        await session.commit()

    return {"document_id": document_id, "dimensions": data, "extracted": len([v for v in data.values() if v])}


@router.get("/matrix", summary="Get literature matrix for multiple papers")
async def get_matrix(document_ids: str, db=Depends(get_db)):
    """Get comparison matrix for selected papers. Comma-separated IDs."""
    await ensure_tables(db)
    ids = [d.strip() for d in document_ids.split(",") if d.strip()]
    if not ids:
        raise HTTPException(status_code=400, detail="At least one document ID required")

    results = []
    async with db.async_session_maker() as session:
        for did in ids:
            row = (await session.execute(sa_text(
                "SELECT dimensions FROM literature_matrix WHERE document_id = :did AND user_id = 'default'"),
                {"did": did})).fetchone()
            doc = await db.get_document(did)
            dims = json.loads(row[0]) if row and row[0] else {}
            results.append({
                "document_id": did,
                "title": doc.title or doc.filename if doc else "Unknown",
                "authors": doc.authors if doc else [],
                "year": doc.year if doc else None,
                "dimensions": dims,
                "has_extraction": bool(row),
            })

    return {
        "papers": results,
        "count": len(results),
        "dimensions": MATRIX_DIMENSIONS,
        "comparison_table": _build_comparison_table(results),
    }


@router.post("/matrix/compare", summary="AI compare papers across dimensions")
async def ai_compare_matrix(document_ids: List[str], db=Depends(get_db), llm_service=Depends(get_llm_service)):
    """Use AI to compare papers and generate insights across dimensions."""
    if len(document_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 papers")

    docs = []
    for did in document_ids[:5]:
        doc = await db.get_document(did)
        if doc:
            docs.append(doc)

    if len(docs) < 2:
        raise HTTPException(status_code=400, detail="Not enough valid documents")

    # Build comparison prompt
    prompt = "Compare the following papers. For each dimension, highlight similarities and differences.\n\n"
    for i, d in enumerate(docs):
        prompt += f"Paper {i+1}: {d.title} ({d.year})\nAuthors: {', '.join(d.authors or [])}\nAbstract: {(d.abstract or '')[:500]}\n\n"

    prompt += "Dimensions to compare: research question, methodology, dataset, key findings, limitations, contributions."

    try:
        resp = await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a research comparison expert. Output structured comparison with clear similarities and differences. Use markdown tables.",
        )
        comparison = resp.get("content", "") if isinstance(resp, dict) else str(resp)
    except Exception as e:
        comparison = f"AI comparison unavailable: {e}"

    return {
        "papers_compared": len(docs),
        "comparison": comparison,
        "paper_titles": [d.title or d.filename for d in docs],
    }


def _build_comparison_table(results):
    """Build a markdown comparison table from extracted data."""
    if not results:
        return ""

    dimensions = MATRIX_DIMENSIONS
    header = "| Dimension | " + " | ".join(r.get("title", "?")[:30] for r in results) + " |"
    separator = "|" + "|".join("---" for _ in range(len(results) + 1)) + "|"
    rows = []
    for dim in dimensions:
        row = f"| **{dim.replace('_', ' ').title()}** "
        for r in results:
            val = r.get("dimensions", {}).get(dim, "")
            row += "| " + (val[:60] if val else "-")
        row += " |"
        rows.append(row)

    return header + "\n" + separator + "\n" + "\n".join(rows)
