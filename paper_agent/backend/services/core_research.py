"""
Core Research Intelligence — essential paper discovery and organization capabilities.

Covers: paper clustering, quote search, auto-tagging, summary cards,
reading history, topic recommendations, citation context, concept extraction.
"""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List

from backend.services.registry import get_db, get_llm_service, get_vector_service

logger = logging.getLogger(__name__)


class CoreResearchIntelligence:
    """Essential research intelligence capabilities."""

    # ─── 1. Paper Clustering ─────────────────────────────────

    async def cluster_papers(self, max_papers: int = 50) -> Dict[str, Any]:
        """Auto-cluster papers by research topic using AI."""
        db = get_db()
        llm = get_llm_service()
        docs = await db.get_documents(limit=max_papers) if db else []

        if not docs or not llm:
            return {"clusters": [], "total": 0}

        # Extract titles + abstracts for clustering
        paper_list = "\n".join(
            f"[{i+1}] {d.title or d.filename}: {(d.abstract or '')[:200]}"
            for i, d in enumerate(docs)
        )

        try:
            resp = await llm.chat_completion(
                messages=[{"role": "user", "content":
                    f"Group these papers into research topic clusters. Output as JSON:\n"
                    f"{{\"clusters\": [{{\"topic\": \"...\", \"papers\": [1, 3, 5], \"description\": \"...\"}}]}}\n\nPapers:\n{paper_list}"}],
                system_prompt="You identify research topics and cluster papers by methodology, subject, and approach. Output valid JSON only.",
            )
            content = resp.get("content", "{}") if isinstance(resp, dict) else str(resp)
            match = re.search(r'\{.*\}', content, re.DOTALL)
            clusters = json.loads(match.group()) if match else {"clusters": []}

            # Enrich with document details
            enriched = []
            for c in clusters.get("clusters", []):
                papers = []
                for idx in c.get("papers", []):
                    if 0 <= idx - 1 < len(docs):
                        d = docs[idx - 1]
                        papers.append({"id": d.id, "title": d.title or d.filename, "year": d.year})
                enriched.append({
                    "topic": c.get("topic", "Unknown"),
                    "description": c.get("description", ""),
                    "papers": papers,
                    "size": len(papers),
                })

            return {"clusters": enriched, "total_papers": len(docs), "cluster_count": len(enriched)}

        except Exception as e:
            return {"clusters": [], "error": str(e)}

    # ─── 2. Quote/Claim Search ────────────────────────────────

    async def search_quote(self, quote: str, max_results: int = 5) -> Dict[str, Any]:
        """Find which paper a specific quote or claim comes from."""
        db = get_db()
        vs = get_vector_service()
        results = []

        # Use vector search to find papers with similar text
        if vs:
            search_results = vs.search_similar(quote, limit=max_results * 3)
        else:
            search_results = await db.search_documents(quote, limit=max_results) if db else []

        seen_docs = set()
        for r in search_results:
            did = r.get("document_id", r.get("id", ""))
            if did in seen_docs:
                continue
            seen_docs.add(did)

            doc = await db.get_document(did) if db else None
            if not doc:
                continue

            text = (doc.abstract or "") + " " + (doc.summary or "")
            # Find the most relevant sentence
            sentences = re.split(r'[.!?]+', text)
            best_sentence = ""
            best_score = 0
            for s in sentences:
                s = s.strip()
                if not s:
                    continue
                # Simple relevance scoring
                quote_words = set(quote.lower().split())
                sent_words = set(s.lower().split())
                overlap = len(quote_words & sent_words)
                score = overlap / max(len(quote_words), 1)
                if score > best_score:
                    best_score = score
                    best_sentence = s[:300]

            results.append({
                "document_id": did,
                "title": doc.title or doc.filename,
                "authors": doc.authors or [],
                "year": doc.year,
                "matched_sentence": best_sentence,
                "relevance": round(best_score, 3),
                "source": (doc.abstract or "")[:100] if best_score < 0.3 else best_sentence,
            })

        results.sort(key=lambda x: -x["relevance"])
        return {
            "quote": quote,
            "results": results[:max_results],
            "count": len(results[:max_results]),
        }

    # ─── 3. AI Auto-Tagging ──────────────────────────────────

    async def auto_tag_paper(self, document_id: str) -> Dict[str, Any]:
        """Extract meaningful tags from a paper using AI."""
        db = get_db()
        llm = get_llm_service()
        doc = await db.get_document(document_id) if db else None
        if not doc:
            return {"error": "Document not found"}

        text = f"Title: {doc.title}\nAuthors: {', '.join(doc.authors or [])}\nAbstract: {(doc.abstract or '')[:1000]}"

        try:
            resp = await llm.chat_completion(
                messages=[{"role": "user", "content":
                    f"Extract 5-10 meaningful tags for this academic paper. "
                    f"Tags should cover: research area, methodology, key technique, dataset, evaluation metric, application domain. "
                    f"Output as JSON array of strings.\n\n{text}"}],
                system_prompt="You extract standardized academic tags from papers. Use consistent, searchable terms. Output valid JSON.",
            )
            content = resp.get("content", "[]") if isinstance(resp, dict) else str(resp)
            match = re.search(r'\[.*\]', content, re.DOTALL)
            tags = json.loads(match.group()) if match else []

            # Store tags
            meta = doc.doc_metadata or {}
            existing_tags = meta.get("auto_tags", [])
            all_tags = list(set(existing_tags + tags))
            if len(all_tags) > 50:
                all_tags = all_tags[:50]
            meta["auto_tags"] = all_tags
            await db.update_document(document_id, {"doc_metadata": meta, "keywords": all_tags})

            return {"document_id": document_id, "tags": tags, "all_tags": all_tags}

        except Exception as e:
            return {"error": str(e)}

    async def auto_tag_all(self, max_docs: int = 20) -> Dict[str, Any]:
        """Auto-tag all papers that don't have tags yet."""
        db = get_db()
        docs = await db.get_documents(limit=max_docs) if db else []
        results = []
        for doc in docs:
            meta = doc.doc_metadata or {}
            if not meta.get("auto_tags") and not doc.keywords:
                try:
                    result = await self.auto_tag_paper(doc.id)
                    results.append({"id": doc.id, "tags": result.get("tags", [])})
                except Exception: pass
        return {"tagged": len(results), "results": results}

    # ─── 4. Paper Summary Cards ───────────────────────────────

    async def generate_summary_card(self, document_id: str) -> Dict[str, Any]:
        """Generate a structured one-page paper summary card."""
        db = get_db()
        llm = get_llm_service()
        doc = await db.get_document(document_id) if db else None
        if not doc:
            return {"error": "Not found"}

        text = f"Title: {doc.title}\nAuthors: {', '.join(doc.authors or [])}\nYear: {doc.year}\nAbstract: {(doc.abstract or '')[:1500]}"
        if doc.summary:
            text += f"\nSummary: {doc.summary}"

        # Try to get structured card from LLM
        if llm:
            try:
                resp = await llm.chat_completion(
                    messages=[{"role": "user", "content":
                        f"Create a structured summary card for this paper. Output as JSON:\n"
                        f"{{\"one_sentence_summary\": \"...\", \"key_contributions\": [\"...\"], "
                        f"\"methodology\": \"...\", \"main_results\": [\"...\"], "
                        f"\"limitations\": [\"...\"], \"relevance\": \"...\", "
                        f"\"key_figures\": [\"...\"]}}\n\n{text}"}],
                    system_prompt="You create concise, structured paper summaries. Output valid JSON.",
                )
                card = json.loads(re.search(r'\{.*\}', resp.get("content", "{}"), re.DOTALL).group())
            except Exception:
                card = {}
        else:
            card = {}

        return {
            "document_id": document_id,
            "title": doc.title or doc.filename,
            "authors": doc.authors or [],
            "year": doc.year,
            "abstract": (doc.abstract or "")[:300],
            "ai_summary": doc.summary or "",
            "card": card,
        }

    # ─── 5. Reading History ──────────────────────────────────

    async def get_reading_history(self, days: int = 90) -> Dict[str, Any]:
        """Get detailed reading history with analytics."""
        db = get_db()
        if not db:
            return {"error": "DB unavailable"}

        history = {
            "total_days": days,
            "sessions": [],
            "papers_read": [],
            "daily_stats": [],
            "weekly_stats": [],
        }

        # Get reading sessions
        try:
            async with db.async_session_maker() as session:
                from sqlalchemy import text as sa_text
                since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

                sessions = (await session.execute(sa_text(
                    "SELECT date, COUNT(*), SUM(duration_minutes), SUM(pages_read) FROM reading_sessions "
                    "WHERE user_id = 'default' AND date >= :since GROUP BY date ORDER BY date"),
                    {"since": since})).fetchall()

                history["sessions"] = [{
                    "date": s[0], "count": s[1],
                    "minutes": s[2] or 0, "pages": s[3] or 0
                } for s in sessions]

                # Papers marked as read
                read_papers = (await session.execute(sa_text(
                    "SELECT r.document_id, r.date_completed, d.title, d.authors, d.year "
                    "FROM reading_list r LEFT JOIN documents d ON r.document_id = d.id "
                    "WHERE r.user_id = 'default' AND r.status = 'read' "
                    "AND r.date_completed >= :since ORDER BY r.date_completed DESC"),
                    {"since": since})).fetchall()

                history["papers_read"] = [{
                    "id": r[0], "date": str(r[1])[:10] if r[1] else "",
                    "title": r[2] or "Unknown", "authors": json.loads(r[3]) if isinstance(r[3], str) else (r[3] or []),
                    "year": r[4],
                } for r in read_papers]

        except Exception as e:
            logger.warning(f"Reading history error: {e}")

        # Calculate daily and weekly stats
        from collections import defaultdict
        daily = defaultdict(lambda: {"papers": 0, "minutes": 0, "pages": 0})
        for s in history["sessions"]:
            daily[s["date"]]["papers"] += s["count"]
            daily[s["date"]]["minutes"] += s["minutes"]
            daily[s["date"]]["pages"] += s["pages"]

        history["daily_stats"] = [{"date": d, **s} for d, s in sorted(daily.items())]

        weekly = defaultdict(lambda: {"papers": 0, "minutes": 0, "pages": 0})
        from datetime import datetime as dt
        for d, s in daily.items():
            try:
                week = dt.strptime(d, "%Y-%m-%d").strftime("%Y-W%W")
                weekly[week]["papers"] += s["papers"]
                weekly[week]["minutes"] += s["minutes"]
                weekly[week]["pages"] += s["pages"]
            except Exception: pass

        history["weekly_stats"] = [{"week": w, **s} for w, s in sorted(weekly.items())]

        history["totals"] = {
            "reading_sessions": sum(s["count"] for s in history["sessions"]),
            "total_minutes": sum(s["minutes"] for s in history["sessions"]),
            "total_pages": sum(s["pages"] for s in history["sessions"]),
            "papers_read": len(history["papers_read"]),
            "avg_daily_minutes": round(sum(s["minutes"] for s in history["sessions"]) / max(days, 1), 1),
        }

        return history

    # ─── 6. Topic-Based Recommendations ───────────────────────

    async def recommend_by_topic(self, topic: str, exclude_ids: List[str] = None,
                                   max_results: int = 10) -> Dict[str, Any]:
        """Recommend papers by research topic."""
        db = get_db()
        vs = get_vector_service()
        exclude = set(exclude_ids or [])

        if vs:
            results = vs.search_similar(topic, limit=max_results * 2)
        else:
            results = await db.search_documents(topic, limit=max_results * 2) if db else []

        papers = []
        seen = set()
        for r in results:
            did = r.get("document_id", r.get("id", ""))
            if did in exclude or did in seen:
                continue
            seen.add(did)
            doc = await db.get_document(did) if db else None
            if doc:
                papers.append({
                    "id": doc.id, "title": doc.title or doc.filename,
                    "authors": doc.authors or [], "year": doc.year,
                    "abstract": (doc.abstract or "")[:200],
                    "score": r.get("score", 0),
                    "reason": f"Matches topic: {topic}",
                })

        return {"topic": topic, "recommendations": papers[:max_results], "count": len(papers[:max_results])}

    async def recommend_what_to_read_next(self, document_id: str, max_results: int = 5) -> Dict[str, Any]:
        """Recommend papers to read next based on a paper you liked."""
        db = get_db()
        vs = get_vector_service()
        doc = await db.get_document(document_id) if db else None
        if not doc:
            return {"error": "Document not found"}

        text = (doc.abstract or "") + " " + (doc.title or "")

        if vs:
            results = vs.search_similar(text, limit=max_results + 3)
        else:
            results = []

        papers = []
        for r in results:
            did = r.get("document_id")
            if did == document_id:
                continue
            d = await db.get_document(did) if db else None
            if d:
                papers.append({
                    "id": d.id, "title": d.title or d.filename,
                    "authors": d.authors or [], "year": d.year,
                    "score": r.get("score", 0),
                    "reason": "Similar methodology or topic",
                })

        return {
            "based_on": doc.title or doc.filename,
            "recommendations": papers[:max_results],
            "count": len(papers[:max_results]),
        }

    # ─── 7. Citation Context ──────────────────────────────────

    async def get_citation_context(self, citing_doc_id: str, cited_doc_id: str) -> Dict[str, Any]:
        """Find the context around why a paper cites another."""
        db = get_db()
        citing = await db.get_document(citing_doc_id) if db else None
        cited = await db.get_document(cited_doc_id) if db else None

        if not citing or not cited:
            return {"error": "One or both papers not found"}

        # Search for citation in the citing paper's text
        search_terms = []
        if cited.authors:
            for author in cited.authors[:2]:
                parts = author.split(", ")
                search_terms.append(parts[0])  # Last name
        if cited.year:
            search_terms.append(str(cited.year))

        context = ""
        text = (citing.abstract or "") + " " + (citing.summary or "")

        # Find sentences mentioning the cited paper
        sentences = re.split(r'(?<=[.!?])\s+', text)
        relevant = []
        for s in sentences:
            s_lower = s.lower()
            # Check for common citation patterns
            has_citation = any(term.lower() in s_lower for term in search_terms)
            has_bracket = '[' in s and ']' in s
            if has_citation or has_bracket:
                relevant.append(s)

        context = " ".join(relevant[:5]) if relevant else "Citation context not found in available text."

        return {
            "citing_paper": {"id": citing.id, "title": citing.title or citing.filename},
            "cited_paper": {"id": cited.id, "title": cited.title or cited.filename},
            "citation_context": context[:1000],
            "citation_snippets": relevant[:5],
        }

    # ─── 8. Concept Extraction ────────────────────────────────

    async def extract_concepts(self, document_id: str = None, max_docs: int = 20) -> Dict[str, Any]:
        """Extract key concepts across papers and build a concept map."""
        db = get_db()
        llm = get_llm_service()

        if document_id:
            doc = await db.get_document(document_id) if db else None
            docs = [doc] if doc else []
        else:
            docs = await db.get_documents(limit=max_docs) if db else []

        if not docs:
            return {"concepts": [], "error": "No papers"}

        # First pass: extract concepts from each paper
        all_concepts = {}
        for doc in docs:
            text = f"Title: {doc.title}\nAbstract: {(doc.abstract or '')[:500]}"
            if not text.strip():
                continue

            # Use LLM if available
            if llm:
                try:
                    resp = await llm.chat_completion(
                        messages=[{"role": "user", "content":
                            f"Extract key concepts from this paper. Output as JSON array:\n"
                            f"[{{\"concept\": \"transformer\", \"type\": \"architecture\", \"relevance\": 0.9}}]\n\n{text}"}],
                        system_prompt="Extract research concepts with type and relevance score. Output valid JSON array.",
                    )
                    content = resp.get("content", "[]") if isinstance(resp, dict) else str(resp)
                    match = re.search(r'\[.*\]', content, re.DOTALL)
                    concepts = json.loads(match.group()) if match else []
                except Exception:
                    concepts = [{"concept": doc.title or "Untitled", "type": "paper", "relevance": 0.5}]
            else:
                # Keyword-based fallback
                words = re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', text)
                concepts = [{"concept": w, "type": "keyword", "relevance": 0.3} for w in words[:10]]

            for c in concepts:
                name = c.get("concept", "")
                if not name:
                    continue
                if name not in all_concepts:
                    all_concepts[name] = {"concept": name, "type": c.get("type", "concept"), "papers": [], "relevance": 0}
                all_concepts[name]["papers"].append({"id": doc.id, "title": doc.title or doc.filename})
                all_concepts[name]["relevance"] = max(all_concepts[name]["relevance"], c.get("relevance", 0.1))

        # Sort by relevance
        sorted_concepts = sorted(all_concepts.values(), key=lambda x: -x["relevance"] * len(x["papers"]))
        top_concepts = sorted_concepts[:30]

        # Build concept relationships (co-occurrence)
        relationships = []
        for i, c1 in enumerate(top_concepts):
            for c2 in top_concepts[i + 1:]:
                shared = len(set(p["id"] for p in c1["papers"]) & set(p["id"] for p in c2["papers"]))
                if shared > 0:
                    relationships.append({
                        "source": c1["concept"],
                        "target": c2["concept"],
                        "strength": shared,
                    })

        return {
            "concepts": top_concepts,
            "relationships": relationships[:50],
            "total_papers": len(docs),
            "total_concepts": len(all_concepts),
        }

    async def build_concept_graph(self, document_ids: List[str] = None) -> Dict[str, Any]:
        """Build a visual knowledge graph from extracted concepts."""
        result = await self.extract_concepts(max_docs=30)
        concepts = result.get("concepts", [])
        relationships = result.get("relationships", [])

        # Format for D3.js visualization
        nodes = [{"id": c["concept"], "group": c["type"], "size": min(len(c["papers"]) * 5, 50)} for c in concepts[:20]]
        links = [{"source": r["source"], "target": r["target"], "value": r["strength"]} for r in relationships[:30]]

        return {"nodes": nodes, "links": links}


core_intelligence = CoreResearchIntelligence()
