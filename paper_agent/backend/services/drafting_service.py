"""
Drafting Service for Paper Agent.

Specialized in generating structured academic content:
- Automated "Related Work" sections (LaTeX compatible)
- Methodology comparisons
- Research proposal drafting
"""

import logging
from typing import Any, Dict, List

from backend.services.cluster_database import ClusterDatabaseService
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class DraftingService:
    """Service for drafting academic text from multiple sources."""

    def __init__(self, db: ClusterDatabaseService, llm: LLMService):
        self.db = db
        self.llm = llm

    async def generate_related_work(self, doc_ids: List[str], focus_topic: str) -> Dict[str, Any]:
        """Generate a LaTeX formatted 'Related Work' section."""
        docs = []
        for d_id in doc_ids:
            doc = await self.db.get_document(d_id)
            if doc:
                docs.append(doc)

        if not docs:
            return {"content": "No documents found to analyze."}

        # Build citations context
        docs_context = ""
        for i, doc in enumerate(docs):
            docs_context += f"Paper {i+1}:\nTitle: {doc.title}\nAuthors: {', '.join(doc.authors)}\nYear: {doc.year}\nSummary: {doc.summary or doc.abstract[:500]}\n\n"

        prompt = (
            f"As a professional researcher, write a structured 'Related Work' section in LaTeX format. "
            f"The focus topic is: '{focus_topic}'.\n\n"
            f"Use the following papers as your primary references:\n{docs_context}\n"
            f"Requirements:\n"
            f"1. Organize by thematic sub-sections.\n"
            f"2. Use \\cite{{AuthorYear}} style citations.\n"
            f"3. Synthesize findings across papers, highlighting how they relate to the focus topic.\n"
            f"4. Provide a concluding paragraph identifying a gap that justify further research."
        )

        response = await self.llm.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a senior academic writer specialized in high-impact journal submissions. Your tone is formal, precise, and analytical."
        )

        return {
            "content": response.get("content", ""),
            "citations_used": [doc.id for doc in docs]
        }

    async def decode_formula(self, formula_latex: str, doc_context: str) -> Dict[str, Any]:
        """Explain a complex mathematical formula in plain language."""
        prompt = (
            f"Explain the following mathematical formula in a way that a first-year graduate student would understand. "
            f"Explain each variable's role and the overall intuition of the expression.\n\n"
            f"Formula: $${formula_latex}$$\n\n"
            f"Document Context: {doc_context[:1000]}"
        )

        response = await self.llm.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are an expert mathematics and physics professor. Break down complex symbols into intuitive concepts."
        )

        return {"explanation": response.get("content", "")}

# Global instances would be registered in the registry
