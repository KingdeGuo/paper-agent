"""Peer review module — complete paper review workflow."""

import json
import logging
import uuid
from datetime import datetime

from backend.services.registry import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text as sa_text

logger = logging.getLogger(__name__)
router = APIRouter()

REVIEW_STATUSES = ["draft", "submitted", "under_review", "review_completed", "accepted", "revision_needed", "rejected"]
REVIEW_CRITERIA = [
    "novelty", "methodology", "experimental_rigor", "clarity",
    "reproducibility", "related_work", "significance", "overall",
]


async def ensure_tables(db):
    async with db.async_session_maker() as session:
        for ddl in [
            """CREATE TABLE IF NOT EXISTS review_assignments (
                id TEXT PRIMARY KEY, document_id TEXT NOT NULL,
                title TEXT, submitted_by TEXT NOT NULL DEFAULT 'default',
                status TEXT DEFAULT 'draft', journal_target TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted INTEGER DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS review_invitations (
                id TEXT PRIMARY KEY, assignment_id TEXT NOT NULL,
                reviewer_id TEXT NOT NULL, invited_by TEXT,
                status TEXT DEFAULT 'pending', due_date TEXT,
                responded_at TIMESTAMP, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS review_reports (
                id TEXT PRIMARY KEY, assignment_id TEXT NOT NULL,
                reviewer_id TEXT NOT NULL, scores TEXT DEFAULT '{}',
                summary TEXT, strengths TEXT, weaknesses TEXT,
                suggestions TEXT, decision TEXT DEFAULT 'pending',
                is_confidential INTEGER DEFAULT 0,
                submitted_at TIMESTAMP, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS review_discussions (
                id TEXT PRIMARY KEY, assignment_id TEXT NOT NULL,
                user_id TEXT NOT NULL, content TEXT NOT NULL,
                parent_id TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS review_revisions (
                id TEXT PRIMARY KEY, assignment_id TEXT NOT NULL,
                version INTEGER DEFAULT 1, notes TEXT,
                file_path TEXT, submitted_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
        ]:
            try:
                await session.execute(sa_text(ddl))
            except Exception:
                pass
        await session.commit()


# ─── Paper Submission ───────────────────────────────────────

@router.post("/review/submit", summary="Submit a paper for review")
async def submit_for_review(document_id: str, title: str = None, journal_target: str = None, db=Depends(get_db)):
    """Submit a paper from your library for peer review."""
    await ensure_tables(db)
    doc = await db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    aid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO review_assignments (id, document_id, title, submitted_by, status, journal_target) "
            "VALUES (:id, :did, :t, 'default', 'submitted', :jt)"),
            {"id": aid, "did": document_id, "t": title or doc.title or doc.filename, "jt": journal_target})
        await session.commit()
    return {"id": aid, "status": "submitted", "message": "Paper submitted for review"}


@router.get("/review/assignments", summary="List review assignments")
async def list_assignments(status: str = None, db=Depends(get_db)):
    """List all review assignments."""
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        sql = "SELECT ra.*, d.title as doc_title, d.authors FROM review_assignments ra LEFT JOIN documents d ON ra.document_id = d.id WHERE ra.is_deleted = 0"
        params = {}
        if status:
            sql += " AND ra.status = :s"
            params["s"] = status
        sql += " ORDER BY ra.updated_at DESC"
        rows = (await session.execute(sa_text(sql), params)).fetchall()
        return [{
            "id": r[0], "document_id": r[1], "title": r[2] or r[8],
            "submitted_by": r[3], "status": r[4], "journal_target": r[5],
            "doc_title": r[8], "doc_authors": json.loads(r[9]) if isinstance(r[9], str) else (r[9] or []),
            "created_at": str(r[6]) if r[6] else None,
        } for r in rows]


# ─── Reviewer Management ────────────────────────────────────

@router.post("/review/assign/{assignment_id}/reviewer", summary="Assign a reviewer")
async def assign_reviewer(assignment_id: str, reviewer_id: str, due_date: str = None, db=Depends(get_db)):
    """Invite a reviewer to review a paper."""
    await ensure_tables(db)
    iid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO review_invitations (id, assignment_id, reviewer_id, invited_by, due_date) "
            "VALUES (:id, :aid, :rid, 'default', :dd)"),
            {"id": iid, "aid": assignment_id, "rid": reviewer_id, "dd": due_date})
        await session.execute(sa_text(
            "UPDATE review_assignments SET status = 'under_review', updated_at = :n WHERE id = :id"),
            {"n": datetime.utcnow().isoformat(), "id": assignment_id})
        await session.commit()
    return {"id": iid, "reviewer_id": reviewer_id, "status": "pending"}


@router.get("/review/{assignment_id}/reviewers", summary="List reviewers")
async def list_reviewers(assignment_id: str, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT * FROM review_invitations WHERE assignment_id = :aid ORDER BY created_at"),
            {"aid": assignment_id})).fetchall()
        return [{"id": r[0], "reviewer_id": r[2], "invited_by": r[3], "status": r[4],
                 "due_date": str(r[5]) if r[5] else None, "responded_at": str(r[6]) if r[6] else None} for r in rows]


# ─── Review Submission ───────────────────────────────────────

REVIEW_FORM_SCHEMA = {
    "novelty": {"label": "Novelty & Originality", "type": "rating", "min": 1, "max": 10},
    "methodology": {"label": "Methodology Rigor", "type": "rating", "min": 1, "max": 10},
    "experimental_rigor": {"label": "Experimental Rigor", "type": "rating", "min": 1, "max": 10},
    "clarity": {"label": "Clarity & Presentation", "type": "rating", "min": 1, "max": 10},
    "reproducibility": {"label": "Reproducibility", "type": "rating", "min": 1, "max": 10},
    "related_work": {"label": "Related Work Coverage", "type": "rating", "min": 1, "max": 10},
    "significance": {"label": "Significance", "type": "rating", "min": 1, "max": 10},
    "overall": {"label": "Overall Assessment", "type": "rating", "min": 1, "max": 10},
}


@router.get("/review/form", summary="Get review form schema")
async def get_review_form():
    """Get the structured review form schema."""
    return {"criteria": REVIEW_FORM_SCHEMA, "sections": ["summary", "strengths", "weaknesses", "suggestions"]}


@router.post("/review/{assignment_id}/report", summary="Submit a review report")
async def submit_review(assignment_id: str, reviewer_id: str, scores: dict = None,
                        summary: str = "", strengths: str = "", weaknesses: str = "",
                        suggestions: str = "", decision: str = "pending", db=Depends(get_db)):
    """Submit a structured review report."""
    await ensure_tables(db)
    rid = str(uuid.uuid4())
    scores_clean = {}
    if scores:
        for k, v in scores.items():
            if k in REVIEW_FORM_SCHEMA and isinstance(v, (int, float)):
                scores_clean[k] = max(1, min(10, v))

    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO review_reports (id, assignment_id, reviewer_id, scores, summary, strengths, weaknesses, suggestions, decision, submitted_at) "
            "VALUES (:id, :aid, :rid, :sc, :su, :st, :we, :sg, :dec, :n)"),
            {"id": rid, "aid": assignment_id, "rid": reviewer_id, "sc": json.dumps(scores_clean),
             "su": summary, "st": strengths, "we": weaknesses, "sg": suggestions,
             "dec": decision, "n": datetime.utcnow().isoformat()})
        # Update invitation status
        await session.execute(sa_text(
            "UPDATE review_invitations SET status = 'completed', responded_at = :n WHERE assignment_id = :aid AND reviewer_id = :rid"),
            {"n": datetime.utcnow().isoformat(), "aid": assignment_id, "rid": reviewer_id})
        await session.commit()

    return {"id": rid, "message": "Review submitted", "scores": scores_clean, "decision": decision}


@router.get("/review/{assignment_id}/reports", summary="Get review reports")
async def get_reports(assignment_id: str, db=Depends(get_db)):
    """Get all review reports for an assignment."""
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT * FROM review_reports WHERE assignment_id = :aid ORDER BY submitted_at"),
            {"aid": assignment_id})).fetchall()
        reports = []
        for r in rows:
            scores = json.loads(r[3]) if isinstance(r[3], str) else (r[3] or {})
            total = sum(scores.values()) if scores else 0
            count = len(scores) if scores else 1
            reports.append({
                "id": r[0], "reviewer_id": r[2], "scores": scores,
                "average_score": round(total / count, 1) if scores else 0,
                "summary": r[4], "strengths": r[5], "weaknesses": r[6],
                "suggestions": r[7], "decision": r[8],
                "submitted_at": str(r[9]) if r[9] else None,
            })
        return reports


# ─── Decision ────────────────────────────────────────────────

@router.put("/review/{assignment_id}/decision", summary="Make review decision")
async def make_decision(assignment_id: str, decision: str, db=Depends(get_db)):
    """Make a final decision on a review assignment."""
    if decision not in REVIEW_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid decision. Must be one of: {REVIEW_STATUSES}")
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "UPDATE review_assignments SET status = :s, updated_at = :n WHERE id = :id"),
            {"s": decision, "n": datetime.utcnow().isoformat(), "id": assignment_id})
        await session.commit()
    return {"assignment_id": assignment_id, "decision": decision}


# ─── Discussion ───────────────────────────────────────────────

@router.post("/review/{assignment_id}/discuss", summary="Add discussion comment")
async def add_discussion(assignment_id: str, content: str, parent_id: str = None, db=Depends(get_db)):
    """Add a discussion comment to a review."""
    await ensure_tables(db)
    did = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO review_discussions (id, assignment_id, user_id, content, parent_id) "
            "VALUES (:id, :aid, 'default', :c, :pid)"),
            {"id": did, "aid": assignment_id, "c": content, "pid": parent_id})
        await session.commit()
    return {"id": did, "message": "Comment added"}
