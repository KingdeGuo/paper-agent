"""Literature Directory Tree — hierarchical taxonomy organizing papers by topic, methodology, field."""

import json
import logging
import uuid

from backend.services.registry import get_db, get_llm_service
from fastapi import APIRouter, Depends
from sqlalchemy import text as sa_text

logger = logging.getLogger(__name__)
router = APIRouter()


async def ensure_tables(db):
    async with db.async_session_maker() as session:
        for ddl in [
            """CREATE TABLE IF NOT EXISTS directory_nodes (
                id TEXT PRIMARY KEY, parent_id TEXT,
                user_id TEXT DEFAULT 'default',
                name TEXT NOT NULL, node_type TEXT DEFAULT 'folder',
                description TEXT, icon TEXT, sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted INTEGER DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS directory_papers (
                id TEXT PRIMARY KEY, node_id TEXT NOT NULL,
                document_id TEXT NOT NULL, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS directory_views (
                id TEXT PRIMARY KEY, user_id TEXT DEFAULT 'default',
                name TEXT NOT NULL, root_node_id TEXT,
                is_default INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS auto_classification_rules (
                id TEXT PRIMARY KEY, user_id TEXT DEFAULT 'default',
                keyword TEXT NOT NULL, target_node_id TEXT NOT NULL,
                match_type TEXT DEFAULT 'contains', is_active INTEGER DEFAULT 1
            )""",
        ]:
            try: await session.execute(sa_text(ddl))
            except Exception: pass
        await session.commit()


# ─── Taxonomy Trees ─────────────────────────────────────────

@router.post("/directory/nodes", summary="Create a directory node")
async def create_node(name: str, parent_id: str = None, node_type: str = "folder",
                       description: str = "", icon: str = "📁", db=Depends(get_db)):
    """Create a node in the literature directory tree."""
    await ensure_tables(db)
    nid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        # Get sort order
        max_order = (await session.execute(sa_text(
            "SELECT MAX(sort_order) FROM directory_nodes WHERE parent_id IS :pid AND user_id = 'default' AND is_deleted = 0"),
            {"pid": parent_id})).scalar() or 0
        await session.execute(sa_text(
            "INSERT INTO directory_nodes (id, parent_id, user_id, name, node_type, description, icon, sort_order) "
            "VALUES (:id, :pid, 'default', :n, :nt, :d, :ic, :so)"),
            {"id": nid, "pid": parent_id, "n": name, "nt": node_type,
             "d": description, "ic": icon, "so": max_order + 1})
        await session.commit()
    return {"id": nid, "name": name, "type": node_type}


@router.get("/directory/tree", summary="Get full directory tree")
async def get_directory_tree(root_id: str = None, db=Depends(get_db)):
    """Get the complete literature directory tree structure."""
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        # Get all nodes
        sql = "SELECT * FROM directory_nodes WHERE user_id = 'default' AND is_deleted = 0 ORDER BY sort_order ASC"
        params = {}
        if root_id:
            sql += " AND (id = :rid OR parent_id = :rid2)"
            params["rid"] = root_id
            params["rid2"] = root_id
        nodes = (await session.execute(sa_text(sql), params)).fetchall()

        # Get paper counts per node
        paper_counts = {}
        for n in nodes:
            cnt = (await session.execute(sa_text(
                "SELECT COUNT(*) FROM directory_papers WHERE node_id = :nid"),
                {"nid": n[0]})).scalar() or 0
            paper_counts[n[0]] = cnt

        # Build tree
        node_map = {}
        for n in nodes:
            node_map[n[0]] = {
                "id": n[0], "parent_id": n[1], "name": n[3],
                "node_type": n[4], "description": n[5] or "", "icon": n[6] or "📁",
                "sort_order": n[7] or 0, "paper_count": paper_counts.get(n[0], 0),
                "children": [],
            }

        tree = []
        for nid, nd in node_map.items():
            if nd["parent_id"] and nd["parent_id"] in node_map:
                node_map[nd["parent_id"]]["children"].append(nd)
            else:
                tree.append(nd)

        return {"tree": tree, "total_nodes": len(nodes)}


# ─── Paper Assignment ──────────────────────────────────────

@router.post("/directory/papers", summary="Assign paper to directory node")
async def assign_paper(node_id: str, document_id: str, db=Depends(get_db)):
    """Assign a paper to a directory node."""
    await ensure_tables(db)
    await _ensure_paper_in_node(node_id, document_id, db)
    return {"message": "Paper assigned to directory node"}


async def _ensure_paper_in_node(node_id: str, document_id: str, db):
    async with db.async_session_maker() as session:
        existing = (await session.execute(sa_text(
            "SELECT id FROM directory_papers WHERE node_id = :nid AND document_id = :did"),
            {"nid": node_id, "did": document_id})).fetchone()
        if not existing:
            await session.execute(sa_text(
                "INSERT INTO directory_papers (id, node_id, document_id) VALUES (:id, :nid, :did)"),
                {"id": str(uuid.uuid4()), "nid": node_id, "did": document_id})
            await session.commit()


@router.get("/directory/node/{node_id}/papers", summary="Get papers in directory node")
async def get_node_papers(node_id: str, db=Depends(get_db)):
    """Get all papers assigned to a directory node."""
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        node = (await session.execute(sa_text(
            "SELECT * FROM directory_nodes WHERE id = :id"), {"id": node_id})).fetchone()
        if not node:
            return {"error": "Node not found"}

        papers = (await session.execute(sa_text(
            "SELECT dp.*, d.title, d.authors, d.year, d.abstract FROM directory_papers dp "
            "LEFT JOIN documents d ON dp.document_id = d.id WHERE dp.node_id = :nid ORDER BY dp.added_at DESC"),
            {"nid": node_id})).fetchall()

        return {
            "node": {"id": node[0], "name": node[3], "type": node[4], "icon": node[6]},
            "papers": [{
                "id": p[0], "document_id": p[2],
                "title": p[4] or "Untitled", "authors": json.loads(p[5]) if isinstance(p[5], str) else (p[5] or []),
                "year": p[6], "abstract": (p[7] or "")[:200],
            } for p in papers],
            "count": len(papers),
        }


# ─── Auto-Classification ────────────────────────────────────

@router.post("/directory/auto-classify/{document_id}", summary="Auto-classify paper in directory")
async def auto_classify(document_id: str, db=Depends(get_db), llm_service=Depends(get_llm_service)):
    """Use AI to automatically suggest where a paper belongs in the directory tree."""
    await ensure_tables(db)
    doc = await db.get_document(document_id)
    if not doc:
        return {"error": "Document not found"}

    # Get available nodes
    async with db.async_session_maker() as session:
        nodes = (await session.execute(sa_text(
            "SELECT id, name, description FROM directory_nodes WHERE user_id = 'default' AND is_deleted = 0 AND node_type = 'folder'"))).fetchall()

    if not nodes:
        return {"suggestion": None, "message": "No directory nodes created yet. Create a taxonomy first."}

    text = f"Title: {doc.title}\nAbstract: {(doc.abstract or '')[:500]}"
    node_options = "\n".join(f"- {n[1]}: {n[2] or 'No description'}" for n in nodes)

    try:
        resp = await llm_service.chat_completion(
            messages=[{"role": "user", "content": f"Suggest the best directory folder for this paper based on its content.\n\nPaper:\n{text}\n\nAvailable folders:\n{node_options}\n\nOutput the folder name only, or 'NONE' if no good match."}],
            system_prompt="You classify academic papers into topic folders. Output only the folder name.",
        )
        suggestion = resp.get("content", "NONE").strip() if isinstance(resp, dict) else str(resp).strip()
    except Exception:
        suggestion = "NONE"

    matched_node = None
    for n in nodes:
        if n[1].lower() in suggestion.lower() or suggestion.lower() in n[1].lower():
            matched_node = {"id": n[0], "name": n[1]}
            break

    if matched_node:
        await _ensure_paper_in_node(matched_node["id"], document_id, db)

    return {
        "document_id": document_id,
        "title": doc.title or doc.filename,
        "ai_suggestion": suggestion if suggestion != "NONE" else None,
        "auto_assigned": matched_node,
    }


# ─── Classification Views ──────────────────────────────────

@router.post("/directory/views", summary="Create a directory view")
async def create_view(name: str, root_node_id: str = None, is_default: bool = False, db=Depends(get_db)):
    await ensure_tables(db)
    vid = str(uuid.uuid4())
    async with db.async_session_maker() as session:
        if is_default:
            await session.execute(sa_text(
                "UPDATE directory_views SET is_default = 0 WHERE user_id = 'default'"))
        await session.execute(sa_text(
            "INSERT INTO directory_views (id, user_id, name, root_node_id, is_default) VALUES (:id, 'default', :n, :rn, :df)"),
            {"id": vid, "n": name, "rn": root_node_id, "df": int(is_default)})
        await session.commit()
    return {"id": vid, "name": name}


@router.get("/directory/views", summary="List directory views")
async def list_views(db=Depends(get_db)):
    await ensure_tables(db)
    async with db.async_session_maker() as session:
        rows = (await session.execute(sa_text(
            "SELECT * FROM directory_views WHERE user_id = 'default' ORDER BY is_default DESC, created_at DESC"))).fetchall()
        return [{"id": r[0], "name": r[2], "root_node_id": r[3], "is_default": bool(r[4])} for r in rows]


# ─── Suggested Taxonomy ─────────────────────────────────────

@router.post("/directory/suggest-taxonomy", summary="AI-suggest directory taxonomy")
async def suggest_taxonomy(db=Depends(get_db), llm_service=Depends(get_llm_service)):
    """Use AI to analyze your library and suggest a directory taxonomy."""
    docs = await db.get_documents(limit=50) if db else []
    if not docs:
        return {"error": "Not enough papers to suggest taxonomy"}

    # Extract keywords
    all_keywords = []
    for d in docs:
        all_keywords.extend(d.keywords or [])
    keyword_freq = {}
    for kw in all_keywords:
        keyword_freq[kw] = keyword_freq.get(kw, 0) + 1
    top_keywords = sorted(keyword_freq.items(), key=lambda x: -x[1])[:15]

    try:
        resp = await llm_service.chat_completion(
            messages=[{"role": "user", "content": "Suggest a hierarchical folder taxonomy (max 3 levels deep) to organize these research topics. Output as JSON: {\"taxonomy\": [{\"name\": \"...\", \"children\": [{\"name\": \"...\"}]}]}\n\nResearch topics found in library:\n" + "\n".join(f"- {kw} ({cnt} papers)" for kw, cnt in top_keywords)}],
            system_prompt="You design research paper taxonomies. Output valid JSON only. Each folder should represent a distinct research area.",
        )
        content = resp.get("content", "{}") if isinstance(resp, dict) else str(resp)
        import re
        match = re.search(r'\{.*\}', content, re.DOTALL)
        taxonomy = json.loads(match.group()) if match else {"taxonomy": []}
    except Exception:
        taxonomy = {"taxonomy": [{"name": kw, "children": []} for kw, _ in top_keywords[:5]]}

    return {
        "based_on": len(docs),
        "top_keywords": [{"keyword": kw, "count": cnt} for kw, cnt in top_keywords],
        "suggested_taxonomy": taxonomy,
    }
