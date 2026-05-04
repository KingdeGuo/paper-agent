"""
Semantic analysis service for cross-paper insight extraction.

Focuses on:
- Contradiction Detection (Paper A says X, Paper B says Y)
- Methodology Comparison
- Hypothesis Generation (Gap Analysis)
"""

import logging
from typing import List, Dict, Any, Optional
from backend.services.llm_service import llm_service
from backend.services.cluster_database import ClusterDatabaseService
from backend.services.vector_service import vector_service

logger = logging.getLogger(__name__)

class SemanticDistillery:
    """Service for deep semantic synthesis across documents."""
    
    def __init__(self, db: ClusterDatabaseService):
        self.db = db

    async def find_contradictions(self, doc_ids: List[str]) -> List[Dict[str, Any]]:
        """Identify conflicting findings across multiple papers."""
        docs = []
        for d_id in doc_ids:
            doc = await self.db.get_document(d_id)
            if doc:
                docs.append(doc)
        
        if len(docs) < 2:
            return []

        # Construct comparative prompt
        prompt = "Compare the findings of the following papers and identify any direct contradictions or significant differences in results/methodologies:\n\n"
        for i, doc in enumerate(docs):
            prompt += f"Paper {i+1}: {doc.title}\nAbstract: {doc.abstract[:1000]}\nSummary: {doc.summary or 'N/A'}\n\n"
        
        prompt += "\nOutput direct contradictions in a JSON list format: [{'point': '...', 'paper1_view': '...', 'paper2_view': '...', 'reasoning': '...'}]"
        
        # Use LLM with reasoning
        response = await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are an expert scientific peer reviewer. Focus on technical contradictions, experimental setup differences, and conflicting conclusions."
        )
        
        # In a real impl, we'd parse the JSON from the CoT output
        # For now, return a placeholder structured result
        return [{"type": "contradiction", "content": response.get("content", "")}]

    async def generate_research_gaps(self, doc_ids: List[str]) -> List[Dict[str, Any]]:
        """Analyze a collection of papers to identify non-obvious research gaps."""
        docs = []
        for d_id in doc_ids:
            doc = await self.db.get_document(d_id)
            if doc:
                docs.append(doc)

        prompt = "As a senior research architect, analyze these papers to find 'semantic voids'—areas where these works almost touch but leave a gap, or where their methodologies could be hybridized to solve an unaddressed problem:\n\n"
        for i, doc in enumerate(docs):
            prompt += f"Paper {i+1} [{doc.year}]: {doc.title}\nKey Findings: {doc.summary or doc.abstract[:500]}\nMethodology: {doc.doc_metadata.get('methodology', 'Standard')}\n\n"
        
        prompt += "\nTask: Generate 3 high-impact research hypotheses. For each, provide:\n1. Title\n2. The specific 'Void' (Gap)\n3. Proposed Hybrid Methodology\n4. Expected Impact."
        
        response = await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are an elite scientific visionary. Avoid obvious suggestions like 'more data' or 'better hardware'. Focus on structural, theoretical, or algorithmic innovations that arise from the intersection of these specific works."
        )
        
        return [{"type": "hypothesis", "content": response.get("content", "")}]

# Note: In a real project, this would be registered in the registry
