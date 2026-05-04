"""Platform integration API — DingTalk, Feishu, Slack, WeCom webhooks."""

import uuid
import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text as sa_text

from backend.services.registry import get_db
from backend.services.cluster_database import ClusterDatabaseService
from backend.services.integration_service import (
    IntegrationService, Platform, MessageType, integration_service,
)

logger = logging.getLogger(__name__)
router = APIRouter()


async def ensure_tables(db):
    async with db.async_session_maker() as session:
        await session.execute(sa_text("""CREATE TABLE IF NOT EXISTS webhook_configs (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL DEFAULT 'default',
            platform TEXT NOT NULL, name TEXT NOT NULL,
            webhook_url TEXT NOT NULL, secret TEXT,
            enabled INTEGER DEFAULT 1, notify_on TEXT DEFAULT 'digest',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""))
        await session.commit()


@router.post("/webhooks", summary="Register a webhook")
async def register_webhook(platform: str, name: str, webhook_url: str,
                           secret: str = None, notify_on: str = "digest", db=Depends(get_db)):
    """Register a platform webhook (DingTalk, Feishu, Slack, WeCom)."""
    await ensure_tables(db)
    if platform not in [p.value for p in Platform]:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
    wid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO webhook_configs (id, user_id, platform, name, webhook_url, secret, notify_on) "
            "VALUES (:id, 'default', :p, :n, :u, :s, :no)"),
            {"id": wid, "p": platform, "n": name, "u": webhook_url, "s": secret, "no": notify_on})
        await session.commit()
    return {"id": wid, "platform": platform, "name": name, "notify_on": notify_on}


@router.get("/webhooks", summary="List webhooks")
async def list_webhooks(db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT * FROM webhook_configs WHERE user_id = 'default' ORDER BY created_at DESC"))).fetchall()
        return [{"id": r[0], "platform": r[2], "name": r[3], "webhook_url": r[4][:30] + "...",
                 "enabled": bool(r[6]), "notify_on": r[7]} for r in rows]


@router.delete("/webhooks/{webhook_id}", summary="Delete webhook")
async def delete_webhook(webhook_id: str, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        await session.execute(sa_text("DELETE FROM webhook_configs WHERE id = :id"), {"id": webhook_id})
        await session.commit()
    return {"message": "Deleted"}


@router.post("/webhooks/test", summary="Test a webhook")
async def test_webhook(platform: str, webhook_url: str, secret: str = None):
    """Send a test message to verify webhook configuration."""
    content = (
        "## ✅ Paper Agent Connected!\n\n"
        "Your research library notifications are now active.\n\n"
        "- 📚 Track new papers\n"
        "- 📊 Daily reading progress\n"
        "- 🔔 Research alerts\n"
        "- 📋 Weekly digests\n\n"
        f"*Connected: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*"
    )
    from datetime import datetime
    result = await integration_service.send(
        Platform(platform), webhook_url, content,
        msg_type=MessageType.MARKDOWN, title="Paper Agent Connected", secret=secret,
    )
    return result


@router.post("/webhooks/send-digest", summary="Send digest to all active webhooks")
async def send_digest_to_all(days: int = 7, db=Depends(get_db)):
    """Send research digest to all configured webhooks."""
    from backend.services.registry import get_db as get_db_registry

    await ensure_tables(db)
    async with db.async_session_maker() as session:
        hooks = (await session.execute(sa_text(
            "SELECT * FROM webhook_configs WHERE user_id = 'default' AND enabled = 1"))).fetchall()

    if not hooks:
        return {"message": "No active webhooks configured", "sent": 0}

    # Gather stats
    db_svc = get_db_registry()
    stats = await db_svc.get_processing_stats() if db_svc else {}
    reading_stats = {"to_read": 0, "reading": 0, "read": 0}
    try:
        async with db_svc.async_session_maker() as session:
            row = (await session.execute(sa_text(
                "SELECT COUNT(*), SUM(CASE WHEN status='to_read' THEN 1 ELSE 0 END), SUM(CASE WHEN status='reading' THEN 1 ELSE 0 END), SUM(CASE WHEN status='read' THEN 1 ELSE 0 END) FROM reading_list"))).fetchone()
            if row: reading_stats = {"total": row[0] or 0, "to_read": row[1] or 0, "reading": row[2] or 0, "read": row[3] or 0}
    except: pass

    stats.update(reading_stats)
    stats["read_progress"] = round((reading_stats.get("read", 0) / max(reading_stats.get("total", 1), 1)) * 100, 1)
    stats["sessions"] = 0
    stats["minutes"] = 0
    stats["pages"] = 0
    stats["new_papers"] = f"{stats.get('total', 0)} total papers in library"

    results = []
    for hook in hooks:
        result = await integration_service.send_digest(
            Platform(hook[2]), hook[4], stats,
            secret=hook[5],
        )
        results.append({"platform": hook[2], "name": hook[3], "success": result.get("success")})

    return {"sent": len(results), "results": results}


from datetime import datetime
