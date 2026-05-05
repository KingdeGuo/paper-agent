"""Persistent Research Chat — context-aware paper Q&A across sessions."""

import json
import logging
import uuid
from datetime import datetime
from typing import List

from backend.services.registry import get_db, get_llm_service, get_vector_service
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text as sa_text

logger = logging.getLogger(__name__)
router = APIRouter()


async def ensure_tables(db):
    async with db.async_session_maker() as session:
        for ddl in [
            """CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY, user_id TEXT DEFAULT 'default',
                title TEXT, context_papers TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted INTEGER DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS chat_messages (
                id TEXT PRIMARY KEY, session_id TEXT NOT NULL,
                role TEXT NOT NULL, content TEXT NOT NULL,
                sources TEXT DEFAULT '[]', tokens INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
        ]:
            try: await session.execute(sa_text(ddl))
            except Exception: pass
        await session.commit()


@router.post("/chat/sessions", summary="Create a chat session")
async def create_chat_session(title: str = "Research Chat", context_papers: List[str] = None, db=Depends(get_db)):
    """Create a new research chat session, optionally with context papers."""
    await ensure_tables(db)
    sid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO chat_sessions (id, user_id, title, context_papers) VALUES (:id, 'default', :t, :cp)"),
            {"id": sid, "t": title, "cp": json.dumps(context_papers or [])})
        await session.commit()
    return {"id": sid, "title": title}


@router.get("/chat/sessions", summary="List chat sessions")
async def list_chat_sessions(db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT cs.*, (SELECT COUNT(*) FROM chat_messages WHERE session_id = cs.id) as msg_count "
            "FROM chat_sessions cs WHERE cs.user_id = 'default' AND cs.is_deleted = 0 ORDER BY cs.updated_at DESC"))).fetchall()
        return [{"id": r[0], "title": r[2], "context_papers": json.loads(r[3]) if isinstance(r[3], str) else (r[3] or []),
                 "message_count": r[7] or 0, "created_at": str(r[4]) if r[4] else None} for r in rows]


@router.post("/chat/sessions/{session_id}/ask", summary="Ask a question in chat session")
async def ask_in_session(session_id: str, question: str,
                          search_library: bool = True,
                          db=Depends(get_db),
                          llm_service=Depends(get_llm_service),
                          vector_service=Depends(get_vector_service)):
    """Ask a question with full conversation history and library context."""
    await ensure_tables(db)

    # Get session context
    async with db.async_session_maker() as session:
        sess = (await session.execute(sa_text(
            "SELECT * FROM chat_sessions WHERE id = :id AND is_deleted = 0"),
            {"id": session_id})).fetchone()
        if not sess:
            raise HTTPException(status_code=404, detail="Session not found")

        context_paper_ids = json.loads(sess[3]) if isinstance(sess[3], str) else (sess[3] or [])

        # Get conversation history (last 10 messages)
        history = (await session.execute(sa_text(
            "SELECT role, content FROM chat_messages WHERE session_id = :sid ORDER BY created_at ASC LIMIT 10"),
            {"sid": session_id})).fetchall()

    # Gather context from library
    context_text = ""
    sources = []

    if search_library and vector_service:
        results = vector_service.search_similar(question, limit=5)
        for r in results:
            did = r.get("document_id", "")
            doc = await db.get_document(did) if did else None
            if doc:
                context_text += f"\n[From: {doc.title or doc.filename}]\n{r.get('text', '')[:500]}\n"
                sources.append({"document_id": did, "title": doc.title or doc.filename, "score": r.get("score", 0)})

    # Also include context from explicitly linked papers
    for pid in context_paper_ids:
        doc = await db.get_document(pid)
        if doc:
            context_text += f"\n[Context Paper: {doc.title}]\n{(doc.abstract or '')[:500]}\n"
            if not any(s.get("document_id") == pid for s in sources):
                sources.append({"document_id": pid, "title": doc.title or doc.filename, "score": 1.0})

    # Build conversation
    system = "You are a research assistant. Answer based on the provided paper context and conversation history. Cite sources using [Paper Title]. Be precise and concise."
    messages = [{"role": "system", "content": system}]

    if context_text:
        messages.append({"role": "system", "content": f"Relevant papers:\n{context_text[:3000]}"})

    for h in history[-10:]:
        messages.append({"role": h[0], "content": h[1]})

    messages.append({"role": "user", "content": question})

    # Get AI response
    try:
        resp = await llm_service.chat_completion(messages=messages[1:], system_prompt=system)  # system is separate
        answer = resp.get("content", "") if isinstance(resp, dict) else str(resp)
    except Exception as e:
        answer = f"AI response unavailable: {e}"

    # Save question and answer
    msg_id_q = str(uuid.uuid4())
    msg_id_a = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO chat_messages (id, session_id, role, content, sources) VALUES (:id, :sid, 'user', :c, '[]')"),
            {"id": msg_id_q, "sid": session_id, "c": question})
        await session.execute(sa_text(
            "INSERT INTO chat_messages (id, session_id, role, content, sources) VALUES (:id, :sid, 'assistant', :c, :s)"),
            {"id": msg_id_a, "sid": session_id, "c": answer, "s": json.dumps(sources)})
        await session.execute(sa_text("UPDATE chat_sessions SET updated_at = :n WHERE id = :id"),
                              {"n": datetime.utcnow().isoformat(), "id": session_id})
        await session.commit()

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "message_count": len(history) + 2,
    }


@router.get("/chat/sessions/{session_id}/messages", summary="Get chat history")
async def get_chat_history(session_id: str, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT * FROM chat_messages WHERE session_id = :sid ORDER BY created_at ASC"),
            {"sid": session_id})).fetchall()
        return [{"id": r[0], "role": r[2], "content": r[3],
                 "sources": json.loads(r[4]) if isinstance(r[4], str) else (r[4] or []),
                 "created_at": str(r[6]) if r[6] else None} for r in rows]


@router.put("/chat/sessions/{session_id}/title", summary="Update session title")
async def update_session_title(session_id: str, title: str, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        await session.execute(sa_text("UPDATE chat_sessions SET title = :t, updated_at = :n WHERE id = :id"),
                              {"t": title, "n": datetime.utcnow().isoformat(), "id": session_id})
        await session.commit()
    return {"message": "Title updated"}


@router.delete("/chat/sessions/{session_id}", summary="Delete chat session")
async def delete_chat_session(session_id: str, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        await session.execute(sa_text("UPDATE chat_sessions SET is_deleted = 1 WHERE id = :id"), {"id": session_id})
        await session.commit()
    return {"message": "Session deleted"}
