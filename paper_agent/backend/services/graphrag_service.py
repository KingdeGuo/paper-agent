"""
GraphRAG Engine — Graph-based Retrieval Augmented Generation.

Combines knowledge graph traversal with vector search for deeper,
context-aware retrieval. Instead of flat vector search, traverses
citation links, author connections, and semantic relationships.

Reference: Microsoft GraphRAG (github.com/microsoft/graphrag)
"""

import json
import logging
import asyncio
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from backend.services.registry import get_db, get_vector_service, get_llm_service
from backend.services.cluster_database import ClusterDatabaseService
from backend.services.vector_service import VectorService
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)


@dataclass
class GraphRAGConfig:
    max_depth: int = 2          # Citation graph traversal depth
    max_nodes: int = 50          # Max nodes to explore
    similarity_top_k: int = 10   # Initial vector search results
    final_top_k: int = 8         # Final results after graph expansion
    edge_weight: float = 0.3     # Weight for graph-based scores
    vector_weight: float = 0.7   # Weight for vector search scores


class GraphRAGEngine:
    """Graph-based RAG using citation networks and semantic relationships."""

    def __init__(self, db, vector_service, llm_service, config: Optional[GraphRAGConfig] = None):
        self.db = db
        self.vs = vector_service
        self.llm = llm_service
        self.config = config or GraphRAGConfig()

    async def retrieve(self, query: str, doc_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Retrieve context using GraphRAG: vector search + graph traversal + LLM synthesis.
        
        Returns:
            {
                "answer": "...",
                "sources": [...],
                "graph_traversed": [...],
                "reasoning_path": "..."
            }
        """
        # Phase 1: Initial vector search
        vector_results = self.vs.search_similar(query, limit=self.config.similarity_top_k) if self.vs else []
        if not vector_results and self.db:
            docs = await self.db.search_documents(query, limit=self.config.similarity_top_k) if hasattr(self.db, 'search_documents') else []
            vector_results = [{"document_id": d.id, "title": d.title, "score": 0.5, "text": d.abstract or ""} for d in docs]

        if not vector_results:
            return {"answer": "No relevant papers found.", "sources": [], "graph_traversed": []}

        # Phase 2: Graph traversal — expand via citations and semantic links
        seed_ids = [r["document_id"] for r in vector_results[:5] if r.get("document_id")]
        graph_nodes = await self._traverse_graph(seed_ids, query)

        # Phase 3: Score and rank combining vector + graph signals
        combined = await self._rank_results(vector_results, graph_nodes, query)

        # Phase 4: Build context and generate answer
        answer, sources = await self._synthesize(query, combined)

        return {
            "answer": answer,
            "sources": sources,
            "graph_traversed": [{"id": n["id"], "title": n["title"], "depth": n["depth"]} for n in graph_nodes],
            "total_sources": len(sources),
            "graph_nodes_explored": len(graph_nodes),
        }

    async def _traverse_graph(self, seed_ids: List[str], query: str) -> List[Dict]:
        """Traverse citation/semantic graph from seed papers."""
        visited = set(seed_ids)
        frontier = set(seed_ids)
        nodes = []
        depth = 0

        while frontier and depth < self.config.max_depth and len(visited) < self.config.max_nodes:
            depth += 1
            next_frontier = set()

            for doc_id in frontier:
                doc = await self.db.get_document(doc_id) if self.db else None
                if not doc:
                    continue

                nodes.append({
                    "id": doc.id, "title": doc.title or doc.filename,
                    "authors": doc.authors or [], "year": doc.year,
                    "depth": depth, "keywords": doc.keywords or [],
                })

                # Find semantically similar papers (acts as "citations")
                if self.vs and doc.abstract:
                    similar = self.vs.search_similar(doc.abstract, limit=5)
                    for s in similar:
                        sid = s.get("document_id")
                        if sid and sid not in visited:
                            visited.add(sid)
                            next_frontier.add(sid)

                # Find papers with shared keywords
                if doc.keywords:
                    for kw in doc.keywords[:3]:
                        if self.vs:
                            kw_results = self.vs.search_similar(kw, limit=3)
                            for r in kw_results:
                                rid = r.get("document_id")
                                if rid and rid not in visited:
                                    visited.add(rid)
                                    next_frontier.add(rid)

            frontier = next_frontier

        return nodes

    async def _rank_results(self, vector_results: List[Dict], graph_nodes: List[Dict], query: str) -> List[Dict]:
        """Combine vector and graph signals with scoring."""
        # Build graph scores
        graph_scores = defaultdict(float)
        for n in graph_nodes:
            nid = n["id"]
            # Papers found earlier in traversal = more relevant
            depth_score = 1.0 / (n.get("depth", 2) + 0.5)
            # Papers with matching keywords get bonus
            keyword_bonus = 0
            if n.get("keywords"):
                q_words = set(query.lower().split())
                kw_words = set(k.lower() for k in n["keywords"])
                overlap = len(q_words & kw_words)
                keyword_bonus = overlap * 0.1
            graph_scores[nid] = depth_score + keyword_bonus

        # Combine scores
        combined = {}
        for r in vector_results:
            did = r.get("document_id", r.get("id", ""))
            vec_score = r.get("score", 0.5)
            graph_score = graph_scores.get(did, 0)
            total = (self.config.vector_weight * vec_score) + (self.config.edge_weight * graph_score)
            combined[did] = {
                "document_id": did,
                "title": r.get("title", ""),
                "text": r.get("text", ""),
                "vector_score": vec_score,
                "graph_score": graph_score,
                "final_score": total,
                "in_graph": did in graph_scores,
            }

        # Add pure graph nodes not found by vector search
        for n in graph_nodes:
            nid = n["id"]
            if nid not in combined:
                combined[nid] = {
                    "document_id": nid,
                    "title": n["title"],
                    "text": "",
                    "vector_score": 0,
                    "graph_score": graph_scores.get(nid, 0),
                    "final_score": self.config.edge_weight * graph_scores.get(nid, 0),
                    "in_graph": True,
                }

        # Sort and return top
        results = sorted(combined.values(), key=lambda x: -x["final_score"])
        return results[:self.config.final_top_k]

    async def _synthesize(self, query: str, ranked: List[Dict]) -> Tuple[str, List[Dict]]:
        """Synthesize final answer with citations from ranked results."""
        if not ranked:
            return "No relevant sources found.", []

        sources = []
        context_parts = []

        for i, r in enumerate(ranked):
            did = r["document_id"]
            doc = await self.db.get_document(did) if self.db else None
            if not doc:
                continue

            title = doc.title or doc.filename
            text = r.get("text") or doc.abstract or ""
            if not text:
                continue

            tag = f"[{i+1}]"
            context_parts.append(f"{tag} {title}: {text[:600]}")
            sources.append({
                "document_id": did, "title": title,
                "authors": doc.authors or [],
                "year": doc.year,
                "relevance_score": r["final_score"],
                "in_graph": r.get("in_graph", False),
            })

        if not context_parts:
            return "Sources found but no extractable text.", sources

        context = "\n\n".join(context_parts)
        system_prompt = (
            "You are a research assistant using GraphRAG (graph-based retrieval). "
            "Answer based ONLY on the provided sources. Cite using [1], [2], etc. "
            "If sources contradict, note the contradiction. Be precise and thorough."
        )

        try:
            response = await self.llm.chat_completion(
                messages=[{"role": "user", "content": f"Based on these papers:\n\n{context}\n\nQuestion: {query}"}],
                system_prompt=system_prompt,
            )
            answer = response.get("content", "") if isinstance(response, dict) else str(response)
        except Exception as e:
            answer = f"AI synthesis unavailable: {e}"

        return answer, sources

    async def query(self, question: str) -> Dict[str, Any]:
        """High-level query interface."""
        return await self.retrieve(question)


class GraphRAGCommunityDetector:
    """Detect research communities and topics using graph clustering."""

    async def detect_communities(self, db) -> List[Dict]:
        """Identify research communities in the library based on citation patterns."""
        docs = await db.get_documents(limit=200) if db else []
        if len(docs) < 5:
            return []

        # Build co-author graph
        author_papers = defaultdict(list)
        for d in docs:
            for a in (d.authors or []):
                author_papers[a].append(d.id)

        # Find communities via shared keywords
        keyword_docs = defaultdict(list)
        for d in docs:
            for kw in (d.keywords or []):
                keyword_docs[kw].append(d.id)

        communities = []
        for kw, paper_ids in sorted(keyword_docs.items(), key=lambda x: -len(x[1]))[:10]:
            if len(paper_ids) >= 2:
                members = []
                for pid in paper_ids[:5]:
                    doc = await db.get_document(pid) if db else None
                    if doc:
                        members.append({"id": pid, "title": doc.title or doc.filename})
                communities.append({
                    "topic": kw,
                    "size": len(paper_ids),
                    "members": members,
                    "type": "keyword_cluster",
                })

        # Author-based communities
        for author, paper_ids in sorted(author_papers.items(), key=lambda x: -len(x[1]))[:10]:
            if len(paper_ids) >= 3:
                members = []
                for pid in paper_ids[:5]:
                    doc = await db.get_document(pid) if db else None
                    if doc:
                        members.append({"id": pid, "title": doc.title or doc.filename})
                communities.append({
                    "topic": f"{author}'s Network",
                    "size": len(paper_ids),
                    "members": members,
                    "type": "author_network",
                    "author": author,
                })

        return communities[:15]
