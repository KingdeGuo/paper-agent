"""Research Journal — daily research diary with auto-populated reading data."""

import json
import logging
import uuid
from datetime import datetime
from typing import List

from backend.services.registry import get_db
from fastapi import APIRouter, Depends
from sqlalchemy import text as sa_text

logger = logging.getLogger(__name__)
router = APIRouter()


async def ensure_tables(db):
    async with db.async_session_maker() as session:
        await session.execute(sa_text("""CREATE TABLE IF NOT EXISTS journal_entries (
            id TEXT PRIMARY KEY, user_id TEXT DEFAULT 'default',
            date TEXT NOT NULL, content TEXT, mood TEXT,
            papers_read INTEGER DEFAULT 0, minutes_spent INTEGER DEFAULT 0,
            goals_today TEXT, goals_tomorrow TEXT,
            tags TEXT DEFAULT '[]', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""))
        await session.commit()


@router.post("/journal", summary="Create or update daily journal entry")
async def write_journal(date: str = None, content: str = "",
                         mood: str = None, goals_today: str = None,
                         goals_tomorrow: str = None, tags: List[str] = None,
                         db=Depends(get_db)):
    """Write a daily research journal entry."""
    await ensure_tables(db)
    date = date or datetime.utcnow().strftime("%Y-%m-%d")

    # Auto-calculate reading stats for today
    papers_read = 0
    minutes_spent = 0
    try:
        async with db.async_session_maker() as session:
            row = (await session.execute(sa_text(
                "SELECT COUNT(*), SUM(duration_minutes) FROM reading_sessions WHERE user_id = 'default' AND date = :d"),
                {"d": date})).fetchone()
            if row:
                papers_read = row[0] or 0
                minutes_spent = row[1] or 0

            # Also check reading_list for papers marked read today
            read_today = (await session.execute(sa_text(
                "SELECT COUNT(*) FROM reading_list WHERE user_id = 'default' AND status = 'read' AND date(date_updated) = :d"),
                {"d": date})).scalar()
            if read_today:
                papers_read += read_today
    except Exception: pass

    # Upsert
    async with db.async_session_maker() as session:
        existing = (await session.execute(sa_text(
            "SELECT id FROM journal_entries WHERE user_id = 'default' AND date = :d"), {"d": date})).fetchone()

        if existing:
            sets = ["content = :c", "papers_read = :pr", "minutes_spent = :ms", "updated_at = :n"]
            params = {"id": existing[0], "c": content, "pr": papers_read, "ms": minutes_spent, "n": datetime.utcnow().isoformat()}
            if mood: sets.append("mood = :m"); params["m"] = mood
            if goals_today is not None: sets.append("goals_today = :gt"); params["gt"] = goals_today
            if goals_tomorrow is not None: sets.append("goals_tomorrow = :gtr"); params["gtr"] = goals_tomorrow
            if tags is not None: sets.append("tags = :tg"); params["tg"] = json.dumps(tags)
            await session.execute(sa_text(f"UPDATE journal_entries SET {', '.join(sets)} WHERE id = :id"), params)
        else:
            await session.execute(sa_text(
                "INSERT INTO journal_entries (id, user_id, date, content, mood, papers_read, minutes_spent, goals_today, goals_tomorrow, tags) "
                "VALUES (:id, 'default', :d, :c, :m, :pr, :ms, :gt, :gtr, :tg)"),
                {"id": str(uuid.uuid4()), "d": date, "c": content, "m": mood or "",
                 "pr": papers_read, "ms": minutes_spent, "gt": goals_today or "",
                 "gtr": goals_tomorrow or "", "tg": json.dumps(tags or [])})
        await session.commit()

    return {
        "date": date,
        "content": content,
        "papers_read": papers_read,
        "minutes_spent": minutes_spent,
        "message": "Journal entry saved",
    }


@router.get("/journal", summary="Get journal entries")
async def get_journal(days: int = 30, date: str = None, db=Depends(get_db)):
    """Get journal entries for a date range or specific date."""
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        if date:
            rows = (await session.execute(sa_text(
                "SELECT * FROM journal_entries WHERE user_id = 'default' AND date = :d ORDER BY created_at"),
                {"d": date})).fetchall()
        else:
            from datetime import timedelta
            since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
            rows = (await session.execute(sa_text(
                "SELECT * FROM journal_entries WHERE user_id = 'default' AND date >= :since ORDER BY date DESC"),
                {"since": since})).fetchall()

        return [{
            "id": r[0], "date": r[2], "content": r[3], "mood": r[4] or "",
            "papers_read": r[5] or 0, "minutes_spent": r[6] or 0,
            "goals_today": r[7] or "", "goals_tomorrow": r[8] or "",
            "tags": json.loads(r[9]) if isinstance(r[9], str) else (r[9] or []),
        } for r in rows]


@router.get("/journal/weekly-review", summary="Generate weekly research review")
async def weekly_review(db=Depends(get_db)):
    """Generate an AI-powered weekly research review from journal entries."""
    await ensure_tables(db)
    from datetime import timedelta
    week_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")

    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT date, content, papers_read, minutes_spent, goals_today, mood FROM journal_entries "
            "WHERE user_id = 'default' AND date >= :since ORDER BY date"),
            {"since": week_ago})).fetchall()

    if not rows:
        return {"message": "No journal entries this week", "entries": 0}

    total_papers = sum(r[2] or 0 for r in rows)
    total_minutes = sum(r[3] or 0 for r in rows)
    entries_count = len(rows)

    return {
        "week_ending": datetime.utcnow().strftime("%Y-%m-%d"),
        "entries": entries_count,
        "total_papers_read": total_papers,
        "total_minutes": total_minutes,
        "avg_daily_papers": round(total_papers / max(entries_count, 1), 1),
        "avg_daily_minutes": round(total_minutes / max(entries_count, 1), 1),
        "daily_entries": [{"date": r[0], "papers_read": r[2] or 0, "minutes": r[3] or 0, "mood": r[5] or ""} for r in rows],
    }
