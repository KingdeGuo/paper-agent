"""Unified Notification Center — aggregate all alerts across the system."""

import uuid
import json
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy import text as sa_text

from backend.services.registry import get_db
from backend.services.cluster_database import ClusterDatabaseService

logger = logging.getLogger(__name__)
router = APIRouter()


async def ensure_tables(db):
    async with db.async_session_maker() as session:
        await session.execute(sa_text("""CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY, user_id TEXT DEFAULT 'default',
            title TEXT NOT NULL, message TEXT, notification_type TEXT DEFAULT 'info',
            source TEXT, reference_id TEXT, is_read INTEGER DEFAULT 0,
            is_dismissed INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""))
        await session.commit()


@router.get("/notifications", summary="Get all notifications")
async def get_notifications(limit: int = 50, unread_only: bool = False, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        sql = "SELECT * FROM notifications WHERE user_id = 'default' AND is_dismissed = 0"
        params = {}
        if unread_only:
            sql += " AND is_read = 0"
        sql += " ORDER BY created_at DESC LIMIT :lim"
        params["lim"] = limit
        rows = (await session.execute(sa_text(sql), params)).fetchall()
        return [{"id": r[0], "title": r[2], "message": r[3], "type": r[4], "source": r[5],
                 "reference_id": r[6], "is_read": bool(r[7]), "created_at": str(r[9]) if r[9] else None} for r in rows]


@router.get("/notifications/unread-count", summary="Get unread notification count")
async def unread_count(db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        count = (await session.execute(sa_text(
            "SELECT COUNT(*) FROM notifications WHERE user_id = 'default' AND is_read = 0 AND is_dismissed = 0"))).scalar() or 0
        return {"count": count}


@router.post("/notifications", summary="Create a notification")
async def create_notification(title: str, message: str = "", notification_type: str = "info",
                               source: str = None, reference_id: str = None, db=Depends(get_db)):
    await ensure_tables(db)
    nid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO notifications (id, user_id, title, message, notification_type, source, reference_id) "
            "VALUES (:id, 'default', :t, :m, :nt, :s, :ri)"),
            {"id": nid, "t": title, "m": message, "nt": notification_type,
             "s": source, "ri": reference_id})
        await session.commit()
    return {"id": nid, "title": title}


@router.put("/notifications/{notification_id}/read", summary="Mark notification as read")
async def mark_read(notification_id: str, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        await session.execute(sa_text("UPDATE notifications SET is_read = 1 WHERE id = :id"), {"id": notification_id})
        await session.commit()
    return {"message": "Marked as read"}


@router.put("/notifications/read-all", summary="Mark all as read")
async def mark_all_read(db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        await session.execute(sa_text("UPDATE notifications SET is_read = 1 WHERE user_id = 'default' AND is_read = 0"))
        await session.commit()
    return {"message": "All marked as read"}


@router.post("/notifications/scan", summary="Scan all subsystems for notifications")
async def scan_for_notifications(db=Depends(get_db)):
    """Scan all subsystems and generate notifications for important events."""
    await ensure_tables(db)
    created = 0

    # 1. Check conference deadlines
    try:
        async with db.async_session_maker() as session:
            from datetime import datetime as dt, timedelta
            now = dt.utcnow().isoformat()
            upcoming = (await session.execute(sa_text(
                "SELECT id, venue_name, submission_deadline FROM conference_trackers "
                "WHERE user_id = 'default' AND submission_deadline IS NOT NULL "
                "AND submission_deadline > :now AND submission_deadline < :week"),
                {"now": now, "week": (dt.utcnow() + timedelta(days=7)).isoformat()})).fetchall()
            for u in upcoming:
                nid = str(uuid.uuid4())
                await session.execute(sa_text(
                    "INSERT INTO notifications (id, user_id, title, message, notification_type, source, reference_id) "
                    "VALUES (:id, 'default', :t, :m, 'deadline', 'conference', :ri)"),
                    {"id": nid, "t": f"Deadline approaching: {u[1]}",
                     "m": f"Submission deadline for {u[1]} is in less than 7 days.", "ri": u[0]})
                created += 1
    except: pass

    # 2. Check reading list
    try:
        async with db.async_session_maker() as session:
            to_read_count = (await session.execute(sa_text(
                "SELECT COUNT(*) FROM reading_list WHERE user_id = 'default' AND status = 'to_read'"))).scalar() or 0
            if to_read_count > 10:
                nid = str(uuid.uuid4())
                await session.execute(sa_text(
                    "INSERT INTO notifications (id, user_id, title, message, notification_type, source) "
                    "VALUES (:id, 'default', 'Reading queue growing', :m, 'warning', 'reading')"),
                    {"id": nid, "m": f"You have {to_read_count} papers in your reading queue."})
                created += 1
    except: pass

    # 3. Check flashcards due
    try:
        async with db.async_session_maker() as session:
            due = (await session.execute(sa_text(
                "SELECT COUNT(*) FROM flashcards WHERE user_id = 'default' AND is_deleted = 0 AND (next_review IS NULL OR next_review <= :now)"),
                {"now": datetime.utcnow().isoformat()})).scalar() or 0
            if due > 0:
                nid = str(uuid.uuid4())
                await session.execute(sa_text(
                    "INSERT INTO notifications (id, user_id, title, message, notification_type, source) "
                    "VALUES (:id, 'default', 'Flashcards due for review', :m, 'info', 'flashcards')"),
                    {"id": nid, "m": f"You have {due} flashcards to review."})
                created += 1
    except: pass

    await session.commit()
    return {"scanned": True, "notifications_created": created}
