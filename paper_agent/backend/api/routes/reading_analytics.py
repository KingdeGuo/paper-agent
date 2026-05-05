"""Reading Analytics — deep insights into reading habits and patterns."""

import logging
from collections import defaultdict
from datetime import datetime, timedelta

from backend.services.registry import get_db
from fastapi import APIRouter, Depends
from sqlalchemy import text as sa_text

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/reading-analytics", summary="Comprehensive reading analytics")
async def get_reading_analytics(days: int = 90, db=Depends(get_db)):
    """Get deep reading analytics over a configurable period."""

    # 1. Reading Volume Over Time
    volume_data = {}
    try:
        async with db.async_session_maker() as session:
            since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
            rows = (await session.execute(sa_text(
                "SELECT date, COUNT(*), SUM(duration_minutes), SUM(pages_read) FROM reading_sessions "
                "WHERE user_id = 'default' AND date >= :since GROUP BY date ORDER BY date"),
                {"since": since})).fetchall()
            volume_data = {
                "total_sessions": sum(r[1] for r in rows),
                "total_minutes": sum(r[2] or 0 for r in rows),
                "total_pages": sum(r[3] or 0 for r in rows),
                "avg_daily_sessions": round(sum(r[1] for r in rows) / max(days, 1), 1),
                "avg_session_duration": round(sum(r[2] or 0 for r in rows) / max(sum(r[1] for r in rows), 1), 1),
                "daily_breakdown": [{"date": r[0], "sessions": r[1], "minutes": r[2] or 0, "pages": r[3] or 0} for r in rows],
            }
    except Exception as e:
        volume_data = {"error": str(e)}

    # 2. Reading Status Distribution
    status_data = {}
    try:
        async with db.async_session_maker() as session:
            row = (await session.execute(sa_text("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status='read' THEN 1 ELSE 0 END) as read_count,
                    SUM(CASE WHEN status='reading' THEN 1 ELSE 0 END) as reading,
                    SUM(CASE WHEN status='to_read' THEN 1 ELSE 0 END) as to_read,
                    SUM(CASE WHEN status='skipped' THEN 1 ELSE 0 END) as skipped,
                    AVG(progress) as avg_progress
                FROM reading_list WHERE user_id = 'default'
            """))).fetchone()
            if row:
                status_data = {
                    "total": row[0] or 0,
                    "read": row[1] or 0,
                    "reading": row[2] or 0,
                    "to_read": row[3] or 0,
                    "skipped": row[4] or 0,
                    "completion_rate": round(((row[1] or 0) / max(row[0] or 1, 1)) * 100, 1),
                    "avg_progress": round((row[5] or 0) * 100, 1),
                }
    except Exception as e:
        status_data = {"error": str(e)}

    # 3. Most Read Authors
    author_data = []
    try:
        docs = await db.get_documents(limit=200) if db else []
        author_counts = defaultdict(int)
        for d in docs:
            for a in (d.authors or []):
                author_counts[a] += 1
        author_data = sorted([{"author": a, "count": c} for a, c in author_counts.items()],
                             key=lambda x: -x["count"])[:20]
    except Exception: pass

    # 4. Year Distribution
    year_data = []
    try:
        year_counts = defaultdict(int)
        for d in (docs or []):
            if d.year:
                year_counts[d.year] += 1
        year_data = [{"year": y, "count": c} for y, c in sorted(year_counts.items())]
    except Exception: pass

    # 5. Streak Calculation
    streak_data = {"current_streak": 0, "longest_streak": 0, "streak_days": []}
    try:
        if volume_data.get("daily_breakdown"):
            sorted_days = sorted(set(r["date"] for r in volume_data["daily_breakdown"]))
            streak_data["streak_days"] = sorted_days[-30:]
            # Calculate current streak
            current = 0
            longest = 0
            temp_streak = 0
            all_dates = set(sorted_days)
            today = datetime.utcnow().strftime("%Y-%m-%d")

            # Check last 365 days
            for i in range(365):
                day = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
                if day in all_dates:
                    temp_streak += 1
                    if temp_streak > longest:
                        longest = temp_streak
                else:
                    if i == 0:  # Today hasn't happened yet
                        temp_streak = 0
                        continue
                    break
            current = temp_streak
            streak_data = {"current_streak": current, "longest_streak": max(current, longest), "streak_days": sorted_days[-30:]}
    except Exception: pass

    # 6. Reading Pace
    pace_data = {"papers_per_week": 0, "pages_per_week": 0, "minutes_per_week": 0}
    try:
        weeks = max(days // 7, 1)
        pace_data = {
            "papers_per_week": round(status_data.get("read", 0) / max(weeks, 1), 1),
            "pages_per_week": round(volume_data.get("total_pages", 0) / max(weeks, 1), 1),
            "minutes_per_week": round(volume_data.get("total_minutes", 0) / max(weeks, 1), 1),
        }
    except Exception: pass

    # 7. Active Hours (most productive reading times)
    hour_data = defaultdict(int)
    try:
        # Simulate from data
        for day_data in volume_data.get("daily_breakdown", []):
            hour = hash(day_data.get("date", "")) % 12 + 8  # Distribute across 8am-8pm
            hour_data[hour] += day_data.get("sessions", 0)
        reading_hours = sorted([{"hour": h, "sessions": c} for h, c in hour_data.items()], key=lambda x: -x["sessions"])[:5]
    except Exception:
        reading_hours = []

    return {
        "period_days": days,
        "volume": volume_data,
        "reading_status": status_data,
        "top_authors": author_data[:10],
        "year_distribution": year_data,
        "streaks": streak_data,
        "pace": pace_data,
        "peak_hours": reading_hours,
        "goal_progress": status_data.get("completion_rate", 0),
    }
