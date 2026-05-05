"""Scholar Perspectives — community insights, discussion threads, and peer perspectives on papers."""

import json
import logging
import uuid
from typing import List

from backend.services.registry import get_db, get_llm_service
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text as sa_text

logger = logging.getLogger(__name__)
router = APIRouter()


async def ensure_tables(db):
    async with db.async_session_maker() as session:
        for ddl in [
            """CREATE TABLE IF NOT EXISTS paper_discussions (
                id TEXT PRIMARY KEY, document_id TEXT NOT NULL,
                user_id TEXT DEFAULT 'default', title TEXT,
                content TEXT NOT NULL, discussion_type TEXT DEFAULT 'insight',
                parent_id TEXT, is_question INTEGER DEFAULT 0,
                upvotes INTEGER DEFAULT 0, tags TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted INTEGER DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS discussion_votes (
                id TEXT PRIMARY KEY, discussion_id TEXT NOT NULL,
                user_id TEXT NOT NULL, vote INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS scholar_annotations (
                id TEXT PRIMARY KEY, document_id TEXT NOT NULL,
                user_id TEXT, content TEXT NOT NULL,
                annotation_type TEXT DEFAULT 'critique',
                page_number INTEGER, visibility TEXT DEFAULT 'workspace',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted INTEGER DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS reading_groups (
                id TEXT PRIMARY KEY, name TEXT NOT NULL,
                description TEXT, created_by TEXT DEFAULT 'default',
                is_public INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS reading_group_members (
                id TEXT PRIMARY KEY, group_id TEXT NOT NULL,
                user_id TEXT NOT NULL, role TEXT DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS reading_group_sessions (
                id TEXT PRIMARY KEY, group_id TEXT NOT NULL,
                document_id TEXT NOT NULL, scheduled_date TEXT,
                notes TEXT, created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
        ]:
            try: await session.execute(sa_text(ddl))
            except Exception: pass
        await session.commit()


# ─── Paper Discussions ─────────────────────────────────────

@router.post("/discussions/{document_id}", summary="Add a discussion/insight on a paper")
async def add_discussion(document_id: str, content: str, title: str = None,
                          discussion_type: str = "insight", parent_id: str = None,
                          is_question: bool = False, tags: List[str] = None,
                          db=Depends(get_db)):
    """Add a discussion thread, insight, or question about a paper."""
    await ensure_tables(db)
    doc = await db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    did = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO paper_discussions (id, document_id, user_id, title, content, discussion_type, parent_id, is_question, tags) "
            "VALUES (:id, :did, 'default', :t, :c, :dt, :pid, :iq, :tg)"),
            {"id": did, "did": document_id, "t": title or content[:50],
             "c": content, "dt": discussion_type, "pid": parent_id,
             "iq": int(is_question), "tg": json.dumps(tags or [])})
        await session.commit()
    return {"id": did, "message": "Discussion added", "type": discussion_type}


@router.get("/discussions/{document_id}", summary="Get paper discussions")
async def get_discussions(document_id: str, discussion_type: str = None, db=Depends(get_db)):
    """Get all discussions and insights for a paper."""
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        sql = "SELECT * FROM paper_discussions WHERE document_id = :did AND is_deleted = 0"
        params = {"did": document_id}
        if discussion_type:
            sql += " AND discussion_type = :dt"
            params["dt"] = discussion_type
        sql += " ORDER BY upvotes DESC, created_at DESC"
        rows = (await session.execute(sa_text(sql), params)).fetchall()

        # Organize into threads
        threads = {}
        for r in rows:
            entry = {
                "id": r[0], "user_id": r[2], "title": r[3], "content": r[4],
                "type": r[5], "parent_id": r[6], "is_question": bool(r[7]),
                "upvotes": r[8] or 0, "tags": json.loads(r[9]) if isinstance(r[9], str) else (r[9] or []),
                "created_at": str(r[10]) if r[10] else None,
                "replies": [],
            }
            if r[6] and r[6] in threads:
                threads[r[6]]["replies"].append(entry)
            else:
                threads[r[0]] = entry

        return {
            "document_id": document_id,
            "discussion_count": len(rows),
            "threads": [t for t in threads.values()],
        }


@router.post("/discussions/{discussion_id}/vote", summary="Upvote a discussion")
async def vote_discussion(discussion_id: str, vote: int = 1, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        existing = (await session.execute(sa_text(
            "SELECT id FROM discussion_votes WHERE discussion_id = :did AND user_id = 'default'"),
            {"did": discussion_id})).fetchone()
        if existing:
            await session.execute(sa_text("DELETE FROM discussion_votes WHERE id = :id"), {"id": existing[0]})
        else:
            await session.execute(sa_text(
                "INSERT INTO discussion_votes (id, discussion_id, user_id, vote) VALUES (:id, :did, 'default', :v)"),
                {"id": str(uuid.uuid4()), "did": discussion_id, "v": vote})
        # Update count
        cnt = (await session.execute(sa_text(
            "SELECT COUNT(*) FROM discussion_votes WHERE discussion_id = :did"), {"did": discussion_id})).scalar() or 0
        await session.execute(sa_text("UPDATE paper_discussions SET upvotes = :c WHERE id = :id"),
                              {"c": cnt, "id": discussion_id})
        await session.commit()
    return {"discussion_id": discussion_id, "upvotes": cnt}


# ─── AI Perspective Synthesis ──────────────────────────────

@router.get("/perspectives/{document_id}/synthesize", summary="AI synthesis of scholar perspectives")
async def synthesize_perspectives(document_id: str, db=Depends(get_db), llm_service=Depends(get_llm_service)):
    """Use AI to synthesize all discussions, annotations, and insights about a paper."""
    await ensure_tables(db)
    doc = await db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Gather all discussions
    async with db.async_session_maker() as session:
        discussions = (await session.execute(sa_text(
            "SELECT content, discussion_type, upvotes FROM paper_discussions WHERE document_id = :did AND is_deleted = 0 ORDER BY upvotes DESC"),
            {"did": document_id})).fetchall()

        annotations = (await session.execute(sa_text(
            "SELECT content, annotation_type FROM scholar_annotations WHERE document_id = :did AND is_deleted = 0"),
            {"did": document_id})).fetchall()

    if not discussions and not annotations:
        return {
            "document_id": document_id,
            "title": doc.title or doc.filename,
            "synthesis": "No community discussions yet. Be the first to share your perspective!",
            "discussion_count": 0,
        }

    # Build context for AI
    all_comments = []
    for d in discussions:
        all_comments.append(f"[{d[1]}] ({d[2]} upvotes): {d[0][:500]}")
    for a in annotations:
        all_comments.append(f"[{a[1]}]: {a[0][:500]}")

    context = "\n".join(all_comments)

    try:
        resp = await llm_service.chat_completion(
            messages=[{"role": "user", "content": f"Synthesize these community perspectives on the paper '{doc.title}'. Identify:\n1. Common themes in what people think\n2. Points of disagreement\n3. Key insights that emerged\n4. Open questions\n\nCommunity perspectives:\n{context}"}],
            system_prompt="You synthesize scholarly discussions. Identify patterns, disagreements, and insights. Be balanced and insightful.",
        )
        synthesis = resp.get("content", "") if isinstance(resp, dict) else str(resp)
    except Exception as e:
        synthesis = f"AI synthesis unavailable: {e}"

    return {
        "document_id": document_id,
        "title": doc.title or doc.filename,
        "synthesis": synthesis,
        "discussion_count": len(discussions),
        "annotation_count": len(annotations),
    }


# ─── Reading Groups (Journal Club) ─────────────────────────

@router.post("/reading-groups", summary="Create a reading group")
async def create_reading_group(name: str, description: str = "", is_public: bool = False, db=Depends(get_db)):
    await ensure_tables(db)
    gid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO reading_groups (id, name, description, created_by, is_public) VALUES (:id, :n, :d, 'default', :p)"),
            {"id": gid, "n": name, "d": description, "p": int(is_public)})
        await session.execute(sa_text(
            "INSERT INTO reading_group_members (id, group_id, user_id, role) VALUES (:id, :gid, 'default', 'owner')"),
            {"id": str(uuid.uuid4()), "gid": gid})
        await session.commit()
    return {"id": gid, "name": name}


@router.post("/reading-groups/{group_id}/schedule", summary="Schedule a reading session")
async def schedule_reading(group_id: str, document_id: str, scheduled_date: str = None,
                            notes: str = "", db=Depends(get_db)):
    """Schedule a paper for discussion in a reading group (journal club)."""
    await ensure_tables(db)
    sid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO reading_group_sessions (id, group_id, document_id, scheduled_date, notes, created_by) "
            "VALUES (:id, :gid, :did, :sd, :n, 'default')"),
            {"id": sid, "gid": group_id, "did": document_id, "sd": scheduled_date, "n": notes})
        await session.commit()

    doc = await db.get_document(document_id)
    return {
        "id": sid,
        "document_title": doc.title if doc else "Unknown",
        "scheduled_date": scheduled_date,
        "message": "Reading session scheduled",
    }


@router.get("/reading-groups/{group_id}/sessions", summary="List reading group sessions")
async def list_sessions(group_id: str, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT rgs.*, d.title, d.authors FROM reading_group_sessions rgs "
            "LEFT JOIN documents d ON rgs.document_id = d.id WHERE rgs.group_id = :gid ORDER BY rgs.scheduled_date DESC"),
            {"gid": group_id})).fetchall()
        return [{
            "id": r[0], "document_id": r[2], "scheduled_date": r[3],
            "notes": r[4], "document_title": r[6] or "Unknown",
            "authors": json.loads(r[7]) if isinstance(r[7], str) else (r[7] or []),
        } for r in rows]
