"""Conference Tracker — track CFP deadlines, conferences, and submissions."""

import uuid
import json
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy import text as sa_text

from backend.services.registry import get_db
from backend.services.cluster_database import ClusterDatabaseService

logger = logging.getLogger(__name__)
router = APIRouter()


CONFERENCE_VENUES = [
    {"id": "neurips", "name": "NeurIPS", "field": "ML/AI", "typical_month": "May"},
    {"id": "icml", "name": "ICML", "field": "ML/AI", "typical_month": "January"},
    {"id": "iclr", "name": "ICLR", "field": "ML/AI", "typical_month": "September"},
    {"id": "aaai", "name": "AAAI", "field": "AI", "typical_month": "August"},
    {"id": "acl", "name": "ACL", "field": "NLP", "typical_month": "February"},
    {"id": "emnlp", "name": "EMNLP", "field": "NLP", "typical_month": "May"},
    {"id": "cvpr", "name": "CVPR", "field": "CV", "typical_month": "November"},
    {"id": "iccv", "name": "ICCV", "field": "CV", "typical_month": "March"},
    {"id": "eccv", "name": "ECCV", "field": "CV", "typical_month": "March"},
    {"id": "acl_rolling", "name": "ACL Rolling Review", "field": "NLP", "typical_month": "Ongoing"},
    {"id": "sigmod", "name": "SIGMOD", "field": "Databases", "typical_month": "July"},
    {"id": "vldb", "name": "VLDB", "field": "Databases", "typical_month": "March"},
    {"id": "osdi", "name": "OSDI", "field": "Systems", "typical_month": "January"},
    {"id": "sosp", "name": "SOSP", "field": "Systems", "typical_month": "April"},
    {"id": "plato", "name": "PLATO", "field": "General", "typical_month": "Various"},
    {"id": "nature", "name": "Nature", "field": "General", "typical_month": "Ongoing"},
    {"id": "science", "name": "Science", "field": "General", "typical_month": "Ongoing"},
]


async def ensure_tables(db):
    async with db.async_session_maker() as session:
        for ddl in [
            """CREATE TABLE IF NOT EXISTS conference_trackers (
                id TEXT PRIMARY KEY, venue_id TEXT NOT NULL,
                venue_name TEXT NOT NULL, field TEXT,
                submission_deadline TEXT, notification_date TEXT,
                conference_date TEXT, location TEXT,
                url TEXT, notes TEXT, status TEXT DEFAULT 'tracking',
                user_id TEXT DEFAULT 'default',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS paper_submissions (
                id TEXT PRIMARY KEY, tracker_id TEXT NOT NULL,
                document_id TEXT, title TEXT, authors TEXT,
                abstract TEXT, status TEXT DEFAULT 'draft',
                submitted_date TEXT, decision TEXT,
                user_id TEXT DEFAULT 'default',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
        ]:
            try: await session.execute(sa_text(ddl))
            except: pass
        await session.commit()


@router.get("/conferences/venues", summary="List known conference venues")
async def list_venues():
    return {"venues": CONFERENCE_VENUES, "count": len(CONFERENCE_VENUES)}


@router.post("/conferences/track", summary="Start tracking a conference deadline")
async def track_conference(venue_id: str, submission_deadline: str = None,
                           notification_date: str = None, conference_date: str = None,
                           url: str = None, notes: str = None, db=Depends(get_db)):
    """Track a conference CFP deadline."""
    await ensure_tables(db)
    venue = next((v for v in CONFERENCE_VENUES if v["id"] == venue_id), None)
    if not venue:
        raise HTTPException(status_code=400, detail=f"Unknown venue: {venue_id}")

    tid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO conference_trackers (id, venue_id, venue_name, field, submission_deadline, notification_date, conference_date, url, notes) "
            "VALUES (:id, :vid, :vn, :f, :sd, :nd, :cd, :u, :n)"),
            {"id": tid, "vid": venue_id, "vn": venue["name"], "f": venue["field"],
             "sd": submission_deadline, "nd": notification_date, "cd": conference_date,
             "u": url, "n": notes})
        await session.commit()
    return {"id": tid, "venue": venue["name"], "status": "tracking"}


@router.get("/conferences/tracked", summary="List tracked conferences")
async def list_tracked(db=Depends(get_db)):
    """List all tracked conferences and deadlines."""
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT ct.*, (SELECT COUNT(*) FROM paper_submissions WHERE tracker_id = ct.id) as submission_count "
            "FROM conference_trackers ct WHERE ct.user_id = 'default' ORDER BY ct.submission_deadline ASC"))).fetchall()

        results = []
        now = datetime.utcnow()
        for r in rows:
            deadline = r[4]
            days_until = None
            if deadline:
                try:
                    dd = datetime.strptime(deadline[:10], "%Y-%m-%d")
                    days_until = (dd - now).days
                except: pass

            urgency = "normal"
            if days_until is not None:
                if days_until < 0: urgency = "past"
                elif days_until < 7: urgency = "critical"
                elif days_until < 30: urgency = "upcoming"

            results.append({
                "id": r[0], "venue_id": r[1], "venue_name": r[2], "field": r[3],
                "submission_deadline": r[4], "notification_date": r[5],
                "conference_date": r[6], "url": r[8], "notes": r[9],
                "status": r[10], "submission_count": r[13] or 0,
                "days_until_deadline": days_until,
                "urgency": urgency,
            })
        return results


@router.put("/conferences/tracked/{tracker_id}", summary="Update tracked conference")
async def update_tracked(tracker_id: str, submission_deadline: str = None,
                          status: str = None, notes: str = None, db=Depends(get_db)):
    await ensure_tables(db)
    sets = []
    params = {"id": tracker_id}
    if submission_deadline: sets.append("submission_deadline = :sd"); params["sd"] = submission_deadline
    if status: sets.append("status = :s"); params["s"] = status
    if notes is not None: sets.append("notes = :n"); params["n"] = notes
    if sets:
        async with db.async_session_maker() as session:
            await session.execute(sa_text(f"UPDATE conference_trackers SET {', '.join(sets)} WHERE id = :id"), params)
            await session.commit()
    return {"message": "Updated"}


@router.delete("/conferences/tracked/{tracker_id}", summary="Remove tracked conference")
async def delete_tracked(tracker_id: str, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        await session.execute(sa_text("DELETE FROM paper_submissions WHERE tracker_id = :id"), {"id": tracker_id})
        await session.execute(sa_text("DELETE FROM conference_trackers WHERE id = :id"), {"id": tracker_id})
        await session.commit()
    return {"message": "Deleted"}


# ─── Paper Submissions ─────────────────────────────────────

@router.post("/conferences/submit", summary="Log a paper submission")
async def log_submission(tracker_id: str, document_id: str = None, title: str = None,
                          abstract: str = None, db=Depends(get_db)):
    """Log a paper submission to a tracked conference."""
    await ensure_tables(db)
    sid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO paper_submissions (id, tracker_id, document_id, title, abstract, status) "
            "VALUES (:id, :tid, :did, :t, :a, 'draft')"),
            {"id": sid, "tid": tracker_id, "did": document_id, "t": title, "a": abstract})
        await session.commit()
    return {"id": sid, "message": "Submission logged"}


@router.get("/conferences/submissions", summary="List all submissions")
async def list_submissions(status: str = None, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        sql = "SELECT ps.*, ct.venue_name, ct.conference_date FROM paper_submissions ps LEFT JOIN conference_trackers ct ON ps.tracker_id = ct.id WHERE ps.user_id = 'default'"
        params = {}
        if status:
            sql += " AND ps.status = :s"
            params["s"] = status
        sql += " ORDER BY ps.created_at DESC"
        rows = (await session.execute(sa_text(sql), params)).fetchall()
        return [{
            "id": r[0], "tracker_id": r[1], "document_id": r[2], "title": r[3],
            "abstract": r[4], "status": r[5], "submitted_date": r[6], "decision": r[7],
            "venue_name": r[9] if len(r) > 9 else None,
            "conference_date": r[10] if len(r) > 10 else None,
        } for r in rows]


@router.put("/conferences/submissions/{submission_id}/decision", summary="Update submission decision")
async def update_decision(submission_id: str, decision: str, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        await session.execute(sa_text("UPDATE paper_submissions SET decision = :d, status = 'decided' WHERE id = :id"),
                              {"d": decision, "id": submission_id})
        await session.commit()
    return {"message": f"Decision updated to: {decision}"}
