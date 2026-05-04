"""Tests for GraphRAG engine and re-ranking pipeline."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestRerankingPipeline:
    @pytest.mark.asyncio
    async def test_keyword_scoring(self):
        from paper_agent.backend.services.reranking_service import RerankingPipeline
        pipeline = RerankingPipeline()
        score = await pipeline._keyword_score(
            "transformer attention mechanism",
            "The transformer architecture uses self-attention mechanisms to process sequences."
        )
        assert score > 0, "Should have positive score for matching keywords"
        assert score <= 1.0, "Score should be capped at 1.0"

    @pytest.mark.asyncio
    async def test_keyword_scoring_no_match(self):
        from paper_agent.backend.services.reranking_service import RerankingPipeline
        pipeline = RerankingPipeline()
        score = await pipeline._keyword_score(
            "quantum computing",
            "This paper is about machine learning on images."
        )
        assert score == 0.0, "Should have zero score for no keyword matches"

    @pytest.mark.asyncio
    async def test_keyword_scoring_empty_query(self):
        from paper_agent.backend.services.reranking_service import RerankingPipeline
        pipeline = RerankingPipeline()
        score = await pipeline._keyword_score("", "Some text")
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_rerank_empty_candidates(self):
        from paper_agent.backend.services.reranking_service import RerankingPipeline
        pipeline = RerankingPipeline()
        result = await pipeline.rerank("test query", [], top_k=5)
        assert result == []

    @pytest.mark.asyncio
    async def test_rerank_with_candidates(self):
        from paper_agent.backend.services.reranking_service import RerankingPipeline
        pipeline = RerankingPipeline()
        candidates = [
            {"document_id": "1", "title": "Transformers", "text": "Transformer attention mechanism"},
            {"document_id": "2", "title": "CNN", "text": "Convolutional neural networks for images"},
        ]
        result = await pipeline.rerank("transformer attention", candidates, top_k=2, method="keyword")
        assert len(result) == 2
        assert result[0]["document_id"] == "1"  # More relevant


class TestGraphRAG:
    def test_default_config(self):
        from paper_agent.backend.services.graphrag_service import GraphRAGConfig
        config = GraphRAGConfig()
        assert config.max_depth == 2
        assert config.max_nodes == 50
        assert config.similarity_top_k == 10
        assert config.final_top_k == 8
        assert config.vector_weight + config.edge_weight == 1.0

    @pytest.mark.asyncio
    async def test_retrieve_no_results(self):
        from paper_agent.backend.services.graphrag_service import GraphRAGEngine, GraphRAGConfig

        mock_db = AsyncMock()
        mock_db.get_document = AsyncMock(return_value=None)
        mock_vs = MagicMock()
        mock_vs.search_similar = MagicMock(return_value=[])
        mock_llm = AsyncMock()

        engine = GraphRAGEngine(mock_db, mock_vs, mock_llm, GraphRAGConfig())
        result = await engine.retrieve("test query")
        assert "answer" in result
        assert result["total_sources"] == 0


class TestAgentService:
    def test_agent_registration(self):
        from paper_agent.backend.services.agent_service import (
            AgentOrchestrator, LiteratureReviewAgent, GapAnalysisAgent, WritingAgent
        )
        orch = AgentOrchestrator()
        orch.register_agent(LiteratureReviewAgent())
        orch.register_agent(GapAnalysisAgent())
        orch.register_agent(WritingAgent())
        agents = orch.list_agents()
        assert len(agents) == 3

    def test_agent_card(self):
        from paper_agent.backend.services.agent_service import LiteratureReviewAgent
        agent = LiteratureReviewAgent()
        card = agent.get_agent_card()
        assert card["name"] == "LiteratureReviewAgent"
        assert "literature_review" in card["capabilities"]

    def test_unknown_agent(self):
        from paper_agent.backend.services.agent_service import AgentOrchestrator
        orch = AgentOrchestrator()
        agent = orch.get_agent("NonExistentAgent")
        assert agent is None


class TestDSPyIntegration:
    def test_signatures_defined(self):
        from paper_agent.backend.api.routes.dspy_integration import SIGNATURES
        assert "summarize" in SIGNATURES
        assert "extract_findings" in SIGNATURES
        assert "compare_papers" in SIGNATURES
        assert "identify_gaps" in SIGNATURES
        assert "extract_methodology" in SIGNATURES
        assert len(SIGNATURES) >= 5

    def test_signature_structure(self):
        from paper_agent.backend.api.routes.dspy_integration import SIGNATURES
        for name, sig in SIGNATURES.items():
            assert "description" in sig
            assert "inputs" in sig
            assert "outputs" in sig
            assert "template" in sig


class TestMultiModal:
    def test_extract_elements_structure(self):
        """Test that multi-modal extraction route has proper structure."""
        from paper_agent.backend.api.routes.multi_modal import router
        routes = [r.path for r in router.routes]
        assert "/multimodal/extract/{document_id}" in routes
        assert "/multimodal/extract-batch" in routes
        assert "/multimodal/data-tables/{document_id}" in routes
