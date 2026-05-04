"""
Research Agent System — autonomous agents for literature tasks.

Supports:
- Literature Review Agent: Independent literature survey execution
- Gap Analysis Agent: Research gap identification
- Writing Agent: Draft generation with citations
- A2A Protocol: Agent-to-Agent messaging

Reference: Google A2A (Agent-to-Agent) protocol concept
"""

import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from enum import Enum

from backend.services.registry import get_db, get_vector_service, get_llm_service
from backend.services.llm_service import LLMService
from backend.services.graphrag_service import GraphRAGEngine, GraphRAGConfig

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"  # Waiting for another agent (A2A)


class AgentMessage:
    """A2A protocol message between agents."""

    def __init__(self, sender: str, recipient: str, msg_type: str,
                 payload: Dict, conversation_id: Optional[str] = None):
        self.id = str(uuid.uuid4())
        self.sender = sender
        self.recipient = recipient
        self.msg_type = msg_type  # request, response, error, progress
        self.payload = payload
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat()


class ResearchAgent:
    """Base class for autonomous research agents."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.status = AgentStatus.IDLE
        self.capabilities = []
        self.conversations = {}  # conversation_id -> [messages]

    async def process_message(self, msg: AgentMessage) -> AgentMessage:
        """Handle an incoming A2A message."""
        if msg.msg_type == "request":
            result = await self.execute_task(msg.payload)
            return AgentMessage(
                sender=self.name,
                recipient=msg.sender,
                msg_type="response",
                payload=result,
                conversation_id=msg.conversation_id,
            )
        elif msg.msg_type == "response":
            # Store response for the calling agent
            if msg.conversation_id not in self.conversations:
                self.conversations[msg.conversation_id] = []
            self.conversations[msg.conversation_id].append(msg)
            return AgentMessage(
                sender=self.name, recipient=msg.sender,
                msg_type="response",
                payload={"status": "received", "message_id": msg.id},
                conversation_id=msg.conversation_id,
            )
        return AgentMessage(
            sender=self.name, recipient=msg.sender,
            msg_type="error", payload={"error": f"Unknown message type: {msg.msg_type}"},
        )

    async def execute_task(self, payload: Dict) -> Dict:
        """Execute a task — override in subclass."""
        raise NotImplementedError

    def get_agent_card(self) -> Dict:
        """A2A agent card for discovery."""
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "status": self.status.value,
            "version": "1.0",
            "protocol": "a2a",
        }


class LiteratureReviewAgent(ResearchAgent):
    """Autonomous literature review agent."""

    def __init__(self):
        super().__init__(
            name="LiteratureReviewAgent",
            description="Conducts autonomous literature reviews. Searches, analyzes, and synthesizes papers on any topic."
        )
        self.capabilities = [
            "literature_review",
            "topic_summary",
            "paper_discovery",
            "citation_analysis",
            "trend_identification",
        ]

    async def execute_task(self, payload: Dict) -> Dict:
        """Execute a literature review task."""
        self.status = AgentStatus.RUNNING
        topic = payload.get("topic", "")
        depth = payload.get("depth", "moderate")
        max_papers = payload.get("max_papers", 10)
        include_graph = payload.get("include_graph", False)

        db = get_db()
        vs = get_vector_service()
        llm = get_llm_service()

        if not topic:
            self.status = AgentStatus.FAILED
            return {"error": "No topic specified"}

        try:
            # Phase 1: Search for papers
            papers_found = []
            if vs:
                results = vs.search_similar(topic, limit=max_papers * 2)
                for r in results:
                    did = r.get("document_id")
                    doc = await db.get_document(did) if db and did else None
                    if doc:
                        papers_found.append({
                            "id": doc.id, "title": doc.title or doc.filename,
                            "authors": doc.authors or [], "year": doc.year,
                            "abstract": (doc.abstract or "")[:300],
                            "summary": doc.summary or "",
                            "score": r.get("score", 0),
                        })
            else:
                docs = await db.get_documents(limit=max_papers) if db else []
                for d in docs:
                    papers_found.append({
                        "id": d.id, "title": d.title or d.filename,
                        "authors": d.authors or [], "year": d.year,
                        "abstract": (d.abstract or "")[:300],
                        "summary": d.summary or "", "score": 0.5,
                    })

            # Phase 2: GraphRAG exploration
            graph_insights = ""
            if include_graph and llm and vs:
                graph_engine = GraphRAGEngine(db, vs, llm, GraphRAGConfig(max_depth=2))
                graph_result = await graph_engine.retrieve(topic)
                graph_insights = graph_result.get("answer", "")

            # Phase 3: AI synthesis
            synthesis = ""
            if llm and papers_found:
                paper_list = "\n".join(
                    f"- {p['title']} ({p['year']}) - {', '.join(p['authors'][:3])}: {p['abstract'][:200]}"
                    for p in papers_found[:max_papers]
                )
                resp = await llm.chat_completion(
                    messages=[{
                        "role": "user",
                        "content": f"Conduct a literature review on '{topic}' based on these papers:\n\n{paper_list}\n\nProvide:\n1. Key themes and findings\n2. Methodological approaches\n3. Research gaps\n4. Future directions\n\nCite papers by title."
                    }],
                    system_prompt="You are an expert literature review agent. Be thorough and well-structured.",
                )
                synthesis = resp.get("content", "") if isinstance(resp, dict) else str(resp)

            self.status = AgentStatus.COMPLETED
            return {
                "topic": topic,
                "papers_reviewed": len(papers_found[:max_papers]),
                "papers": papers_found[:max_papers],
                "synthesis": synthesis,
                "graph_insights": graph_insights if include_graph else None,
                "depth": depth,
                "completed_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.status = AgentStatus.FAILED
            return {"error": str(e), "topic": topic}


class GapAnalysisAgent(ResearchAgent):
    """Identifies research gaps and generates novel hypotheses."""

    def __init__(self):
        super().__init__(
            name="GapAnalysisAgent",
            description="Analyzes research gaps, contradictions, and generates novel hypotheses."
        )
        self.capabilities = ["gap_analysis", "contradiction_detection", "hypothesis_generation", "research_directions"]

    async def execute_task(self, payload: Dict) -> Dict:
        self.status = AgentStatus.RUNNING
        topic = payload.get("topic", "")
        max_papers = payload.get("max_papers", 15)

        db = get_db()
        llm = get_llm_service()
        if not llm:
            self.status = AgentStatus.FAILED
            return {"error": "LLM service required"}

        docs = await db.get_documents(limit=max_papers) if db else []
        doc_texts = "\n".join(f"- {d.title} ({d.year}): {(d.abstract or '')[:200]}" for d in docs[:max_papers])

        try:
            resp = await llm.chat_completion(
                messages=[{"role": "user", "content": f"Analyze these papers on '{topic or 'the library topics'}' and identify:\n1. Research gaps (underexplored areas)\n2. Contradictions (conflicting findings)\n3. Novel research hypotheses\n\nPapers:\n{doc_texts}"}],
                system_prompt="You are a senior research strategist. Identify non-obvious gaps and generate high-impact hypotheses.",
            )
            analysis = resp.get("content", "") if isinstance(resp, dict) else str(resp)
            self.status = AgentStatus.COMPLETED
            return {"topic": topic, "papers_analyzed": len(docs), "analysis": analysis}
        except Exception as e:
            self.status = AgentStatus.FAILED
            return {"error": str(e)}


class WritingAgent(ResearchAgent):
    """Drafts academic text with proper citations."""

    def __init__(self):
        super().__init__(
            name="WritingAgent",
            description="Drafts academic writing with automatic citation support."
        )
        self.capabilities = ["draft_section", "abstract_generation", "citation_formatting", "related_work"]

    async def execute_task(self, payload: Dict) -> Dict:
        self.status = AgentStatus.RUNNING
        section_type = payload.get("section_type", "related_work")
        topic = payload.get("topic", "")
        style = payload.get("style", "academic")
        max_papers = payload.get("max_papers", 8)

        db = get_db()
        llm = get_llm_service()
        vs = get_vector_service()

        # Get relevant papers
        if vs:
            results = vs.search_similar(topic, limit=max_papers)
        else:
            results = await db.search_documents(topic, limit=max_papers) if db else []

        papers = []
        for r in results:
            did = r.get("document_id", r.get("id", ""))
            doc = await db.get_document(did) if db and did else None
            if doc:
                papers.append(f"[{len(papers)+1}] {doc.title} ({doc.year}) - {', '.join(doc.authors or [])[:50]}: {(doc.summary or doc.abstract or '')[:300]}")

        if not papers:
            self.status = AgentStatus.COMPLETED
            return {"section": "", "message": "No relevant papers found."}

        paper_list = "\n".join(papers)
        prompts = {
            "related_work": f"Write a 'Related Work' section on '{topic}' citing these papers:\n\n{paper_list}",
            "abstract": f"Write an abstract for a paper on '{topic}' based on these related works:\n\n{paper_list}",
            "introduction": f"Write an introduction section for a paper on '{topic}' that motivates the research:\n\n{paper_list}",
            "discussion": f"Write a discussion section comparing findings across these papers:\n\n{paper_list}",
        }
        prompt = prompts.get(section_type, prompts["related_work"])

        try:
            resp = await llm.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=f"You are an academic writing assistant. Write in {style} style. Use [1], [2] citations.",
            )
            section = resp.get("content", "") if isinstance(resp, dict) else str(resp)
            self.status = AgentStatus.COMPLETED
            return {"section_type": section_type, "topic": topic, "content": section, "papers_cited": len(papers)}
        except Exception as e:
            self.status = AgentStatus.FAILED
            return {"error": str(e)}


class AgentOrchestrator:
    """
    A2A Protocol orchestrator — routes tasks between agents.
    Supports agent discovery, messaging, and delegation.
    """

    def __init__(self):
        self.agents = {}

    def register_agent(self, agent: ResearchAgent):
        self.agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name}")

    def get_agent(self, name: str) -> Optional[ResearchAgent]:
        return self.agents.get(name)

    def list_agents(self) -> List[Dict]:
        return [a.get_agent_card() for a in self.agents.values()]

    async def send_message(self, msg: AgentMessage) -> AgentMessage:
        """Send an A2A message to an agent."""
        agent = self.get_agent(msg.recipient)
        if not agent:
            return AgentMessage(
                sender="orchestrator", recipient=msg.sender,
                msg_type="error", payload={"error": f"Agent '{msg.recipient}' not found"},
                conversation_id=msg.conversation_id,
            )
        return await agent.process_message(msg)

    async def delegate_task(self, task: str, payload: Dict,
                            preferred_agent: str = None) -> Dict:
        """Delegate a task to the most suitable agent."""
        if preferred_agent and preferred_agent in self.agents:
            msg = AgentMessage("orchestrator", preferred_agent, "request", payload)
            response = await self.send_message(msg)
            return response.payload

        # Auto-select agent based on task
        task_map = {
            "literature_review": "LiteratureReviewAgent",
            "gap_analysis": "GapAnalysisAgent",
            "writing": "WritingAgent",
        }
        agent_name = task_map.get(task)
        if agent_name and agent_name in self.agents:
            msg = AgentMessage("orchestrator", agent_name, "request", payload)
            response = await self.send_message(msg)
            return response.payload

        return {"error": f"No suitable agent for task: {task}"}


# Global orchestrator (singleton — prevents duplicate registration on reimport)
import sys as _sys
_orch_module_key = 'paper_agent.backend.services.agent_service.orchestrator'

if _orch_module_key not in _sys.modules:
    orchestrator = AgentOrchestrator()
    orchestrator.register_agent(LiteratureReviewAgent())
    orchestrator.register_agent(GapAnalysisAgent())
    orchestrator.register_agent(WritingAgent())
    _sys.modules[_orch_module_key] = orchestrator
else:
    orchestrator = _sys.modules[_orch_module_key]
