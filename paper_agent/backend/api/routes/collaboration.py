"""Collaboration API routes - groups, sharing, comments, activity."""

import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends

from backend.services.registry import get_db
from backend.services.cluster_database import ClusterDatabaseService
from sqlalchemy import text as sa_text

logger = logging.getLogger(__name__)
router = APIRouter()


async def ensure_tables(db: ClusterDatabaseService):
    """Create collaboration tables if needed."""
    async with db.async_session_maker() as session:
        for ddl in [
            """CREATE TABLE IF NOT EXISTS research_groups (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT DEFAULT '',
                owner_id TEXT NOT NULL DEFAULT 'default',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_deleted INTEGER DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS group_members (
                id TEXT PRIMARY KEY, group_id TEXT NOT NULL, user_id TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'member', joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(group_id, user_id)
            )""",
            """CREATE TABLE IF NOT EXISTS shared_documents (
                id TEXT PRIMARY KEY, document_id TEXT NOT NULL, group_id TEXT,
                shared_by TEXT NOT NULL, shared_with TEXT, permission TEXT DEFAULT 'view',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_deleted INTEGER DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS document_comments (
                id TEXT PRIMARY KEY, document_id TEXT NOT NULL, user_id TEXT NOT NULL DEFAULT 'default',
                content TEXT NOT NULL, parent_id TEXT, page_number INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted INTEGER DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS activity_feed (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL DEFAULT 'default',
                document_id TEXT, activity_type TEXT NOT NULL, description TEXT,
                metadata TEXT DEFAULT '{}', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
        ]:
            await session.execute(sa_text(ddl))
        await session.commit()


async def log_activity(db, user_id: str, activity_type: str, description: str, document_id: str = None, metadata: dict = None):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        import json
        await session.execute(sa_text(
            "INSERT INTO activity_feed (id, user_id, document_id, activity_type, description, metadata) VALUES (:id, :uid, :doc_id, :type, :desc, :meta)"
        ), {"id": str(uuid.uuid4()), "uid": user_id, "doc_id": document_id, "type": activity_type,
            "desc": description, "meta": json.dumps(metadata or {})})
        await session.commit()


# ─── Groups ──────────────────────────────────────────────────

@router.post("/groups", summary="Create a research group")
async def create_group(name: str, description: str = ""):
    db = (get_db)()
    await ensure_tables(db)
    gid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO research_groups (id, name, description, owner_id) VALUES (:id, :name, :desc, 'default')"),
            {"id": gid, "name": name, "desc": description})
        await session.execute(sa_text(
            "INSERT INTO group_members (id, group_id, user_id, role) VALUES (:id, :gid, 'default', 'owner')"),
            {"id": str(uuid.uuid4()), "gid": gid})
        await session.commit()
    return {"id": gid, "name": name, "description": description}


@router.get("/groups", summary="List user's groups")
async def list_groups():
    db = (get_db)()
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text("""
            SELECT g.*, (SELECT COUNT(*) FROM group_members WHERE group_id = g.id) as member_count
            FROM research_groups g JOIN group_members gm ON g.id = gm.group_id
            WHERE gm.user_id = 'default' AND g.is_deleted = 0
        """))).fetchall()
        return [{"id": r[0], "name": r[1], "description": r[2], "member_count": r[9]} for r in rows]


# ─── Comments ───────────────────────────────────────────────

@router.get("/comments/{document_id}", summary="Get document comments")
async def get_comments(document_id: str):
    db = (get_db)()
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT * FROM document_comments WHERE document_id = :did AND is_deleted = 0 ORDER BY created_at ASC"
        ), {"did": document_id})).fetchall()
        return [{"id": r[0], "document_id": r[1], "user_id": r[2], "content": r[3],
                 "parent_id": r[4], "page_number": r[5], "created_at": str(r[6])} for r in rows]


@router.post("/comments/{document_id}", summary="Add a comment to a document")
async def add_comment(document_id: str, content: str, parent_id: str = None, page_number: int = None):
    db = (get_db)()
    await ensure_tables(db)
    cid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO document_comments (id, document_id, user_id, content, parent_id, page_number) VALUES (:id, :did, 'default', :content, :pid, :page)"
        ), {"id": cid, "did": document_id, "content": content, "pid": parent_id, "page": page_number})
        await session.commit()

    await log_activity("default", "comment", f"Commented on document", document_id)
    return {"id": cid, "message": "Comment added"}


# ─── Sharing ────────────────────────────────────────────────

@router.post("/share/{document_id}", summary="Share a document")
async def share_document(document_id: str, group_id: str = None, shared_with: str = None, permission: str = "view"):
    db = (get_db)()
    await ensure_tables(db)
    sid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO shared_documents (id, document_id, group_id, shared_by, shared_with, permission) VALUES (:id, :did, :gid, 'default', :sw, :perm)"
        ), {"id": sid, "did": document_id, "gid": group_id, "sw": shared_with, "perm": permission})
        await session.commit()
    await log_activity("default", "share", f"Shared document", document_id)
    return {"id": sid, "message": "Document shared"}


@router.get("/shared", summary="Get shared documents")
async def get_shared_documents():
    db = (get_db)()
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text("""
            SELECT sd.*, d.title, d.authors, d.year FROM shared_documents sd
            JOIN documents d ON sd.document_id = d.id
            WHERE (sd.shared_with = 'default' OR sd.group_id IN (SELECT group_id FROM group_members WHERE user_id = 'default'))
            AND sd.is_deleted = 0 ORDER BY sd.created_at DESC
        """))).fetchall()
        return [{"id": r[0], "document_id": r[1], "shared_by": r[3], "permission": r[5],
                 "created_at": str(r[6]), "title": r[9], "authors": r[10], "year": r[11]} for r in rows]


# ─── Activity Feed ──────────────────────────────────────────

@router.get("/activity", summary="Get activity feed")
async def get_activity(limit: int = 20):
    db = (get_db)()
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT * FROM activity_feed WHERE user_id = 'default' ORDER BY created_at DESC LIMIT :lim"
        ), {"lim": limit})).fetchall()
        return [{"id": r[0], "user_id": r[1], "document_id": r[2], "type": r[3],
                 "description": r[4], "created_at": str(r[6])} for r in rows]
