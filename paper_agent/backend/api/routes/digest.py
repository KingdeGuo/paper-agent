"""AI Research Digest - personalized weekly research briefings."""

import json
import logging
import uuid
from datetime import datetime, timedelta

from backend.services.cluster_database import ClusterDatabaseService
from backend.services.llm_service import LLMService
from backend.services.registry import get_db, get_llm_service
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text as sa_text

logger = logging.getLogger(__name__)
router = APIRouter()


async def ensure_digest_table(db: ClusterDatabaseService):
    async with db.async_session_maker() as session:
        await session.execute(sa_text("""
            CREATE TABLE IF NOT EXISTS research_digests (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL DEFAULT 'default',
                title TEXT, summary TEXT, sections TEXT DEFAULT '[]',
                period_start TEXT, period_end TEXT,
                document_ids TEXT DEFAULT '[]', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await session.commit()


@router.post("/generate", summary="Generate a research digest")
async def generate_digest(
    days: int = 7,
    max_docs: int = 20,
    db: ClusterDatabaseService = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Generate an AI research digest from recent documents."""
    await ensure_digest_table(db)

    # Get recent documents
    docs = await db.get_documents(limit=max_docs)
    if not docs:
        raise HTTPException(status_code=400, detail="No documents in library to generate digest from")

    # Filter to recent by date or just use all
    recent = docs[:max_docs]

    # Build digest content
    doc_summaries = []
    for doc in recent:
        meta = doc.doc_metadata or {}
        summary = doc.summary or doc.abstract or "No summary available"
        doc_summaries.append({
            "id": doc.id,
            "title": doc.title or doc.filename,
            "authors": doc.authors or [],
            "year": doc.year,
            "summary": summary[:1000],
            "keywords": doc.keywords or meta.get("keywords", []),
        })

    sections = []

    # Section 1: Document overview
    docs_section = "## Recent Papers\n\n"
    for d in doc_summaries:
        docs_section += f"- **{d['title']}** ({d['year'] or 'n.d.'}) - {', '.join(d['authors'][:3]) or 'Unknown'}\n"
        if d['summary'] != "No summary available":
            docs_section += f"  > {d['summary'][:300]}...\n\n"
    sections.append({"title": "Recent Papers", "content": docs_section})

    # Section 2: AI-generated thematic analysis
    try:
        prompt = "Analyze these papers and identify:\n1. Main research themes\n2. Common methodologies\n3. Key findings or trends\n4. How papers connect to each other\n\nPapers:\n"
        for i, d in enumerate(doc_summaries):
            prompt += f"\nPaper {i+1}: {d['title']} ({d['year']})\nSummary: {d['summary'][:800]}\n"

        response = await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a research analyst. Provide concise, structured analysis. Output in markdown.",
        )
        analysis = response.get("content", "")
        sections.append({"title": "AI Thematic Analysis", "content": analysis})
    except Exception as e:
        logger.warning(f"Thematic analysis failed: {e}")
        sections.append({"title": "AI Thematic Analysis", "content": "AI analysis unavailable for this digest."})

    # Build digest
    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=days)

    digest = {
        "title": f"Research Digest - {period_start.strftime('%b %d')} to {period_end.strftime('%b %d, %Y')}",
        "summary": f"AI-generated overview of {len(doc_summaries)} recent papers in your library.",
        "sections": sections,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "document_ids": [d["id"] for d in doc_summaries],
    }

    # Persist digest
    digest_id = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO research_digests (id, user_id, title, summary, sections, period_start, period_end, document_ids) "
            "VALUES (:id, 'default', :title, :summary, :sections, :ps, :pe, :dids)"
        ), {
            "id": digest_id,
            "title": digest["title"],
            "summary": digest["summary"],
            "sections": json.dumps(sections),
            "ps": digest["period_start"],
            "pe": digest["period_end"],
            "dids": json.dumps(digest["document_ids"]),
        })
        await session.commit()

    digest["id"] = digest_id
    return digest


@router.get("/", summary="List research digests")
async def list_digests(
    limit: int = 10,
    db: ClusterDatabaseService = Depends(get_db),
):
    """List previously generated digests."""
    await ensure_digest_table(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT * FROM research_digests WHERE user_id = 'default' ORDER BY created_at DESC LIMIT :lim"
        ), {"lim": limit})).fetchall()
        return [{
            "id": r[0], "title": r[2], "summary": r[3],
            "sections": json.loads(r[4]) if isinstance(r[4], str) else r[4],
            "period_start": r[5], "period_end": r[6],
            "document_ids": json.loads(r[7]) if isinstance(r[7], str) else r[7],
            "created_at": str(r[8]),
        } for r in rows]


@router.get("/{digest_id}", summary="Get a specific digest")
async def get_digest(
    digest_id: str,
    db: ClusterDatabaseService = Depends(get_db),
):
    """Get a specific digest by ID."""
    await ensure_digest_table(db)
    async with db.async_session_maker() as session:
        row = (await session.execute(sa_text(
            "SELECT * FROM research_digests WHERE id = :id AND user_id = 'default'"
        ), {"id": digest_id})).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Digest not found")
        return {
            "id": row[0], "title": row[2], "summary": row[3],
            "sections": json.loads(row[4]) if isinstance(row[4], str) else row[4],
            "period_start": row[5], "period_end": row[6],
            "document_ids": json.loads(row[7]) if isinstance(row[7], str) else row[7],
            "created_at": str(row[8]),
        }
