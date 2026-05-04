"""
Paper Agent MCP Server — Expose your research library as AI-accessible tools.

This MCP server allows any MCP-compatible AI assistant (Claude Desktop, Claude Code,
VS Code, Cursor, etc.) to interact with your Paper Agent library to:
  - Search and retrieve papers
  - Get summaries and full text
  - Find related research
  - Manage reading lists
  - Export citations
  - Analyze research trends

Usage:
    pip install mcp httpx
    python mcp/server.py

Then configure your MCP client to connect to this server.
"""

import os
import sys
import json
import logging
from typing import Any, Optional
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# MCP SDK
try:
    from mcp.server import Server, NotificationOptions
    from mcp.server.models import InitializationOptions
    import mcp.server.stdio
    import mcp.types as types
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# Paper Agent services
from paper_agent.backend.services.registry import get_db, get_vector_service, get_llm_service
from paper_agent.backend.services.citation_service import (
    doc_to_bibtex, generate_bibliography, search_crossref,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("paper-agent-mcp")


def create_server() -> Optional[Any]:
    """Create and configure the MCP server."""
    if not MCP_AVAILABLE:
        logger.error("MCP SDK not installed. Run: pip install mcp")
        return None

    server = Server("paper-agent")

    db = get_db()
    vector_service = get_vector_service()
    llm_service = get_llm_service()

    # ─── Tools ────────────────────────────────────────────────────────

    @server.list_tools()
    async def handle_list_tools():
        return [
            types.Tool(
                name="search_papers",
                description="Search papers in your library by keyword, title, or author. Returns ranked results with relevance scores.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query (keyword, title, author, or phrase)"},
                        "limit": {"type": "integer", "description": "Max results", "default": 10},
                    },
                    "required": ["query"],
                },
            ),
            types.Tool(
                name="get_paper",
                description="Get detailed information about a specific paper by its ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "paper_id": {"type": "string", "description": "The paper's unique ID (UUID)"},
                    },
                    "required": ["paper_id"],
                },
            ),
            types.Tool(
                name="get_paper_summary",
                description="Get the AI-generated summary of a paper.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "paper_id": {"type": "string", "description": "Paper ID"},
                        "style": {"type": "string", "description": "Summary style: academic, simple, or detailed", "default": "academic"},
                    },
                    "required": ["paper_id"],
                },
            ),
            types.Tool(
                name="find_related_papers",
                description="Find papers related to a given paper, using semantic similarity.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "paper_id": {"type": "string", "description": "Paper ID"},
                        "limit": {"type": "integer", "default": 5},
                    },
                    "required": ["paper_id"],
                },
            ),
            types.Tool(
                name="get_library_stats",
                description="Get statistics about your paper library: total papers, reading progress, processing status.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="ask_library",
                description="Ask a natural language question about your library. The AI searches across all papers and synthesizes an answer with citations.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "question": {"type": "string", "description": "Your research question"},
                        "limit": {"type": "integer", "default": 8},
                    },
                    "required": ["question"],
                },
            ),
            types.Tool(
                name="export_citation",
                description="Export a paper citation in BibTeX format or formatted bibliography style.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "paper_id": {"type": "string", "description": "Paper ID"},
                        "style": {"type": "string", "description": "Citation style: bibtex, apa, mla, ieee, chicago", "default": "bibtex"},
                    },
                    "required": ["paper_id"],
                },
            ),
            types.Tool(
                name="manage_reading_list",
                description="Add or update a paper's reading status: to_read, reading, read, skipped, or reference.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "paper_id": {"type": "string", "description": "Paper ID"},
                        "status": {"type": "string", "enum": ["to_read", "reading", "read", "skipped", "reference"]},
                    },
                    "required": ["paper_id", "status"],
                },
            ),
            types.Tool(
                name="get_reading_list",
                description="Get your current reading list, optionally filtered by status.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["to_read", "reading", "read", "skipped", "reference"], "description": "Filter by status (optional)"},
                        "limit": {"type": "integer", "default": 20},
                    },
                },
            ),
            types.Tool(
                name="search_arxiv",
                description="Search for papers on arXiv and import them into your library.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "default": 10},
                        "import_results": {"type": "boolean", "description": "Auto-import results into library", "default": False},
                    },
                    "required": ["query"],
                },
            ),
            types.Tool(
                name="get_paper_annotations",
                description="Get all highlights and notes for a paper.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "paper_id": {"type": "string", "description": "Paper ID"},
                    },
                    "required": ["paper_id"],
                },
            ),
            types.Tool(
                name="generate_research_digest",
                description="Generate an AI research digest summarizing recent papers in your library.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "days": {"type": "integer", "description": "Lookback period in days", "default": 7},
                    },
                },
            ),
            types.Tool(
                name="analyze_citation_network",
                description="Analyze citation relationships between papers in your library. Identifies influential papers and research clusters.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="manage_alerts",
                description="Create or list research alerts. Get notified when new papers match your interests.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list", "create", "delete", "check"]},
                        "name": {"type": "string", "description": "Alert name (for create)"},
                        "query": {"type": "string", "description": "Search query to monitor (for create)"},
                        "alert_id": {"type": "string", "description": "Alert ID (for delete)"},
                    },
                    "required": ["action"],
                },
            ),
            types.Tool(
                name="manage_projects",
                description="Organize papers into research projects with milestones and tracking.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list", "create", "get", "delete"]},
                        "title": {"type": "string", "description": "Project title"},
                        "project_id": {"type": "string", "description": "Project ID"},
                    },
                    "required": ["action"],
                },
            ),
            types.Tool(
                name="get_glossary",
                description="Get automatically extracted key terms and definitions from your papers.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "search": {"type": "string", "description": "Search for specific terms"},
                    },
                },
            ),
            types.Tool(
                name="manage_collections",
                description="Create curated paper collections/bundles for sharing or organization.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list", "create", "get"]},
                        "title": {"type": "string", "description": "Collection title"},
                        "collection_id": {"type": "string", "description": "Collection ID"},
                    },
                    "required": ["action"],
                },
            ),
            types.Tool(
                name="analyze_timeline",
                description="Get research timeline data showing paper distribution, trends, and author activity over time.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "group_by": {"type": "string", "enum": ["year", "topic"], "default": "year"},
                    },
                },
            ),
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        try:
            if name == "search_papers":
                query = arguments["query"]
                limit = arguments.get("limit", 10)
                if vector_service:
                    results = vector_service.search_similar(query, limit=limit)
                else:
                    results = await db.search_documents(query, limit=limit) if db else []
                if not results:
                    results = await db.search_documents(query, limit=limit) if db else []

                docs_list = []
                for r in results[:limit]:
                    if isinstance(r, dict):
                        doc_id = r.get("document_id", r.get("id", ""))
                        title = r.get("title", r.get("filename", "Untitled"))
                        score = r.get("score", None)
                        snippet = r.get("text", "")[:300] if r.get("text") else ""
                    else:
                        doc_id = r.id
                        title = r.title or r.filename or "Untitled"
                        score = None
                        snippet = (r.abstract or "")[:300]

                    docs_list.append(f"- **{title}** (ID: `{doc_id}`)" + (f" [Relevance: {score:.2f}]" if score else ""))

                text = f"Found {len(docs_list)} papers:\n\n" + "\n".join(docs_list) if docs_list else "No papers found matching your query."
                return [types.TextContent(type="text", text=text)]

            elif name == "get_paper":
                pid = arguments["paper_id"]
                doc = await db.get_document(pid) if db else None
                if not doc:
                    return [types.TextContent(type="text", text=f"Paper not found: {pid}")]
                meta = doc.doc_metadata or {}
                text = (
                    f"# {doc.title or 'Untitled'}\n\n"
                    f"- **Authors**: {', '.join(doc.authors) if doc.authors else 'Unknown'}\n"
                    f"- **Year**: {doc.year or 'N/A'}\n"
                    f"- **Status**: {['Pending', 'Processing', 'Completed', 'Failed'][doc.processed] if doc.processed < 4 else 'Unknown'}\n"
                    f"- **ID**: `{doc.id}`\n\n"
                )
                if doc.abstract:
                    text += f"**Abstract**: {doc.abstract[:1000]}\n\n"
                if doc.summary:
                    text += f"**Summary**: {doc.summary[:500]}\n\n"
                return [types.TextContent(type="text", text=text)]

            elif name == "get_paper_summary":
                pid = arguments["paper_id"]
                doc = await db.get_document(pid) if db else None
                if not doc:
                    return [types.TextContent(type="text", text="Paper not found")]
                if doc.summary:
                    text = f"## Summary of: {doc.title}\n\n{doc.summary}"
                else:
                    text = f"No AI-generated summary available for {doc.title or doc.filename}. Generate one in the Paper Agent UI."
                return [types.TextContent(type="text", text=text)]

            elif name == "find_related_papers":
                pid = arguments["paper_id"]
                limit = arguments.get("limit", 5)
                doc = await db.get_document(pid) if db else None
                if not doc:
                    return [types.TextContent(type="text", text="Paper not found")]

                if vector_service:
                    text_to_search = (doc.abstract or doc.title or "")
                    results = vector_service.search_similar(text_to_search, limit=limit + 1)
                    results = [r for r in results if r.get("document_id") != pid][:limit]
                else:
                    results = await db.search_documents(doc.title or "", limit=limit) if db else []
                    results = [r for r in results if r.id != pid][:limit]

                if not results:
                    return [types.TextContent(type="text", text="No related papers found.")]

                lines = [f"## Related to: {doc.title}\n"]
                for r in results:
                    rid = r.get("document_id", r.id) if isinstance(r, dict) else r.id
                    title = r.get("title", r.title) if isinstance(r, dict) else r.title
                    score = r.get("score", None) if isinstance(r, dict) else None
                    lines.append(f"- **{title}** (ID: `{rid}`)" + (f" [Score: {score:.2f}]" if score else ""))
                return [types.TextContent(type="text", text="\n".join(lines))]

            elif name == "get_library_stats":
                stats = await db.get_processing_stats() if db else {}
                reading_stats = {"to_read": 0, "reading": 0, "read": 0}
                try:
                    async with db.async_session_maker() as session:
                        from sqlalchemy import text as sa_text
                        row = (await session.execute(sa_text(
                            "SELECT COUNT(*), SUM(CASE WHEN status='to_read' THEN 1 ELSE 0 END), SUM(CASE WHEN status='reading' THEN 1 ELSE 0 END), SUM(CASE WHEN status='read' THEN 1 ELSE 0 END) FROM reading_list"
                        ))).fetchone()
                        if row:
                            reading_stats = {"total": row[0] or 0, "to_read": row[1] or 0, "reading": row[2] or 0, "read": row[3] or 0}
                except Exception:
                    pass

                text = (
                    f"## Library Statistics\n\n"
                    f"**Documents**: {stats.get('total', 0)} total ({stats.get('completed', 0)} processed, {stats.get('pending', 0)} pending)\n"
                    f"**Reading**: {reading_stats.get('read', 0)} read, {reading_stats.get('reading', 0)} in progress, {reading_stats.get('to_read', 0)} to read\n"
                )
                if vector_service:
                    vstats = vector_service.get_collection_stats()
                    text += f"**Vector DB**: {vstats.get('total_chunks', 0)} chunks ({vstats.get('model', 'N/A')})\n"
                return [types.TextContent(type="text", text=text)]

            elif name == "ask_library":
                question = arguments["question"]
                limit = arguments.get("limit", 8)
                if not vector_service or not llm_service:
                    return [types.TextContent(type="text", text="Ask Library requires vector search and LLM services to be configured.")]
                results = vector_service.search_similar(question, limit=limit)
                if not results:
                    return [types.TextContent(type="text", text="No relevant documents found in your library to answer this question.")]

                doc_ids = set(r["document_id"] for r in results)
                doc_map = {}
                for did in doc_ids:
                    doc = await db.get_document(did)
                    if doc:
                        doc_map[did] = doc.title or doc.filename

                context_parts = []
                seen = set()
                sources = []
                for r in results:
                    did = r["document_id"]
                    info = doc_map.get(did, "Unknown")
                    context_parts.append(f"[Source: {info}]\n{r.get('text', '')[:600]}")
                    if did not in seen:
                        seen.add(did)
                        sources.append(f"- {info} (ID: `{did}`)")

                context = "\n\n---\n\n".join(context_parts)
                response = await llm_service.chat_completion(
                    messages=[{"role": "user", "content": f"Based on my research library, answer: {question}\n\nRelevant excerpts:\n\n{context}"}],
                    system_prompt="You are a research assistant. Answer based ONLY on the provided excerpts. Cite sources. Be precise.",
                )
                answer = response.get("content", "") if isinstance(response, dict) else str(response)
                sources_text = "\n\n**Sources:**\n" + "\n".join(sources)
                return [types.TextContent(type="text", text=answer + sources_text)]

            elif name == "export_citation":
                pid = arguments["paper_id"]
                style = arguments.get("style", "bibtex")
                doc = await db.get_document(pid) if db else None
                if not doc:
                    return [types.TextContent(type="text", text="Paper not found")]
                meta = doc.doc_metadata or {}
                if style == "bibtex":
                    bib = doc_to_bibtex(doc.id, doc.title, doc.authors, doc.year,
                                        meta.get("journal"), meta.get("volume"),
                                        meta.get("number"), meta.get("pages"), meta.get("doi"))
                    return [types.TextContent(type="text", text=bib)]
                else:
                    bib = generate_bibliography([{
                        "authors": doc.authors or ["Unknown"], "year": doc.year,
                        "title": doc.title or "Untitled", "journal": meta.get("journal", ""),
                        "volume": meta.get("volume", ""), "issue": meta.get("number", ""),
                        "pages": meta.get("pages", ""), "doi": meta.get("doi", ""),
                    }], style=style)
                    return [types.TextContent(type="text", text=bib)]

            elif name == "manage_reading_list":
                pid = arguments["paper_id"]
                status = arguments["status"]
                import uuid as _uuid
                from datetime import datetime as _dt
                async with db.async_session_maker() as session:
                    from sqlalchemy import text as sa_text
                    now = _dt.utcnow().isoformat()
                    existing = (await session.execute(sa_text("SELECT id FROM reading_list WHERE document_id = :d"), {"d": pid})).scalar()
                    if existing:
                        completed = f", date_completed = '{now}'" if status == "read" else ""
                        await session.execute(sa_text(f"UPDATE reading_list SET status = :s, date_updated = '{now}'{completed} WHERE id = :id"), {"s": status, "id": existing})
                    else:
                        eid = str(_uuid.uuid4())
                        await session.execute(sa_text("INSERT INTO reading_list (id, document_id, user_id, status, date_added, date_updated) VALUES (:id, :d, 'default', :s, :n, :n)"), {"id": eid, "d": pid, "s": status, "n": now})
                    await session.commit()
                return [types.TextContent(type="text", text=f"Paper marked as '{status}' ✓")]

            elif name == "get_reading_list":
                status_filter = arguments.get("status")
                limit = arguments.get("limit", 20)
                async with db.async_session_maker() as session:
                    from sqlalchemy import text as sa_text
                    sql = "SELECT r.status, r.progress, d.title, d.authors, d.year, d.id FROM reading_list r LEFT JOIN documents d ON r.document_id = d.id WHERE r.user_id = 'default'"
                    params = {}
                    if status_filter:
                        sql += " AND r.status = :s"
                        params["s"] = status_filter
                    sql += " ORDER BY r.date_updated DESC LIMIT :lim"
                    params["lim"] = limit
                    rows = (await session.execute(sa_text(sql), params)).fetchall()

                if not rows:
                    return [types.TextContent(type="text", text="Reading list is empty.")]
                entries = []
                for r in rows:
                    entries.append(f"- **{r[2] or 'Untitled'}** ({r[4] or 'n.d.'}) — *{r[0]}* — {', '.join(r[3] or [])[:50]} (ID: `{r[5]}`)")
                text = f"## Reading List ({len(entries)} items)\n\n" + "\n".join(entries)
                return [types.TextContent(type="text", text=text)]

            elif name == "search_arxiv":
                query = arguments["query"]
                max_results = arguments.get("max_results", 10)
                should_import = arguments.get("import_results", False)
                from paper_agent.backend.services.arxiv_service import arxiv_service
                if not arxiv_service:
                    return [types.TextContent(type="text", text="arXiv service not available.")]
                results = arxiv_service.search(query, max_results=max_results)
                if not results:
                    return [types.TextContent(type="text", text="No arXiv results found.")]
                lines = [f"## arXiv Results for '{query}'\n"]
                for r in results[:max_results]:
                    lines.append(f"- **{r.get('title', 'Untitled')}** (arXiv: `{r.get('arxiv_id', '?')}`)")
                    lines.append(f"  Authors: {', '.join(r.get('authors', [])[:3])}")
                    lines.append(f"  {r.get('abstract', '')[:200]}...\n")
                return [types.TextContent(type="text", text="\n".join(lines))]

            elif name == "get_paper_annotations":
                pid = arguments["paper_id"]
                async with db.async_session_maker() as session:
                    from sqlalchemy import text as sa_text
                    annotations = (await session.execute(sa_text("SELECT page_number, text, note, highlight_color FROM annotations WHERE document_id = :d AND is_deleted = 0 ORDER BY page_number"), {"d": pid})).fetchall()
                    notes = (await session.execute(sa_text("SELECT page_number, content, tags FROM document_notes WHERE document_id = :d AND is_deleted = 0 ORDER BY page_number"), {"d": pid})).fetchall()
                if not annotations and not notes:
                    return [types.TextContent(type="text", text="No annotations for this paper.")]
                text = "## Annotations & Notes\n\n"
                for a in annotations:
                    text += f"- **Page {a[0]}**: \"{a[1]}\" {f'(Note: {a[2]})' if a[2] else ''}\n"
                for n in notes:
                    text += f"- 📝 **Page {n[0]}**: {n[1]}\n"
                return [types.TextContent(type="text", text=text)]

            elif name == "generate_research_digest":
                days = arguments.get("days", 7)
                docs = await db.get_documents(limit=20) if db else []
                if not docs:
                    return [types.TextContent(type="text", text="No documents in library. Upload some papers first.")]
                titles = "\n".join(f"- {d.title or d.filename} ({d.year or 'n.d.'})" for d in docs[:10])
                if llm_service:
                    resp = await llm_service.chat_completion(
                        messages=[{"role": "user",
                                   "content": f"Generate a concise research digest from these papers. Identify themes, methodologies, and connections:\n\n{titles}"}],
                        system_prompt="You are a research analyst. Provide structured markdown analysis.",
                    )
                    analysis = resp.get("content", "") if isinstance(resp, dict) else str(resp)
                else:
                    analysis = "AI analysis unavailable."
                text = f"## Research Digest (Last {days} days)\n\nBased on {len(docs)} papers:\n\n{titles}\n\n### AI Analysis\n\n{analysis}"
                return [types.TextContent(type="text", text=text)]

            elif name == "analyze_citation_network":
                docs = await db.get_documents(limit=50) if db else []
                if not docs:
                    return [types.TextContent(type="text", text="No papers to analyze.")]
                years = {}
                authors = {}
                for d in docs:
                    if d.year:
                        years[d.year] = years.get(d.year, 0) + 1
                    if d.authors:
                        for a in d.authors:
                            authors[a] = authors.get(a, 0) + 1

                text = "## Citation Network Analysis\n\n"
                text += f"**Total papers**: {len(docs)}\n\n"
                text += "**Publications by year**:\n"
                for y in sorted(years.keys()):
                    text += f"- {y}: {years[y]} papers\n"
                text += "\n**Most prolific authors**:\n"
                top_authors = sorted(authors.items(), key=lambda x: -x[1])[:10]
                for name, count in top_authors:
                    text += f"- {name}: {count} papers\n"

                avg_year = sum(k * v for k, v in years.items()) / sum(years.values()) if years else 0
                text += f"\n**Average publication year**: {avg_year:.0f}\n"
                return [types.TextContent(type="text", text=text)]

            elif name == "manage_alerts":
                action = arguments.get("action", "list")
                from paper_agent.backend.api.routes.alerts import ensure_tables as ensure_alert_tables
                await ensure_alert_tables(db)
                if action == "list":
                    async with db.async_session_maker() as session:
                        from sqlalchemy import text as sa_text
                        rows = (await session.execute(sa_text("SELECT name, query, frequency, last_triggered FROM research_alerts WHERE user_id = 'default' AND is_active = 1"))).fetchall()
                        if not rows:
                            return [types.TextContent(type="text", text="No active alerts. Create one with manage_alerts(action='create', name='...', query='...').")]
                        text = "## Active Research Alerts\n\n" + "\n".join(f"- **{r[0]}**: `{r[1]}` ({r[2]})" for r in rows)
                        return [types.TextContent(type="text", text=text)]
                elif action == "create":
                    name = arguments.get("name", "Alert")
                    query = arguments.get("query", "")
                    import uuid
                    async with db.async_session_maker() as session:
                        from sqlalchemy import text as sa_text
                        await session.execute(sa_text(
                            "INSERT INTO research_alerts (id, user_id, name, query, frequency) VALUES (:id, 'default', :n, :q, 'daily')"),
                            {"id": str(uuid.uuid4()), "n": name, "q": query})
                        await session.commit()
                    return [types.TextContent(type="text", text=f"✅ Alert '{name}' created! I'll notify you when new papers match: {query}")]
                elif action == "check":
                    # Check all active alerts
                    async with db.async_session_maker() as session:
                        from sqlalchemy import text as sa_text
                        alerts = (await session.execute(sa_text("SELECT id, name, query FROM research_alerts WHERE user_id = 'default' AND is_active = 1"))).fetchall()
                        matches = 0
                        for alert_id, name, query in alerts:
                            if vector_service:
                                results = vector_service.search_similar(query, limit=3)
                                for r in results:
                                    if r.get("score", 0) > 0.5:
                                        matches += 1
                                        nid = str(uuid.uuid4())
                                        await session.execute(sa_text(
                                            "INSERT INTO alert_history (id, alert_id, user_id, document_id, message) VALUES (:id, :aid, 'default', :did, :msg)"),
                                            {"id": nid, "aid": alert_id, "did": r.get("document_id", ""), "msg": f"New paper matches '{name}'"})
                            await session.execute(sa_text("UPDATE research_alerts SET last_triggered = :n WHERE id = :id"),
                                                  {"n": datetime.utcnow().isoformat(), "id": alert_id})
                        await session.commit()
                    return [types.TextContent(type="text", text=f"Checked {len(alerts)} alerts. Found {matches} new matches.")]
                return [types.TextContent(type="text", text="Unknown action. Use: list, create, check")]

            elif name == "manage_projects":
                action = arguments.get("action", "list")
                if action == "list":
                    from sqlalchemy import text as sa_text
                    async with db.async_session_maker() as session:
                        rows = (await session.execute(sa_text(
                            "SELECT id, title, status, priority, (SELECT COUNT(*) FROM project_papers WHERE project_id = p.id) as cnt FROM research_projects p WHERE user_id = 'default' ORDER BY updated_at DESC"))).fetchall()
                        if not rows:
                            return [types.TextContent(type="text", text="No research projects. Create one with manage_projects(action='create', title='...')")]
                        text = "## Research Projects\n\n" + "\n".join(f"- **{r[1]}** ({r[2]}, {r[3]} priority) — {r[4]} papers" for r in rows)
                        return [types.TextContent(type="text", text=text)]
                elif action == "create":
                    title = arguments.get("title", "New Project")
                    import uuid
                    async with db.async_session_maker() as session:
                        from sqlalchemy import text as sa_text
                        pid = str(uuid.uuid4())
                        await session.execute(sa_text("INSERT INTO research_projects (id, user_id, title) VALUES (:id, 'default', :t)"), {"id": pid, "t": title})
                        await session.commit()
                    return [types.TextContent(type="text", text=f"✅ Project '{title}' created! (ID: {pid})")]
                return [types.TextContent(type="text", text="Unknown action")]

            elif name == "get_glossary":
                search = arguments.get("search", "")
                from sqlalchemy import text as sa_text
                async with db.async_session_maker() as session:
                    sql = "SELECT term, definition, category FROM concept_glossary WHERE user_id = 'default'"
                    params = {}
                    if search:
                        sql += " AND (term LIKE :s OR definition LIKE :s)"
                        params["s"] = f"%{search}%"
                    sql += " ORDER BY term ASC LIMIT 30"
                    rows = (await session.execute(sa_text(sql), params)).fetchall()
                    if not rows:
                        return [types.TextContent(type="text", text=f"No glossary terms found{' for ' + search if search else ''}. Extract terms from a paper first.")]
                    text = "## Glossary\n\n" + "\n\n".join(f"**{r[0]}** ({r[2] or 'concept'}): {r[1] or 'No definition'}" for r in rows)
                    return [types.TextContent(type="text", text=text)]

            elif name == "manage_collections":
                action = arguments.get("action", "list")
                from sqlalchemy import text as sa_text
                if action == "list":
                    async with db.async_session_maker() as session:
                        rows = (await session.execute(sa_text(
                            "SELECT id, title, description, is_public FROM paper_collections WHERE user_id = 'default' ORDER BY updated_at DESC"))).fetchall()
                        if not rows:
                            return [types.TextContent(type="text", text="No collections. Create one with manage_collections(action='create', title='...')")]
                        text = "## Collections\n\n" + "\n".join(f"- **{r[1]}**: {r[2] or 'No description'} {'🔓' if r[3] else '🔒'}" for r in rows)
                        return [types.TextContent(type="text", text=text)]
                elif action == "create":
                    title = arguments.get("title", "New Collection")
                    import uuid
                    async with db.async_session_maker() as session:
                        cid = str(uuid.uuid4())
                        await session.execute(sa_text("INSERT INTO paper_collections (id, user_id, title) VALUES (:id, 'default', :t)"), {"id": cid, "t": title})
                        await session.commit()
                    return [types.TextContent(type="text", text=f"✅ Collection '{title}' created!")]
                elif action == "get":
                    cid = arguments.get("collection_id", "")
                    async with db.async_session_maker() as session:
                        col = (await session.execute(sa_text("SELECT title, description FROM paper_collections WHERE id = :id"), {"id": cid})).fetchone()
                        papers = (await session.execute(sa_text(
                            "SELECT cp.document_id, d.title, d.authors, d.year FROM collection_papers cp LEFT JOIN documents d ON cp.document_id = d.id WHERE cp.collection_id = :cid"), {"cid": cid})).fetchall()
                        if not col:
                            return [types.TextContent(type="text", text="Collection not found")]
                        text = f"# {col[0]}\n{col[1] or ''}\n\n## Papers ({len(papers)})\n"
                        for p in papers:
                            text += f"- **{p[1] or 'Untitled'}** ({p[3] or 'n.d.'})\n"
                        return [types.TextContent(type="text", text=text)]
                return [types.TextContent(type="text", text="Unknown action")]

            elif name == "analyze_timeline":
                group_by = arguments.get("group_by", "year")
                docs = await db.get_documents(limit=200) if db else []
                if not docs:
                    return [types.TextContent(type="text", text="No papers to analyze.")]
                from collections import defaultdict as dd
                if group_by == "year":
                    years = dd(int)
                    for d in docs:
                        if d.year: years[d.year] += 1
                    text = "## Research Timeline\n\n" + "\n".join(f"- **{y}**: {c} papers" for y, c in sorted(years.items()))
                else:
                    topics = dd(int)
                    for d in docs:
                        for kw in (d.keywords or [])[:3]:
                            topics[kw] += 1
                    text = "## Research Topics\n\n" + "\n".join(f"- **{t}**: {c} papers" for t, c in sorted(topics.items(), key=lambda x: -x[1])[:20])
                text += f"\n\n**Total**: {len(docs)} papers"
                year_list = [d.year for d in docs if d.year]
                if year_list:
                    text += f" | **Range**: {min(year_list)}–{max(year_list)}"
                return [types.TextContent(type="text", text=text)]

            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

        except Exception as e:
            logger.error(f"Tool {name} failed: {e}", exc_info=True)
            return [types.TextContent(type="text", text=f"Error executing {name}: {str(e)}")]

    # ─── Resources ────────────────────────────────────────────────────

    @server.list_resources()
    async def handle_list_resources():
        resources = []
        if db:
            docs = await db.get_documents(limit=20)
            for d in docs:
                resources.append(types.Resource(
                    uri=f"paper:///{d.id}",
                    name=d.title or d.filename or "Untitled",
                    description=f"Paper by {', '.join(d.authors or [])} ({d.year or 'n.d.'})",
                    mimeType="text/markdown",
                ))
        resources.append(types.Resource(
            uri="library:///overview",
            name="Library Overview",
            description="Overview of your entire paper library",
            mimeType="text/markdown",
        ))
        return resources

    @server.read_resource()
    async def handle_read_resource(uri: str):
        if uri == "library:///overview":
            stats = await db.get_processing_stats() if db else {}
            text = f"# Paper Agent Library\n\nTotal: {stats.get('total', 0)} papers\nCompleted: {stats.get('completed', 0)}\nPending: {stats.get('pending', 0)}"
            return [types.TextContent(type="text", text=text)]

        pid = uri.replace("paper:///", "")
        doc = await db.get_document(pid) if db else None
        if not doc:
            raise ValueError(f"Paper not found: {pid}")
        meta = doc.doc_metadata or {}
        text = (
            f"# {doc.title or 'Untitled'}\n\n"
            f"- **Authors**: {', '.join(doc.authors) if doc.authors else 'Unknown'}\n"
            f"- **Year**: {doc.year or 'N/A'}\n"
            f"- **DOI**: {meta.get('doi', 'N/A')}\n"
            f"- **Journal**: {meta.get('journal', 'N/A')}\n\n"
        )
        if doc.abstract:
            text += f"## Abstract\n\n{doc.abstract}\n\n"
        if doc.summary:
            text += f"## AI Summary\n\n{doc.summary}\n\n"
        return [types.TextContent(type="text", text=text)]

    # ─── Prompts ─────────────────────────────────────────────────────

    @server.list_prompts()
    async def handle_list_prompts():
        return [
            types.Prompt(
                name="analyze_paper",
                description="Deep analysis of a specific paper: methodology, contributions, limitations",
                arguments=[
                    types.PromptArgument(name="paper_id", description="Paper ID", required=True),
                ],
            ),
            types.Prompt(
                name="literature_review",
                description="Generate a literature review section from selected papers",
                arguments=[
                    types.PromptArgument(name="paper_ids", description="Comma-separated paper IDs", required=True),
                    types.PromptArgument(name="topic", description="Research topic or focus area"),
                ],
            ),
            types.Prompt(
                name="compare_papers",
                description="Compare multiple papers: methodology, results, contributions",
                arguments=[
                    types.PromptArgument(name="paper_ids", description="Comma-separated paper IDs (2-5)", required=True),
                ],
            ),
            types.Prompt(
                name="research_idea",
                description="Generate novel research ideas based on gaps in your library",
                arguments=[
                    types.PromptArgument(name="paper_ids", description="Comma-separated paper IDs for context", required=True),
                    types.PromptArgument(name="field", description="Research field"),
                ],
            ),
        ]

    @server.get_prompt()
    async def handle_get_prompt(name: str, arguments: dict[str, str]) -> types.GetPromptResult:
        if name == "analyze_paper":
            pid = arguments.get("paper_id", "")
            doc = await db.get_document(pid) if db else None
            paper_info = f"**Title**: {doc.title}\n**Authors**: {', '.join(doc.authors) if doc.authors else 'Unknown'}\n**Year**: {doc.year}\n**Abstract**: {doc.abstract[:1000] if doc.abstract else 'N/A'}" if doc else "Paper not found."
            return types.GetPromptResult(
                description=f"Analyze paper: {doc.title if doc else pid}",
                messages=[
                    types.PromptMessage(role="user", content=types.TextContent(
                        type="text",
                        text=f"Please provide a deep analysis of this academic paper:\n\n{paper_info}\n\nCover: research problem, methodology, key contributions, experimental results, limitations, and suggestions for improvement.",
                    )),
                ],
            )

        elif name == "literature_review":
            pids = [p.strip() for p in arguments.get("paper_ids", "").split(",") if p.strip()]
            topic = arguments.get("topic", "the research topic")
            papers = []
            for pid in pids:
                doc = await db.get_document(pid) if db else None
                if doc:
                    papers.append(f"- {doc.title} ({doc.year}): {', '.join(doc.authors or [])}\n  {doc.summary or doc.abstract or 'N/A'}")

            return types.GetPromptResult(
                description=f"Literature review on {topic}",
                messages=[
                    types.PromptMessage(role="user", content=types.TextContent(
                        type="text",
                        text=f"Write a structured literature review section on {topic} based on these papers:\n\n{chr(10).join(papers)}\n\nOrganize by themes, compare methodologies, identify research gaps. Format in markdown.",
                    )),
                ],
            )

        elif name == "compare_papers":
            pids = [p.strip() for p in arguments.get("paper_ids", "").split(",") if p.strip()]
            papers = []
            for pid in pids[:5]:
                doc = await db.get_document(pid) if db else None
                if doc:
                    papers.append(f"### {doc.title} ({doc.year})\n- Authors: {', '.join(doc.authors or [])}\n- Abstract: {(doc.abstract or 'N/A')[:500]}\n- Summary: {(doc.summary or 'N/A')[:300]}")
            return types.GetPromptResult(
                description="Compare papers",
                messages=[
                    types.PromptMessage(role="user", content=types.TextContent(
                        type="text",
                        text=f"Compare and contrast these papers:\n\n{chr(10).join(papers)}\n\nCover: research questions, methodologies, key findings, strengths, weaknesses.",
                    )),
                ],
            )

        elif name == "research_idea":
            pids = [p.strip() for p in arguments.get("paper_ids", "").split(",") if p.strip()]
            field = arguments.get("field", "this research area")
            papers = []
            for pid in pids[:5]:
                doc = await db.get_document(pid) if db else None
                if doc:
                    papers.append(f"- {doc.title} ({doc.year}): {(doc.summary or doc.abstract or 'N/A')[:300]}")
            return types.GetPromptResult(
                description=f"Research ideas in {field}",
                messages=[
                    types.PromptMessage(role="user", content=types.TextContent(
                        type="text",
                        text=f"Based on these papers in {field}:\n\n{chr(10).join(papers)}\n\nGenerate 3 novel research ideas that address gaps not covered by existing work. For each idea, explain: the gap it addresses, proposed approach, expected impact.",
                    )),
                ],
            )

        raise ValueError(f"Unknown prompt: {name}")

    return server


def main():
    """Run the MCP server."""
    server = create_server()
    if not server:
        logger.error("Failed to create MCP server. Install the 'mcp' package: pip install mcp")
        sys.exit(1)

    logger.info("Paper Agent MCP Server starting...")
    logger.info("Connect via stdio transport (used by Claude Desktop, Claude Code, etc.)")

    async def run():
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="paper-agent",
                    server_version="2.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(tools_changed=True),
                        experimental_capabilities={},
                    ),
                ),
            )

    import asyncio
    asyncio.run(run())


if __name__ == "__main__":
    main()
