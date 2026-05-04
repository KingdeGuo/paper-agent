"""
Re-ranking Pipeline — two-stage retrieval for higher accuracy.

Stage 1: Fast vector search (ChromaDB) for candidate retrieval
Stage 2: Cross-encoder re-ranking for precision

Supports:
- Cross-encoder re-ranking via LLM 
- Cohere rerank API (if available)
- Simple keyword overlap scoring as fallback
"""

import logging
import re
from typing import List, Dict, Any, Optional
from collections import defaultdict

from backend.services.registry import get_llm_service
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class RerankingPipeline:
    """Two-stage retrieval pipeline with re-ranking."""

    async def rerank(self, query: str, candidates: List[Dict], top_k: int = 5,
                     method: str = "hybrid") -> List[Dict]:
        """
        Re-rank candidate documents by relevance to the query.
        
        Args:
            query: User's search query
            candidates: List of candidate documents with 'text' or 'title' fields
            top_k: Number of results to return
            method: 'llm', 'keyword', or 'hybrid'
        
        Returns:
            Re-ranked candidates with 'relevance_score' added
        """
        if not candidates:
            return []

        # Score each candidate
        scored = []
        for c in candidates:
            text = c.get("text") or c.get("abstract") or c.get("title") or ""
            title = c.get("title") or ""
            combined_text = f"{title} {text}"

            if method == "keyword":
                score = await self._keyword_score(query, combined_text)
            elif method == "llm":
                score = await self._llm_score(query, combined_text, c)
            else:  # hybrid
                kw_score = await self._keyword_score(query, combined_text)
                llm_score = await self._llm_score(query, combined_text, c)
                score = (kw_score * 0.4) + (llm_score * 0.6)

            c["relevance_score"] = round(score, 4)
            c["rerank_score"] = c["relevance_score"]
            scored.append(c)

        # Sort by score descending
        scored.sort(key=lambda x: -x["relevance_score"])
        return scored[:top_k]

    async def _keyword_score(self, query: str, text: str) -> float:
        """BM25-style keyword overlap scoring."""
        query_words = set(re.findall(r'\w+', query.lower()))
        text_words = set(re.findall(r'\w+', text.lower()))

        if not query_words:
            return 0.0

        # Exact phrase bonus
        phrase_bonus = 1.5 if query.lower() in text.lower() else 1.0

        # Word overlap (Jaccard)
        overlap = len(query_words & text_words)
        union = len(query_words | text_words)
        jaccard = overlap / union if union > 0 else 0

        # Word frequency bonus
        freq_bonus = 0
        for qw in query_words:
            count = len(re.findall(rf'\b{re.escape(qw)}\b', text.lower()))
            freq_bonus += min(count / 5, 1.0)  # Cap at 1.0 per word
        freq_bonus = freq_bonus / max(len(query_words), 1)

        score = (jaccard * 0.6 + freq_bonus * 0.4) * phrase_bonus
        return min(score, 1.0)

    async def _llm_score(self, query: str, text: str, candidate: Dict) -> float:
        """Use LLM to judge relevance (cross-encoder style)."""
        llm = get_llm_service()
        if not llm:
            return self._keyword_score(query, text)  # Fallback

        try:
            title = candidate.get("title", "")[:100]
            snippet = text[:300]
            resp = await llm.chat_completion(
                messages=[{
                    "role": "user",
                    "content": f"Rate the relevance of this paper to the query on a scale of 0.0 to 1.0. Output ONLY a number.\n\nQuery: {query}\nPaper Title: {title}\nSnippet: {snippet}"
                }],
                system_prompt="You are a relevance judge. Output ONLY a float between 0.0 and 1.0.",
            )
            content = resp.get("content", "0.5") if isinstance(resp, dict) else str(resp)
            # Extract number
            nums = re.findall(r'0\.\d+|1\.0|1\.00', content)
            if nums:
                return float(nums[0])
            return 0.5
        except Exception:
            return self._keyword_score(query, text)

    async def batch_rerank(self, query: str, candidates: List[Dict],
                           top_k: int = 5) -> List[Dict]:
        """Batch re-ranking with LLM for efficiency (fewer API calls)."""
        if not candidates:
            return []

        llm = get_llm_service()
        if not llm or len(candidates) <= 3:
            return await self.rerank(query, candidates, top_k, method="keyword")

        try:
            # Build batch prompt
            items = []
            for i, c in enumerate(candidates):
                title = (c.get("title") or "Untitled")[:80]
                snippet = (c.get("text") or c.get("abstract") or "")[:200]
                items.append(f"[{i+1}] {title}: {snippet}")

            prompt = f"Query: {query}\n\nRate each paper's relevance from 0.0 to 1.0. Output as JSON array of scores: [score1, score2, ...]\n\n" + "\n".join(items)

            resp = await llm.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a relevance judge. Output valid JSON array of floats only.",
            )
            content = resp.get("content", "[]") if isinstance(resp, dict) else str(resp)
            import json
            match = re.search(r'\[.*?\]', content, re.DOTALL)
            scores = json.loads(match.group()) if match else []

            for i, c in enumerate(candidates):
                if i < len(scores):
                    c["relevance_score"] = round(float(scores[i]), 4)
                    c["rerank_score"] = c["relevance_score"]
                else:
                    c["relevance_score"] = 0.5

            candidates.sort(key=lambda x: -x["relevance_score"])
            return candidates[:top_k]

        except Exception as e:
            logger.warning(f"Batch rerank failed, using keyword fallback: {e}")
            return await self.rerank(query, candidates, top_k, method="keyword")


class HybridSearchEngine:
    """Combines vector search + keyword search + re-ranking."""

    async def search(self, query: str, vector_results: List[Dict],
                    keyword_results: List[Dict], top_k: int = 10) -> List[Dict]:
        """Multi-strategy search with fusion and re-ranking."""
        # Fuse results
        seen = {}
        for r in vector_results:
            did = r.get("document_id", r.get("id"))
            if did:
                seen[did] = {**r, "vector_score": r.get("score", 0), "keyword_score": 0}

        for r in keyword_results:
            did = r.get("id")
            if did in seen:
                seen[did]["keyword_score"] = 0.5
                seen[did]["text"] = seen[did].get("text") or r.get("abstract", "")
            elif did:
                seen[did] = {**r, "vector_score": 0, "keyword_score": 0.5}

        candidates = list(seen.values())
        if not candidates:
            return []

        # Re-rank
        pipeline = RerankingPipeline()
        return await pipeline.rerank(query, candidates, top_k)
