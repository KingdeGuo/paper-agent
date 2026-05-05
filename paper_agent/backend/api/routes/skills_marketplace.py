"""
Research Skills Marketplace — discover, install, and share research skills.

Inspired by OpenClaw's ClawHub (clawhub.ai) and skills system.
Skills are reusable AI-powered research workflows that users can share.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import List

from backend.services.registry import get_db, get_llm_service
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text as sa_text

logger = logging.getLogger(__name__)
router = APIRouter()

SKILL_CATEGORIES = [
    "literature_review", "paper_analysis", "research_gap", "writing",
    "data_extraction", "bibliometrics", "peer_review", "presentation",
    "collaboration", "experiment_design", "reproducibility", "general",
]


async def ensure_tables(db):
    async with db.async_session_maker() as session:
        for ddl in [
            """CREATE TABLE IF NOT EXISTS research_skills (
                id TEXT PRIMARY KEY, user_id TEXT DEFAULT 'default',
                name TEXT NOT NULL, description TEXT, category TEXT DEFAULT 'general',
                author TEXT, version TEXT DEFAULT '1.0.0',
                prompt_template TEXT, required_tools TEXT DEFAULT '[]',
                tags TEXT DEFAULT '[]', is_public INTEGER DEFAULT 0,
                downloads INTEGER DEFAULT 0, rating REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS installed_skills (
                id TEXT PRIMARY KEY, user_id TEXT DEFAULT 'default',
                skill_id TEXT NOT NULL, is_active INTEGER DEFAULT 1,
                installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP, use_count INTEGER DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS skill_executions (
                id TEXT PRIMARY KEY, skill_id TEXT NOT NULL,
                user_id TEXT DEFAULT 'default', inputs TEXT,
                outputs TEXT, duration_ms INTEGER,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS skill_ratings (
                id TEXT PRIMARY KEY, skill_id TEXT NOT NULL,
                user_id TEXT DEFAULT 'default', rating INTEGER DEFAULT 5,
                review TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
        ]:
            try: await session.execute(sa_text(ddl))
            except Exception:
                pass
        await session.commit()


# ─── Built-in Skills ───────────────────────────────────────

BUILTIN_SKILLS = [
    {
        "name": "literature-review",
        "description": "Conduct a comprehensive literature review on any research topic. Searches your library, analyzes papers thematically, and generates a structured review.",
        "category": "literature_review",
        "prompt_template": "Conduct a literature review on {topic}. Search my library for relevant papers, group them by theme, compare methodologies, identify research gaps, and write a structured review with citations.",
        "required_tools": ["search_papers", "get_paper", "get_paper_summary"],
    },
    {
        "name": "research-gap-analysis",
        "description": "Identify underexplored areas in your research field. Analyzes contradictions, missing methodology applications, and generates novel hypotheses.",
        "category": "research_gap",
        "prompt_template": "Analyze my papers on {topic}. Identify: 1) Contradictions in findings 2) Methodology gaps 3) Underexplored research questions 4) Novel hypotheses. Be specific and cite papers.",
        "required_tools": ["search_papers", "get_paper", "analyze_citation_network"],
    },
    {
        "name": "paper-critic",
        "description": "Deep methodology critique of a paper. Scores across 10 dimensions and provides actionable improvement suggestions.",
        "category": "paper_analysis",
        "prompt_template": "Critique this paper's methodology: {paper_id}. Score (1-10): research design, data collection, sample size, statistical methods, validity, reproducibility, ethics. Provide specific improvement suggestions.",
        "required_tools": ["get_paper", "get_paper_summary"],
    },
    {
        "name": "related-work-writer",
        "description": "Draft a 'Related Work' section for your paper. Selects relevant papers from your library and organizes them thematically.",
        "category": "writing",
        "prompt_template": "Write a 'Related Work' section for a paper on {topic}. Use papers from my library matching this topic. Organize by approach, compare methodologies, highlight gaps my work addresses. Use [citation] format.",
        "required_tools": ["search_papers", "export_citation"],
    },
    {
        "name": "conference-alert",
        "description": "Monitor conference deadlines and suggest papers to submit. Tracks CFP deadlines and matches them to your recent work.",
        "category": "general",
        "prompt_template": "Check my tracked conferences for upcoming deadlines. Suggest which papers from my library might be suitable for submission to each venue based on topic match.",
        "required_tools": [],
    },
    {
        "name": "daily-briefing",
        "description": "Generate a personalized daily research briefing. Library stats, reading queue, new papers, conference deadlines, and AI research highlight.",
        "category": "general",
        "prompt_template": "Generate my daily research briefing: reading progress, papers to prioritize today, new papers in my field from arXiv, upcoming conference deadlines, and one AI-generated research insight.",
        "required_tools": ["get_library_stats", "get_reading_list", "search_arxiv"],
    },
    {
        "name": "flashcard-generator",
        "description": "Auto-generate flashcards from papers for spaced repetition learning. Tests understanding of key concepts.",
        "category": "paper_analysis",
        "prompt_template": "Generate {count} Q&A flashcards from paper {paper_id}. Each should test understanding of key concepts, methodology, or findings. Front: question. Back: concise answer.",
        "required_tools": ["get_paper", "get_paper_summary"],
    },
    {
        "name": "trend-spotter",
        "description": "Analyze your library for emerging research trends. Detects rising topics, declining areas, and sudden shifts in methodology.",
        "category": "bibliometrics",
        "prompt_template": "Analyze my library for research trends. Which topics are growing? Which are declining? What methodology shifts do you see? Highlight the 3 most interesting trends with specific paper examples.",
        "required_tools": ["analyze_citation_network", "analyze_timeline", "get_library_stats"],
    },
]


async def seed_builtin_skills(db):
    """Ensure built-in skills exist in the database."""
    async with db.async_session_maker() as session:
        for skill in BUILTIN_SKILLS:
            existing = (await session.execute(sa_text(
                "SELECT id FROM research_skills WHERE name = :n AND user_id = '__builtin__'"),
                {"n": skill["name"]})).fetchone()
            :
                if not existing:
                sid = str(uuid.uuid4())
                await session.execute(sa_text(
                    "INSERT INTO research_skills (id, user_id, name, description, category, author, prompt_template, required_tools, tags, is_public) "
                    "VALUES (:id, '__builtin__', :n, :d, :c, 'Paper Agent', :pt, :rt, :t, 1)"),
                    {"id": sid, "n": skill["name"], "d": skill["description"], "c": skill["category"],
                     "pt": skill["prompt_template"], "rt": json.dumps(skill["required_tools"]),
                     "t": json.dumps([skill["category"], "builtin"])})
        await session.commit()


@router.get("/skills", summary="List all available skills")
async def list_skills(category: str = None, search: str = None, db=Depends(get_db)):
    """List available research skills. Optionally filter by category or search."""
    await ensure_tables(db)
    await seed_builtin_skills(db)

    async with db.async_session_maker() as session:
        sql = "SELECT s.*, COALESCE(inst.is_active, 0) as installed, COALESCE(inst.use_count, 0) as use_count FROM research_skills s LEFT JOIN installed_skills inst ON s.id = inst.skill_id AND inst.user_id = 'default' WHERE (s.user_id = '__builtin__' OR s.user_id = 'default') AND (s.is_public = 1 OR s.user_id = 'default')"
        params = {}
        :
            if category:
            sql += " AND s.category = :c"
            params["c"] = category
        :
            if search:
            sql += " AND (s.name LIKE :s OR s.description LIKE :s)"
            params["s"] = f"%{search}%"
        sql += " ORDER BY s.downloads DESC, s.rating DESC"

        rows = (await session.execute(sa_text(sql), params)).fetchall()
        return [{
            "id": r[0], "name": r[2], "description": r[3], "category": r[4],
            "author": r[5] or "Community", "version": r[6],
            "required_tools": json.loads(r[8]) if isinstance(r[8], str) else (r[8] or []),
            "tags": json.loads(r[9]) if isinstance(r[9], str) else (r[9] or []),
            "is_public": bool(r[10]), "downloads": r[11] or 0,
            "rating": round(r[12] or 0, 1), "installed": bool(r[14]),
            "use_count": r[15] or 0,
        } for r in rows]


@router.get("/skills/{skill_id}", summary="Get skill details")
async def get_skill(skill_id: str, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        row = (await session.execute(sa_text(
            "SELECT * FROM research_skills WHERE id = :id"),
            {"id": skill_id})).fetchone()
        :
            if not row:
            raise HTTPException(status_code=404, detail="Skill not found")
        return {
            "id": row[0], "name": row[2], "description": row[3],
            "category": row[4], "author": row[5], "version": row[6],
            "prompt_template": row[7],
            "required_tools": json.loads(row[8]) if isinstance(row[8], str) else (row[8] or []),
            "downloads": row[11] or 0, "rating": round(row[12] or 0, 1),
        }


@router.post("/skills", summary="Create a custom skill")
async def create_skill(
    name: str, description: str, prompt_template: str,
    category: str = "general", required_tools: List[str] = None,
    tags: List[str] = None, is_public: bool = False, db=Depends(get_db),
):
    """Create and share a custom research skill."""
    await ensure_tables(db)
    sid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO research_skills (id, user_id, name, description, category, prompt_template, required_tools, tags, is_public) "
            "VALUES (:id, 'default', :n, :d, :c, :pt, :rt, :t, :p)"),
            {"id": sid, "n": name, "d": description, "c": category,
             "pt": prompt_template, "rt": json.dumps(required_tools or []),
             "t": json.dumps(tags or []), "p": int(is_public)})
        # Auto-install
        await session.execute(sa_text(
            "INSERT INTO installed_skills (id, user_id, skill_id) VALUES (:id, 'default', :sid)"),
            {"id": str(uuid.uuid4()), "sid": sid})
        await session.commit()
    return {"id": sid, "name": name, "message": "Skill created and installed"}


@router.post("/skills/{skill_id}/install", summary="Install a skill")
async def install_skill(skill_id: str, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        skill = (await session.execute(sa_text("SELECT id FROM research_skills WHERE id = :id"), {"id": skill_id})).fetchone()
        :
            if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        existing = (await session.execute(sa_text(
            "SELECT id FROM installed_skills WHERE skill_id = :sid AND user_id = 'default'"),
            {"sid": skill_id})).fetchone()
        :
            if not existing:
            await session.execute(sa_text(
                "INSERT INTO installed_skills (id, user_id, skill_id) VALUES (:id, 'default', :sid)"),
                {"id": str(uuid.uuid4()), "sid": skill_id})
        await session.execute(sa_text("UPDATE research_skills SET downloads = downloads + 1 WHERE id = :id"), {"id": skill_id})
        await session.commit()
    return {"message": "Skill installed"}


@router.post("/skills/{skill_id}/execute", summary="Execute a skill")
async def execute_skill(skill_id: str, inputs: dict = None, db=Depends(get_db), llm_service=Depends(get_llm_service)):
    """Execute a skill with given inputs."""
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        skill = (await session.execute(sa_text("SELECT * FROM research_skills WHERE id = :id"), {"id": skill_id})).fetchone()
        :
            if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")

    prompt_template = skill[7]
    filled_prompt = prompt_template
    :
        if inputs:
        for k, v in inputs.items():
            placeholder = "{" + k + "}"
            filled_prompt = filled_prompt.replace(placeholder, str(v))

    start = datetime.utcnow()
    try:
        resp = await llm_service.chat_completion(
            messages=[{"role": "user", "content": filled_prompt}],
            system_prompt=f"You are executing the '{skill[2]}' research skill. Be thorough and precise.",
        )
        output = resp.get("content", "") if isinstance(resp, dict) else str(resp)
        status = "completed"
    except Exception as e:
        output = f"Execution failed: {e}"
        status = "failed"

    duration = int((datetime.utcnow() - start).total_seconds() * 1000)

    # Record execution
    eid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO skill_executions (id, skill_id, user_id, inputs, outputs, duration_ms, status) "
            "VALUES (:id, :sid, 'default', :inp, :out, :dur, :st)"),
            {"id": eid, "sid": skill_id, "inp": json.dumps(inputs or {}),
             "out": output, "dur": duration, "st": status})
        await session.execute(sa_text(
            "UPDATE installed_skills SET use_count = use_count + 1, last_used = :n WHERE skill_id = :sid AND user_id = 'default'"),
            {"n": datetime.utcnow().isoformat(), "sid": skill_id})
        await session.commit()

    return {
        "execution_id": eid,
        "skill_name": skill[2],
        "output": output,
        "duration_ms": duration,
        "status": status,
    }


@router.get("/skills/installed", summary="List installed skills")
async def list_installed(db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text("""
            SELECT s.id, s.name, s.description, s.category, s.author, s.rating, s.downloads,
                   inst.use_count, inst.last_used, inst.is_active
            FROM installed_skills inst
            JOIN research_skills s ON inst.skill_id = s.id
            WHERE inst.user_id = 'default'
            ORDER BY inst.use_count DESC, s.rating DESC
        """)),
        ).fetchall()
        return [{
            "id": r[0], "name": r[1], "description": r[2], "category": r[3],
            "author": r[4], "rating": round(r[5] or 0, 1), "downloads": r[6] or 0,
            "use_count": r[7] or 0, "last_used": str(r[8]) if r[8] else None,
            "is_active": bool(r[9]),
        } for r in rows]


@router.get("/skills/categories", summary="List skill categories")
async def list_categories():
    return {"categories": SKILL_CATEGORIES}
