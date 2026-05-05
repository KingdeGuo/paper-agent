"""
Workspace service — deep team research collaboration.

Complete workspace management with:
- Team CRUD with invitation system
- Role-based access control (owner/admin/member/viewer)
- Shared document libraries with granular permissions
- Collaborative annotations and discussions
- Team activity streams
- Team reading goals and progress tracking
- Automated team digests
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from backend.services.cluster_database import ClusterDatabaseService
from sqlalchemy import text as sa_text

logger = logging.getLogger(__name__)

# ─── Data Models ─────────────────────────────────────────────

WORKSPACE_ROLES = ["owner", "admin", "member", "viewer"]
DOCUMENT_PERMISSIONS = ["view", "annotate", "edit", "admin"]
INVITE_STATUSES = ["pending", "accepted", "declined", "expired"]

# ─── Workspace Service ───────────────────────────────────────

class WorkspaceService:
    """Complete workspace management for team research collaboration."""

    def __init__(self, db: ClusterDatabaseService):
        self.db = db

    async def ensure_tables(self):
        async with self.db.async_session_maker() as session:
            for ddl in [
                """CREATE TABLE IF NOT EXISTS workspaces (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT DEFAULT '',
                    avatar_url TEXT, owner_id TEXT NOT NULL,
                    is_public INTEGER DEFAULT 0, invite_code TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted INTEGER DEFAULT 0
                )""",
                """CREATE TABLE IF NOT EXISTS workspace_members (
                    id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL,
                    user_id TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'member',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    invited_by TEXT, UNIQUE(workspace_id, user_id)
                )""",
                """CREATE TABLE IF NOT EXISTS workspace_invitations (
                    id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL,
                    email TEXT, user_id TEXT, role TEXT DEFAULT 'member',
                    status TEXT DEFAULT 'pending', invite_code TEXT UNIQUE,
                    invited_by TEXT, expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""",
                """CREATE TABLE IF NOT EXISTS workspace_documents (
                    id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL,
                    document_id TEXT NOT NULL, added_by TEXT,
                    permission TEXT DEFAULT 'view',
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted INTEGER DEFAULT 0
                )""",
                """CREATE TABLE IF NOT EXISTS workspace_annotations (
                    id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL,
                    document_id TEXT NOT NULL, user_id TEXT NOT NULL,
                    content TEXT NOT NULL, annotation_type TEXT DEFAULT 'comment',
                    page_number INTEGER, parent_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted INTEGER DEFAULT 0
                )""",
                """CREATE TABLE IF NOT EXISTS workspace_goals (
                    id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL,
                    title TEXT NOT NULL, target_papers INTEGER DEFAULT 5,
                    period TEXT DEFAULT 'weekly', progress INTEGER DEFAULT 0,
                    created_by TEXT, start_date TIMESTAMP, end_date TIMESTAMP,
                    is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""",
                """CREATE TABLE IF NOT EXISTS workspace_activity (
                    id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL,
                    user_id TEXT, activity_type TEXT NOT NULL,
                    description TEXT, document_id TEXT,
                    metadata TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""",
                """CREATE TABLE IF NOT EXISTS workspace_labels (
                    id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL,
                    name TEXT NOT NULL, color TEXT DEFAULT '#2563eb',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""",
                """CREATE TABLE IF NOT EXISTS workspace_document_labels (
                    id TEXT PRIMARY KEY, workspace_document_id TEXT NOT NULL,
                    label_id TEXT NOT NULL
                )""",
                """CREATE TABLE IF NOT EXISTS workspace_reading_sessions (
                    id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL,
                    user_id TEXT NOT NULL, document_id TEXT,
                    duration_minutes INTEGER DEFAULT 0,
                    date TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""",
            ]:
                try:
                    await session.execute(sa_text(ddl))
                except Exception as e:
                    logger.debug(f"DDL note (likely already exists): {e}")
            await session.commit()

    # ─── Workspace CRUD ────────────────────────────────────────

    async def create_workspace(self, name: str, owner_id: str, description: str = "") -> Dict[str, Any]:
        await self.ensure_tables()
        wid = str(uuid.uuid4())
        invite_code = str(uuid.uuid4())[:12]
        async with self.db.async_session_maker() as session:
            await session.execute(sa_text(
                "INSERT INTO workspaces (id, name, description, owner_id, invite_code) VALUES (:id, :n, :d, :o, :ic)"),
                {"id": wid, "n": name, "d": description, "o": owner_id, "ic": invite_code})
            await session.execute(sa_text(
                "INSERT INTO workspace_members (id, workspace_id, user_id, role) VALUES (:id, :wid, :uid, 'owner')"),
                {"id": str(uuid.uuid4()), "wid": wid, "uid": owner_id})
            await self._log_activity(session, wid, owner_id, "workspace_created", f"Created workspace '{name}'")
            await session.commit()
        return {"id": wid, "name": name, "invite_code": invite_code, "role": "owner"}

    async def get_workspace(self, workspace_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        await self.ensure_tables()
        async with self.db.async_session_maker() as session:
            ws = (await session.execute(sa_text(
                "SELECT * FROM workspaces WHERE id = :id AND is_deleted = 0"), {"id": workspace_id})).fetchone()
            if not ws:
                return None
            membership = (await session.execute(sa_text(
                "SELECT role FROM workspace_members WHERE workspace_id = :wid AND user_id = :uid"),
                {"wid": workspace_id, "uid": user_id})).fetchone()
            member_count = (await session.execute(sa_text(
                "SELECT COUNT(*) FROM workspace_members WHERE workspace_id = :wid"), {"wid": workspace_id})).scalar()
            doc_count = (await session.execute(sa_text(
                "SELECT COUNT(*) FROM workspace_documents WHERE workspace_id = :wid AND is_deleted = 0"),
                {"wid": workspace_id})).scalar()

            return {
                "id": ws[0], "name": ws[1], "description": ws[2],
                "owner_id": ws[4], "invite_code": ws[6],
                "created_at": str(ws[7]) if ws[7] else None,
                "role": membership[0] if membership else None,
                "member_count": member_count or 0,
                "document_count": doc_count or 0,
            }

    async def list_user_workspaces(self, user_id: str) -> List[Dict[str, Any]]:
        await self.ensure_tables()
        async with self.db.async_session_maker() as session:
            rows = (await session.execute(sa_text("""
                SELECT w.*, wm.role,
                    (SELECT COUNT(*) FROM workspace_members WHERE workspace_id = w.id) as member_count,
                    (SELECT COUNT(*) FROM workspace_documents WHERE workspace_id = w.id AND is_deleted = 0) as doc_count
                FROM workspaces w JOIN workspace_members wm ON w.id = wm.workspace_id
                WHERE wm.user_id = :uid AND w.is_deleted = 0 ORDER BY w.updated_at DESC"""),
                {"uid": user_id})).fetchall()
            return [{
                "id": r[0], "name": r[1], "description": r[2],
                "owner_id": r[4], "invite_code": r[6],
                "role": r[9], "member_count": r[10] or 0, "document_count": r[11] or 0,
                "created_at": str(r[7]) if r[7] else None,
            } for r in rows]

    async def update_workspace(self, workspace_id: str, user_id: str, **kwargs) -> Dict[str, Any]:
        await self.ensure_tables()
        allowed = ["name", "description", "is_public"]
        sets = []
        params = {"id": workspace_id}
        for k, v in kwargs.items():
            if k in allowed:
                sets.append(f"{k} = :{k}")
                params[k] = v
        if not sets:
            return {"message": "No changes"}
        sets.append("updated_at = :n")
        params["n"] = datetime.utcnow().isoformat()
        async with self.db.async_session_maker() as session:
            await session.execute(sa_text(f"UPDATE workspaces SET {', '.join(sets)} WHERE id = :id"), params)
            await self._log_activity(session, workspace_id, user_id, "workspace_updated", "Updated workspace settings")
            await session.commit()
        return {"message": "Updated"}

    async def delete_workspace(self, workspace_id: str, user_id: str) -> bool:
        await self.ensure_tables()
        async with self.db.async_session_maker() as session:
            ws = (await session.execute(sa_text("SELECT owner_id FROM workspaces WHERE id = :id"), {"id": workspace_id})).fetchone()
            if not ws or ws[0] != user_id:
                return False
            await session.execute(sa_text("UPDATE workspaces SET is_deleted = 1, updated_at = :n WHERE id = :id"),
                                  {"n": datetime.utcnow().isoformat(), "id": workspace_id})
            await self._log_activity(session, workspace_id, user_id, "workspace_deleted", "Deleted workspace")
            await session.commit()
        return True

    # ─── Membership ───────────────────────────────────────────

    async def invite_member(self, workspace_id: str, invited_by: str,
                            email: str = None, user_id: str = None, role: str = "member") -> Dict[str, Any]:
        await self.ensure_tables()
        inv_id = str(uuid.uuid4())
        invite_code = str(uuid.uuid4())[:12]
        expires = (datetime.utcnow() + timedelta(days=7)).isoformat()
        async with self.db.async_session_maker() as session:
            if user_id:
                existing = (await session.execute(sa_text(
                    "SELECT id FROM workspace_members WHERE workspace_id = :wid AND user_id = :uid"),
                    {"wid": workspace_id, "uid": user_id})).fetchone()
                if existing:
                    return {"message": "User is already a member"}

            await session.execute(sa_text(
                "INSERT INTO workspace_invitations (id, workspace_id, email, user_id, role, invite_code, invited_by, expires_at) "
                "VALUES (:id, :wid, :e, :uid, :r, :ic, :ib, :ex)"),
                {"id": inv_id, "wid": workspace_id, "e": email, "uid": user_id,
                 "r": role, "ic": invite_code, "ib": invited_by, "ex": expires})
            await session.commit()
        return {"invitation_id": inv_id, "invite_code": invite_code, "expires_at": expires}

    async def accept_invitation(self, invite_code: str, user_id: str) -> Dict[str, Any]:
        await self.ensure_tables()
        async with self.db.async_session_maker() as session:
            inv = (await session.execute(sa_text(
                "SELECT id, workspace_id, role, expires_at FROM workspace_invitations WHERE invite_code = :ic AND status = 'pending'"),
                {"ic": invite_code})).fetchone()
            if not inv:
                return {"error": "Invalid or expired invitation"}
            if inv[3] and inv[3] < datetime.utcnow().isoformat():
                await session.execute(sa_text("UPDATE workspace_invitations SET status = 'expired' WHERE id = :id"), {"id": inv[0]})
                await session.commit()
                return {"error": "Invitation has expired"}

            await session.execute(sa_text(
                "INSERT INTO workspace_members (id, workspace_id, user_id, role) VALUES (:id, :wid, :uid, :r)"),
                {"id": str(uuid.uuid4()), "wid": inv[1], "uid": user_id, "r": inv[2]})
            await session.execute(sa_text("UPDATE workspace_invitations SET status = 'accepted' WHERE id = :id"), {"id": inv[0]})
            await self._log_activity(session, inv[1], user_id, "member_joined", "Joined workspace")
            await session.commit()

            ws = await self.get_workspace(inv[1], user_id)
            return {"message": "Accepted", "workspace": ws}

    async def update_member_role(self, workspace_id: str, target_user_id: str, new_role: str, actor_id: str) -> bool:
        await self.ensure_tables()
        if new_role not in WORKSPACE_ROLES:
            return False
        async with self.db.async_session_maker() as session:
            actor = (await session.execute(sa_text(
                "SELECT role FROM workspace_members WHERE workspace_id = :wid AND user_id = :uid"),
                {"wid": workspace_id, "uid": actor_id})).fetchone()
            if not actor or actor[0] not in ("owner", "admin"):
                return False
            await session.execute(sa_text("UPDATE workspace_members SET role = :r WHERE workspace_id = :wid AND user_id = :uid"),
                                  {"r": new_role, "wid": workspace_id, "uid": target_user_id})
            await self._log_activity(session, workspace_id, actor_id, "role_changed", f"Changed member role to {new_role}")
            await session.commit()
        return True

    async def remove_member(self, workspace_id: str, target_user_id: str, actor_id: str) -> bool:
        await self.ensure_tables()
        async with self.db.async_session_maker() as session:
            actor = (await session.execute(sa_text(
                "SELECT role FROM workspace_members WHERE workspace_id = :wid AND user_id = :uid"),
                {"wid": workspace_id, "uid": actor_id})).fetchone()
            if not actor or actor[0] not in ("owner", "admin"):
                return False
            await session.execute(sa_text("DELETE FROM workspace_members WHERE workspace_id = :wid AND user_id = :uid"),
                                  {"wid": workspace_id, "uid": target_user_id})
            await self._log_activity(session, workspace_id, actor_id, "member_removed", "Removed member from workspace")
            await session.commit()
        return True

    async def list_members(self, workspace_id: str) -> List[Dict[str, Any]]:
        await self.ensure_tables()
        async with self.db.async_session_maker() as session:
            rows = (await session.execute(sa_text(
                "SELECT * FROM workspace_members WHERE workspace_id = :wid ORDER BY joined_at ASC"),
                {"wid": workspace_id})).fetchall()
            return [{"id": r[0], "user_id": r[2], "role": r[3], "joined_at": str(r[4]) if r[4] else None} for r in rows]

    # ─── Shared Documents ──────────────────────────────────────

    async def add_document(self, workspace_id: str, document_id: str, added_by: str,
                           permission: str = "view") -> Dict[str, Any]:
        await self.ensure_tables()
        did = str(uuid.uuid4())
        async with self.db.async_session_maker() as session:
            await session.execute(sa_text(
                "INSERT INTO workspace_documents (id, workspace_id, document_id, added_by, permission) VALUES (:id, :wid, :did, :ab, :perm)"),
                {"id": did, "wid": workspace_id, "did": document_id, "ab": added_by, "perm": permission})
            await self._log_activity(session, workspace_id, added_by, "document_added", "Added document to workspace",
                                     document_id=document_id)
            await session.commit()
        return {"id": did, "document_id": document_id, "permission": permission}

    async def list_documents(self, workspace_id: str, user_id: str) -> List[Dict[str, Any]]:
        await self.ensure_tables()
        async with self.db.async_session_maker() as session:
            rows = (await session.execute(sa_text("""
                SELECT wd.*, d.title, d.authors, d.year, d.abstract, d.processed, d.summary
                FROM workspace_documents wd
                LEFT JOIN documents d ON wd.document_id = d.id
                WHERE wd.workspace_id = :wid AND wd.is_deleted = 0
                ORDER BY wd.added_at DESC"""), {"wid": workspace_id})).fetchall()
            return [{
                "id": r[0], "document_id": r[2], "added_by": r[3], "permission": r[4],
                "title": r[6] or "Untitled", "authors": json.loads(r[7]) if isinstance(r[7], str) else (r[7] or []),
                "year": r[8], "abstract": (r[9] or "")[:300], "processed": r[10], "summary": r[11],
                "added_at": str(r[5]) if r[5] else None,
            } for r in rows]

    # ─── Collaborative Annotations ────────────────────────────

    async def add_annotation(self, workspace_id: str, document_id: str, user_id: str,
                             content: str, annotation_type: str = "comment",
                             page_number: int = None, parent_id: str = None) -> Dict[str, Any]:
        await self.ensure_tables()
        aid = str(uuid.uuid4())
        async with self.db.async_session_maker() as session:
            await session.execute(sa_text(
                "INSERT INTO workspace_annotations (id, workspace_id, document_id, user_id, content, annotation_type, page_number, parent_id) "
                "VALUES (:id, :wid, :did, :uid, :c, :at, :pn, :pid)"),
                {"id": aid, "wid": workspace_id, "did": document_id, "uid": user_id,
                 "c": content, "at": annotation_type, "pn": page_number, "pid": parent_id})
            await self._log_activity(session, workspace_id, user_id, "annotation_added", "Added annotation", document_id=document_id)
            await session.commit()
        return {"id": aid, "message": "Annotation added"}

    async def list_annotations(self, workspace_id: str, document_id: str = None) -> List[Dict[str, Any]]:
        await self.ensure_tables()
        async with self.db.async_session_maker() as session:
            sql = "SELECT * FROM workspace_annotations WHERE workspace_id = :wid AND is_deleted = 0"
            params = {"wid": workspace_id}
            if document_id:
                sql += " AND document_id = :did"
                params["did"] = document_id
            sql += " ORDER BY created_at DESC"
            rows = (await session.execute(sa_text(sql), params)).fetchall()
            return [{"id": r[0], "document_id": r[2], "user_id": r[3], "content": r[4],
                     "type": r[5], "page_number": r[6], "parent_id": r[7],
                     "created_at": str(r[8]) if r[8] else None} for r in rows]

    # ─── Team Reading Goals ────────────────────────────────────

    async def create_goal(self, workspace_id: str, title: str, target_papers: int = 5,
                          period: str = "weekly", created_by: str = None) -> Dict[str, Any]:
        await self.ensure_tables()
        gid = str(uuid.uuid4())
        now = datetime.utcnow()
        end = (now + timedelta(days=7 if period == "weekly" else 30)).isoformat()
        async with self.db.async_session_maker() as session:
            await session.execute(sa_text(
                "INSERT INTO workspace_goals (id, workspace_id, title, target_papers, period, created_by, start_date, end_date) "
                "VALUES (:id, :wid, :t, :tp, :p, :cb, :sd, :ed)"),
                {"id": gid, "wid": workspace_id, "t": title, "tp": target_papers,
                 "p": period, "cb": created_by, "sd": now.isoformat(), "ed": end})
            await session.commit()
        return {"id": gid, "title": title, "target": target_papers, "period": period}

    async def list_goals(self, workspace_id: str) -> List[Dict[str, Any]]:
        await self.ensure_tables()
        async with self.db.async_session_maker() as session:
            rows = (await session.execute(sa_text(
                "SELECT * FROM workspace_goals WHERE workspace_id = :wid AND is_active = 1 ORDER BY created_at DESC"),
                {"wid": workspace_id})).fetchall()
            return [{"id": r[0], "title": r[2], "target": r[3], "period": r[4],
                     "progress": r[5] or 0, "percent": round(((r[5] or 0) / max(r[3], 1)) * 100, 1),
                     "start_date": str(r[7]) if r[7] else None, "end_date": str(r[8]) if r[8] else None} for r in rows]

    # ─── Activity ──────────────────────────────────────────────

    async def list_activity(self, workspace_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        await self.ensure_tables()
        async with self.db.async_session_maker() as session:
            rows = (await session.execute(sa_text(
                "SELECT * FROM workspace_activity WHERE workspace_id = :wid ORDER BY created_at DESC LIMIT :lim"),
                {"wid": workspace_id, "lim": limit})).fetchall()
            return [{"id": r[0], "user_id": r[2], "type": r[3], "description": r[4],
                     "document_id": r[5], "created_at": str(r[7]) if r[7] else None} for r in rows]

    async def _log_activity(self, session, workspace_id: str, user_id: str,
                            activity_type: str, description: str, document_id: str = None):
        await session.execute(sa_text(
            "INSERT INTO workspace_activity (id, workspace_id, user_id, activity_type, description, document_id) "
            "VALUES (:id, :wid, :uid, :at, :d, :did)"),
            {"id": str(uuid.uuid4()), "wid": workspace_id, "uid": user_id or "system",
             "at": activity_type, "d": description, "did": document_id})

    # ─── Labels ────────────────────────────────────────────────

    async def create_label(self, workspace_id: str, name: str, color: str = "#2563eb") -> Dict[str, Any]:
        await self.ensure_tables()
        lid = str(uuid.uuid4())
        async with self.db.async_session_maker() as session:
            await session.execute(sa_text(
                "INSERT INTO workspace_labels (id, workspace_id, name, color) VALUES (:id, :wid, :n, :c)"),
                {"id": lid, "wid": workspace_id, "n": name, "c": color})
            await session.commit()
        return {"id": lid, "name": name, "color": color}

    async def list_labels(self, workspace_id: str) -> List[Dict[str, Any]]:
        await self.ensure_tables()
        async with self.db.async_session_maker() as session:
            rows = (await session.execute(sa_text(
                "SELECT * FROM workspace_labels WHERE workspace_id = :wid ORDER BY name"),
                {"wid": workspace_id})).fetchall()
            return [{"id": r[0], "name": r[2], "color": r[3]} for r in rows]

    # ─── Team Digest ────────────────────────────────────────────

    async def generate_team_digest(self, workspace_id: str, days: int = 7) -> Dict[str, Any]:
        """Generate a team research digest for the workspace."""
        await self.ensure_tables()
        async with self.db.async_session_maker() as session:
            # Get recent activity
            activity = (await session.execute(sa_text(
                "SELECT * FROM workspace_activity WHERE workspace_id = :wid AND created_at >= :since ORDER BY created_at DESC LIMIT 20"),
                {"wid": workspace_id, "since": (datetime.utcnow() - timedelta(days=days)).isoformat()})).fetchall()

            # Get member stats
            member_count = (await session.execute(sa_text(
                "SELECT COUNT(*) FROM workspace_members WHERE workspace_id = :wid"), {"wid": workspace_id})).scalar()

            # Get reading progress
            goals = await self.list_goals(workspace_id)

            digest = {
                "workspace_id": workspace_id,
                "period_days": days,
                "member_count": member_count or 0,
                "activity_count": len(activity),
                "recent_activity": [{
                    "type": r[3], "description": r[4],
                    "created_at": str(r[7]) if r[7] else None,
                } for r in activity[:10]],
                "goals": goals[:3],
                "summary": f"{len(activity)} activities in the last {days} days across {member_count} members.",
            }

            return digest

    # ─── Research Agenda ───────────────────────────────────────

    async def create_research_agenda(self, workspace_id: str, title: str, description: str = "",
                                     phase: str = "exploration", created_by: str = None) -> Dict[str, Any]:
        """Create a research agenda item for strategic planning."""
        await self.ensure_tables()
        aid = str(uuid.uuid4())
        async with self.db.async_session_maker() as session:
            await session.execute(sa_text(
                "INSERT INTO workspace_goals (id, workspace_id, title, target_papers, period, created_by) "
                "VALUES (:id, :wid, :t, 0, :p, :cb)"),
                {"id": aid, "wid": workspace_id, "t": title, "p": f"agenda_{phase}", "cb": created_by})
            await session.commit()
        return {"id": aid, "title": title, "phase": phase}
