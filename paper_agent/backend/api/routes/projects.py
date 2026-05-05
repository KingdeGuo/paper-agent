"""Research projects: organize papers into projects with deadlines and notes."""

import json
import logging
import uuid
from datetime import datetime

from backend.services.registry import get_db
from fastapi import APIRouter, Depends
from sqlalchemy import text as sa_text

logger = logging.getLogger(__name__)
router = APIRouter()


async def ensure_tables(db):
    async with db.async_session_maker() as session:
        for ddl in [
            """CREATE TABLE IF NOT EXISTS research_projects (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL DEFAULT 'default',
                title TEXT NOT NULL, description TEXT, status TEXT DEFAULT 'active',
                deadline TEXT, priority TEXT DEFAULT 'medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS project_papers (
                id TEXT PRIMARY KEY, project_id TEXT NOT NULL, document_id TEXT NOT NULL,
                notes TEXT, status TEXT DEFAULT 'to_read', added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS project_milestones (
                id TEXT PRIMARY KEY, project_id TEXT NOT NULL, title TEXT NOT NULL,
                is_completed INTEGER DEFAULT 0, due_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
        ]:
            await session.execute(sa_text(ddl))
        await session.commit()


# ─── Projects ──────────────────────────────────────────────

@router.post("/projects", summary="Create a research project")
async def create_project(title: str, description: str = "", deadline: str = None, priority: str = "medium", db=Depends(get_db)):
    await ensure_tables(db)
    pid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO research_projects (id, user_id, title, description, deadline, priority) VALUES (:id, 'default', :t, :d, :dl, :p)"),
            {"id": pid, "t": title, "d": description, "dl": deadline, "p": priority})
        await session.commit()
    return {"id": pid, "title": title}


@router.get("/projects", summary="List research projects")
async def list_projects(status: str = None, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        sql = "SELECT p.*, (SELECT COUNT(*) FROM project_papers WHERE project_id = p.id) as paper_count FROM research_projects p WHERE p.user_id = 'default'"
        params = {}
        :
            if status:
            sql += " AND p.status = :s"
            params["s"] = status
        sql += " ORDER BY p.updated_at DESC"
        rows = (await session.execute(sa_text(sql), params)).fetchall()
        return [{"id": r[0], "title": r[2], "description": r[3], "status": r[4],
                 "deadline": str(r[5]) if r[5] else None, "priority": r[6],
                 "paper_count": r[9] or 0, "created_at": str(r[7])} for r in rows]


@router.put("/projects/{project_id}", summary="Update project")
async def update_project(project_id: str, title: str = None, description: str = None,
                         status: str = None, deadline: str = None, priority: str = None, db=Depends(get_db)):
    await ensure_tables(db)
    sets = []
    params = {"id": project_id}
    :
        if title:
    :
        if description is not None:
    :
        if status:
    :
        if deadline is not None:
    :
        if priority:
    sets.append("updated_at = :n"); params["n"] = datetime.utcnow().isoformat()
    async with db.async_session_maker() as session:
        await session.execute(sa_text(f"UPDATE research_projects SET {', '.join(sets)} WHERE id = :id"), params)
        await session.commit()
    return {"message": "Updated"}


@router.delete("/projects/{project_id}", summary="Delete project")
async def delete_project(project_id: str, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        await session.execute(sa_text("DELETE FROM project_milestones WHERE project_id = :id"), {"id": project_id})
        await session.execute(sa_text("DELETE FROM project_papers WHERE project_id = :id"), {"id": project_id})
        await session.execute(sa_text("DELETE FROM research_projects WHERE id = :id"), {"id": project_id})
        await session.commit()
    return {"message": "Deleted"}


# ─── Project Papers ────────────────────────────────────────

@router.post("/projects/{project_id}/papers", summary="Add paper to project")
async def add_paper_to_project(project_id: str, document_id: str, notes: str = "", db=Depends(get_db)):
    await ensure_tables(db)
    pid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO project_papers (id, project_id, document_id, notes) VALUES (:id, :pid, :did, :n)"),
            {"id": pid, "pid": project_id, "did": document_id, "n": notes})
        await session.commit()
    return {"id": pid, "document_id": document_id}


@router.get("/projects/{project_id}/papers", summary="Get project papers")
async def get_project_papers(project_id: str, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT pp.*, d.title, d.authors, d.year FROM project_papers pp "
            "LEFT JOIN documents d ON pp.document_id = d.id WHERE pp.project_id = :pid ORDER BY pp.added_at DESC"),
            {"pid": project_id})).fetchall()
        return [{"id": r[0], "project_id": r[1], "document_id": r[2], "notes": r[3] or "",
                 "status": r[4] or "to_read", "title": r[6] or "Untitled",
                 "authors": json.loads(r[7]) if isinstance(r[7], str) else (r[7] or []),
                 "year": r[8]} for r in rows]


# ─── Milestones ────────────────────────────────────────────

@router.post("/projects/{project_id}/milestones", summary="Add milestone")
async def add_milestone(project_id: str, title: str, due_date: str = None, db=Depends(get_db)):
    await ensure_tables(db)
    mid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        await session.execute(sa_text(
            "INSERT INTO project_milestones (id, project_id, title, due_date) VALUES (:id, :pid, :t, :dd)"),
            {"id": mid, "pid": project_id, "t": title, "dd": due_date})
        await session.commit()
    return {"id": mid, "title": title}


@router.get("/projects/{project_id}/milestones", summary="Get project milestones")
async def get_milestones(project_id: str, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT * FROM project_milestones WHERE project_id = :pid ORDER BY created_at"),
            {"pid": project_id})).fetchall()
        return [{"id": r[0], "title": r[2], "is_completed": bool(r[3]), "due_date": str(r[4]) if r[4] else None,
                 "created_at": str(r[5])} for r in rows]


@router.put("/milestones/{milestone_id}", summary="Toggle milestone completion")
async def toggle_milestone(milestone_id: str, is_completed: bool = True, db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        await session.execute(sa_text("UPDATE project_milestones SET is_completed = :c WHERE id = :id"),
                              {"c": int(is_completed), "id": milestone_id})
        await session.commit()
    return {"message": "Updated"}
