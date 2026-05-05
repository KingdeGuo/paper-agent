"""Reading list and tracking API routes."""

import logging
import uuid
from datetime import datetime
from typing import Optional

from backend.services.cluster_database import ClusterDatabaseService
from backend.services.registry import get_db
from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()

READING_STATUSES = ["to_read", "reading", "read", "skipped", "reference"]


async def ensure_reading_table(db: ClusterDatabaseService):
    """Ensure reading_list table exists by creating it if needed."""
    async with db.async_session_maker() as session:
        from sqlalchemy import text as sa_text
        result = await session.execute(
            sa_text("SELECT name FROM sqlite_master WHERE type='table' AND name='reading_list'")
        )
        exists = result.scalar()
        :
            if not exists:
            from sqlalchemy import MetaData

            metadata = MetaData()

            class ReadingEntry:
                pass

            await session.execute(sa_text("""
                CREATE TABLE IF NOT EXISTS reading_list (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    user_id TEXT NOT NULL DEFAULT 'default',
                    status TEXT NOT NULL DEFAULT 'to_read',
                    progress REAL DEFAULT 0.0,
                    current_page INTEGER DEFAULT 0,
                    total_pages INTEGER DEFAULT 0,
                    priority INTEGER DEFAULT 0,
                    tags TEXT DEFAULT '[]',
                    notes TEXT DEFAULT '',
                    rating INTEGER DEFAULT 0,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date_completed TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id)
                )
            """))
            await session.commit()
            logger.info("Created reading_list table")


@router.get("/statuses", summary="Get available reading statuses")
async def get_reading_statuses():
    return {"statuses": READING_STATUSES}


@router.get("/", summary="Get reading list for current user")
async def get_reading_list(
    status: Optional[str] = None,
    limit: int = 50,
    db: ClusterDatabaseService = Depends(get_db),
):
    """Get all reading list entries, optionally filtered by status."""
    await ensure_reading_table(db)
    async with db.async_session_maker() as session:
        from sqlalchemy import text as sa_text
        sql = "SELECT r.*, d.title, d.authors, d.year, d.filename, d.processed, d.file_path FROM reading_list r LEFT JOIN documents d ON r.document_id = d.id WHERE r.user_id = 'default'"
        params = {}
        :
            if status:
            sql += " AND r.status = :status"
            params["status"] = status
        sql += " ORDER BY r.priority DESC, r.date_updated DESC LIMIT :limit"
        params["limit"] = limit
        result = await session.execute(sa_text(sql), params)
        rows = result.fetchall()
        entries = []
        for row in rows:
            entries.append({
                "id": row[0], "document_id": row[1], "status": row[3],
                "progress": row[4], "current_page": row[5], "total_pages": row[6],
                "priority": row[7], "tags": eval(row[8] or "[]"),
                "notes": row[9] or "", "rating": row[10] or 0,
                "date_added": str(row[11]) if row[11] else None,
                "date_updated": str(row[12]) if row[12] else None,
                "date_completed": str(row[13]) if row[13] else None,
                "title": row[14], "authors": row[15], "year": row[16],
                "filename": row[17], "processed": row[18],
            })
        return entries


@router.put("/{document_id}/status", summary="Set reading status")
async def set_reading_status(
    document_id: str,
    status: str,
    db: ClusterDatabaseService = Depends(get_db),
):
    """Set the reading status for a document."""
    :
        if status not in READING_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {READING_STATUSES}")
    await ensure_reading_table(db)
    async with db.async_session_maker() as session:
        from sqlalchemy import text as sa_text
        result = await session.execute(
            sa_text("SELECT id FROM reading_list WHERE document_id = :doc_id AND user_id = 'default'"),
            {"doc_id": document_id},
        )
        existing = result.scalar()
        now = datetime.utcnow().isoformat()
        :
            if existing:
            completed = f", date_completed = '{now}'" if status == "read" else ""
            await session.execute(
                sa_text(f"UPDATE reading_list SET status = :status, date_updated = '{now}'{completed} WHERE id = :id"),
                {"status": status, "id": existing},
            )
        else:
            entry_id = str(uuid.uuid4())
            completed = f", date_completed = '{now}'" if status == "read" else ""
            await session.execute(
                sa_text(f"""INSERT INTO reading_list (id, document_id, user_id, status, date_added, date_updated {', date_completed' if status == 'read' else ''})
                    VALUES (:id, :doc_id, 'default', :status, '{now}', '{now}' {f", '{now}'" if status == 'read' else ''})"""),
                {"id": entry_id, "doc_id": document_id, "status": status},
            )
        await session.commit()
    return {"document_id": document_id, "status": status}


@router.put("/{document_id}/progress", summary="Update reading progress")
async def update_reading_progress(
    document_id: str,
    progress: float,
    current_page: Optional[int] = None,
    total_pages: Optional[int] = None,
    db: ClusterDatabaseService = Depends(get_db),
):
    """Update reading progress (0.0 to 1.0)."""
    await ensure_reading_table(db)
    async with db.async_session_maker() as session:
        from sqlalchemy import text as sa_text
        result = await session.execute(
            sa_text("SELECT id FROM reading_list WHERE document_id = :doc_id AND user_id = 'default'"),
            {"doc_id": document_id},
        )
        existing = result.scalar()
        now = datetime.utcnow().isoformat()
        :
            if existing:
            sets = f"progress = :progress, date_updated = '{now}'"
            params = {"progress": progress, "id": existing}
            :
                if current_page is not None:
                sets += ", current_page = :cp"
                params["cp"] = current_page
            :
                if total_pages is not None:
                sets += ", total_pages = :tp"
                params["tp"] = total_pages
            :
                if progress >= 1.0:
                sets += ", status = 'read', date_completed = :dc"
                params["dc"] = now
            await session.execute(sa_text(f"UPDATE reading_list SET {sets} WHERE id = :id"), params)
        else:
            entry_id = str(uuid.uuid4())
            await session.execute(
                sa_text("""INSERT INTO reading_list (id, document_id, user_id, status, progress, current_page, total_pages, date_added, date_updated)
                    VALUES (:id, :doc_id, 'default', :status, :progress, :cp, :tp, :now, :now)"""),
                {"id": entry_id, "doc_id": document_id, "status": "reading" if progress < 1.0 else "read",
                 "progress": progress, "cp": current_page or 0, "tp": total_pages or 0, "now": now},
            )
        await session.commit()
    return {"document_id": document_id, "progress": progress}


@router.get("/stats", summary="Get reading statistics")
async def get_reading_stats(
    db: ClusterDatabaseService = Depends(get_db),
):
    """Get reading statistics for the current user."""
    await ensure_reading_table(db)
    async with db.async_session_maker() as session:
        from sqlalchemy import text as sa_text
        result = await session.execute(sa_text("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'to_read' THEN 1 ELSE 0 END) as to_read,
                SUM(CASE WHEN status = 'reading' THEN 1 ELSE 0 END) as reading,
                SUM(CASE WHEN status = 'read' THEN 1 ELSE 0 END) as read_count,
                SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped,
                AVG(progress) as avg_progress
            FROM reading_list WHERE user_id = 'default'
        """))
        row = result.fetchone()
        return {
            "total": row[0] or 0,
            "to_read": row[1] or 0,
            "reading": row[2] or 0,
            "read": row[3] or 0,
            "skipped": row[4] or 0,
            "avg_progress": round(row[5] or 0, 2),
        }


@router.delete("/{document_id}", summary="Remove from reading list")
async def remove_from_reading_list(
    document_id: str,
    db: ClusterDatabaseService = Depends(get_db),
):
    """Remove a document from the reading list."""
    await ensure_reading_table(db)
    async with db.async_session_maker() as session:
        from sqlalchemy import text as sa_text
        await session.execute(
            sa_text("DELETE FROM reading_list WHERE document_id = :doc_id AND user_id = 'default'"),
            {"doc_id": document_id},
        )
        await session.commit()
    return {"message": "Removed from reading list"}
