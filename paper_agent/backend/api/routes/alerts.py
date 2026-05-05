"""Smart alerts: get notified when new papers match your interests."""

import logging
import uuid
from datetime import datetime

from backend.services.registry import get_db, get_vector_service
from fastapi import APIRouter, Depends
from sqlalchemy import text as sa_text

logger = logging.getLogger(__name__)
router = APIRouter()


async def ensure_tables(db):
    async with db.async_session_maker() as session:
        await session.execute(sa_text("""CREATE TABLE IF NOT EXISTS research_alerts (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL DEFAULT 'default',
            name TEXT NOT NULL, query TEXT NOT NULL, notification_type TEXT DEFAULT 'email',
            frequency TEXT DEFAULT 'daily', last_triggered TIMESTAMP, is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""))
        await session.execute(sa_text("""CREATE TABLE IF NOT EXISTS alert_history (
            id TEXT PRIMARY KEY, alert_id TEXT, user_id TEXT DEFAULT 'default',
            document_id TEXT, message TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""))
        await session.commit()


@router.post("/alerts", summary="Create a research alert")
async def create_alert(name: str, query: str, frequency: str = "daily",
                       notification_type: str = "in_app", db=Depends(get_db)):
    """Create an alert: get notified when new papers match your query."""
    await ensure_tables(db)
    aid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO research_alerts (id, user_id, name, query, frequency, notification_type) VALUES (:id, 'default', :n, :q, :f, :nt)"),
            {"id": aid, "n": name, "q": query, "f": frequency, "nt": notification_type})
        await session.commit()
    return {"id": aid, "name": name, "query": query, "frequency": frequency}


@router.get("/alerts", summary="List research alerts")
async def list_alerts(db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT * FROM research_alerts WHERE user_id = 'default' ORDER BY created_at DESC"))).fetchall()
        return [{"id": r[0], "name": r[2], "query": r[3], "notification_type": r[4],
                 "frequency": r[5], "last_triggered": str(r[6]) if r[6] else None,
                 "is_active": bool(r[7]), "created_at": str(r[9])} for r in rows]


@router.delete("/alerts/{alert_id}", summary="Delete an alert")
async def delete_alert(alert_id: str, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        await session.execute(sa_text("DELETE FROM research_alerts WHERE id = :id"), {"id": alert_id})
        await session.commit()
    return {"message": "Alert deleted"}


@router.post("/alerts/check", summary="Check alerts against new documents")
async def check_alerts(db=Depends(get_db), vector_service=Depends(get_vector_service)):
    """Check all active alerts against recent documents and generate notifications."""
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        alerts = (await session.execute(sa_text(
            "SELECT id, name, query FROM research_alerts WHERE user_id = 'default' AND is_active = 1"))).fetchall()
        docs = await db.get_documents(limit=20)
        notifications = []
        for alert_id, name, query in alerts:
            :
                if vector_service:
                results = vector_service.search_similar(query, limit=3)
                new_matches = [r for r in results if r.get("score", 0) > 0.5]
                for match in new_matches[:3]:
                    nid = str(uuid.uuid4())
                    msg = f"New paper matches your alert '{name}'"
                    await session.execute(sa_text(
                        "INSERT INTO alert_history (id, alert_id, user_id, document_id, message) VALUES (:id, :aid, 'default', :did, :msg)"),
                        {"id": nid, "aid": alert_id, "did": match.get("document_id", ""), "msg": msg})
                    notifications.append({"alert_id": alert_id, "alert_name": name,
                                          "document_id": match.get("document_id"), "message": msg})
            await session.execute(sa_text(
                "UPDATE research_alerts SET last_triggered = :n WHERE id = :id"),
                {"n": datetime.utcnow().isoformat(), "id": alert_id})
        await session.commit()
    return {"checked": len(alerts), "notifications": len(notifications), "matches": notifications}


@router.get("/alerts/history", summary="Get alert notification history")
async def get_alert_history(limit: int = 20, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT ah.*, a.name as alert_name FROM alert_history ah "
            "LEFT JOIN research_alerts a ON ah.alert_id = a.id "
            "WHERE ah.user_id = 'default' ORDER BY ah.created_at DESC LIMIT :lim"),
            {"lim": limit})).fetchall()
        return [{"id": r[0], "alert_id": r[1], "document_id": r[3], "message": r[4],
                 "alert_name": r[6] or "Unknown", "created_at": str(r[5])} for r in rows]
