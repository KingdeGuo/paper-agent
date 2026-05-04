"""AI Research Assistant — agenda, writing feedback, research direction suggestions."""

import json
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends

from backend.services.registry import get_db, get_llm_service, get_vector_service
from backend.services.cluster_database import ClusterDatabaseService
from backend.services.llm_service import LLMService
from backend.services.vector_service import VectorService

logger = logging.getLogger(__name__)
router = APIRouter()

# ─── Daily Research Agenda ──────────────────────────────────

@router.get("/assistant/agenda", summary="Generate daily research agenda")
async def daily_agenda(db=Depends(get_db), llm_service=Depends(get_llm_service)):
    """Generate a personalized daily research agenda based on library activity."""
    stats = await db.get_processing_stats() if db else {}
    reading_stats = {"to_read": 0, "reading": 0, "read": 0}
    recent_docs = []
    try:
        async with db.async_session_maker() as session:
            from sqlalchemy import text as sa_text
            row = (await session.execute(sa_text(
                "SELECT COUNT(*), SUM(CASE WHEN status='to_read' THEN 1 ELSE 0 END), SUM(CASE WHEN status='reading' THEN 1 ELSE 0 END), SUM(CASE WHEN status='read' THEN 1 ELSE 0 END) FROM reading_list"))).fetchone()
            if row: reading_stats = {"total": row[0] or 0, "to_read": row[1] or 0, "reading": row[2] or 0, "read": row[3] or 0}
            recent_activity = (await session.execute(sa_text(
                "SELECT description, created_at FROM activity_feed ORDER BY created_at DESC LIMIT 5"))).fetchall()
    except: recent_activity = []

    docs = await db.get_documents(limit=5) if db else []
    for d in docs:
        recent_docs.append({"title": d.title or d.filename, "year": d.year})

    day_name = datetime.utcnow().strftime("%A")
    date_str = datetime.utcnow().strftime("%B %d, %Y")

    # AI-suggested focus
    ai_suggestion = ""
    if llm_service and recent_docs:
        try:
            titles = "\n".join(f"- {d['title']} ({d['year']})" for d in recent_docs)
            resp = await llm_service.chat_completion(
                messages=[{"role": "user", "content": f"Today is {day_name}. Based on these papers, suggest what the researcher should focus on today. Be specific and actionable. 2-3 sentences:\n\n{titles}"}],
                system_prompt="You are a research productivity assistant. Give concise, actionable advice.",
            )
            ai_suggestion = resp.get("content", "") if isinstance(resp, dict) else str(resp)
        except: pass

    agenda = {
        "date": date_str,
        "day": day_name,
        "reading_progress": {
            "read": reading_stats.get("read", 0),
            "reading": reading_stats.get("reading", 0),
            "to_read": reading_stats.get("to_read", 0),
            "completion_rate": round((reading_stats.get("read", 0) / max(reading_stats.get("total", 1), 1)) * 100, 1),
        },
        "library_stats": {
            "total": stats.get("total", 0),
            "processed": stats.get("completed", 0),
        },
        "ai_focus_suggestion": ai_suggestion or "Review your reading list and prioritize papers most relevant to your current project.",
        "suggested_actions": [
            f"Read 1 paper from your queue ({reading_stats.get('to_read', 0)} waiting)",
            "Review new papers added to your library",
            "Check research alerts for new matches",
        ],
        "recent_papers": recent_docs[:3],
    }
    return agenda


# ─── Writing Feedback ────────────────────────────────────────

@router.post("/assistant/writing-feedback", summary="Get AI writing feedback")
async def writing_feedback(text: str, context: str = "academic paper section", llm_service=Depends(get_llm_service)):
    """Get AI feedback on academic writing."""
    if len(text) < 50:
        return {"error": "Text too short (min 50 characters)"}

    prompt = f"Please review this {context} and provide structured feedback:\n\n{text[:3000]}"

    try:
        resp = await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=(
                "You are an academic writing coach. Analyze the text for:\n"
                "1. Clarity & conciseness\n"
                "2. Argument structure\n"
                "3. Scientific rigor\n"
                "4. Suggested improvements\n"
                "Be constructive and specific. Output in markdown."
            ),
        )
        feedback = resp.get("content", "") if isinstance(resp, dict) else str(resp)
    except Exception as e:
        feedback = f"Unable to generate feedback: {e}"

    return {"feedback": feedback, "text_length": len(text), "context": context}


# ─── Research Direction Suggestions ─────────────────────────

@router.get("/assistant/research-directions", summary="Suggest research directions")
async def research_directions(db=Depends(get_db), llm_service=Depends(get_llm_service),
                              vector_service=Depends(get_vector_service)):
    """Analyze your library and suggest promising research directions."""
    docs = await db.get_documents(limit=30) if db else []
    if not docs:
        return {"directions": [], "message": "Not enough papers to analyze. Upload more papers first."}

    # Extract topics and keywords
    keywords = {}
    for d in docs:
        for kw in (d.keywords or []):
            keywords[kw] = keywords.get(kw, 0) + 1
    top_keywords = sorted(keywords.items(), key=lambda x: -x[1])[:10]
    recent_years = [d.year for d in docs if d.year and d.year >= 2020]
    year_counts = {}
    for y in recent_years:
        year_counts[y] = year_counts.get(y, 0) + 1

    # AI analysis
    analysis = ""
    if llm_service:
        try:
            titles = "\n".join(f"- {d.title or d.filename} ({d.year or 'n.d.'}) - {', '.join((d.keywords or [])[:3])}" for d in docs[:15])
            resp = await llm_service.chat_completion(
                messages=[{"role": "user", "content": f"Based on this researcher's paper library, suggest 3 promising research directions. For each: direction name, why it fits their existing work, what papers to read next, and potential impact.\n\nPapers:\n{titles}"}],
                system_prompt="You are a research strategist. Be specific about how each direction connects to existing papers in the library.",
            )
            analysis = resp.get("content", "") if isinstance(resp, dict) else str(resp)
        except: pass

    return {
        "total_papers_analyzed": len(docs),
        "top_research_topics": [{"keyword": k, "count": c} for k, c in top_keywords],
        "recent_activity": {str(y): year_counts[y] for y in sorted(year_counts.keys())},
        "ai_suggested_directions": analysis or "AI analysis unavailable. Configure an LLM provider.",
        "recommendation": "Consider exploring intersections between your top research topics. Papers that bridge multiple areas often have higher impact.",
    }


# ─── Weekly Research Briefing ────────────────────────────────

@router.get("/assistant/weekly-briefing", summary="Generate weekly research briefing")
async def weekly_briefing(db=Depends(get_db), llm_service=Depends(get_llm_service)):
    """Generate an executive-level weekly research briefing."""
    docs = await db.get_documents(limit=20) if db else []
    stats = await db.get_processing_stats() if db else {}
    reading_stats = {"to_read": 0, "reading": 0, "read": 0}

    try:
        async with db.async_session_maker() as session:
            from sqlalchemy import text as sa_text
            row = (await session.execute(sa_text(
                "SELECT COUNT(*), SUM(CASE WHEN status='to_read' THEN 1 ELSE 0 END), SUM(CASE WHEN status='reading' THEN 1 ELSE 0 END), SUM(CASE WHEN status='read' THEN 1 ELSE 0 END) FROM reading_list"))).fetchone()
            if row: reading_stats = {"total": row[0] or 0, "to_read": row[1] or 0, "reading": row[2] or 0, "read": row[3] or 0}
    except: pass

    recent_papers = []
    for d in docs[:5]:
        recent_papers.append(f"- **{d.title or d.filename}** ({d.year or 'n.d.'}) — {', '.join((d.authors or [])[:2])}")

    ai_highlight = ""
    if llm_service and recent_papers:
        try:
            resp = await llm_service.chat_completion(
                messages=[{"role": "user", "content": f"Write a 2-paragraph executive briefing highlighting the most important research trends, connections, or insights from this week's papers:\n\n{chr(10).join(recent_papers)}"}],
                system_prompt="You are a research director writing an executive briefing. Be insightful, not just descriptive.",
            )
            ai_highlight = resp.get("content", "") if isinstance(resp, dict) else str(resp)
        except: pass

    return {
        "week_ending": datetime.utcnow().strftime("%B %d, %Y"),
        "library": {"total": stats.get("total", 0), "new_this_week": len(recent_papers)},
        "reading": {"completed": reading_stats.get("read", 0), "progress_pct": reading_stats.get("read", 0) / max(reading_stats.get("total", 1), 1) * 100 if reading_stats.get("total", 0) > 0 else 0},
        "ai_highlight": ai_highlight or "AI highlight unavailable.",
        "recent_papers": recent_papers,
        "key_metrics": {
            "papers_read": reading_stats.get("read", 0),
            "in_progress": reading_stats.get("reading", 0),
            "queue": reading_stats.get("to_read", 0),
            "processed": stats.get("completed", 0),
        },
    }
