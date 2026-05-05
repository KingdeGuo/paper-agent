"""Research Agent API — autonomous agents + A2A protocol."""

import logging
from typing import Optional

from backend.services.agent_service import (
    AgentMessage,
    GapAnalysisAgent,
    LiteratureReviewAgent,
    WritingAgent,
    orchestrator,
)
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/agents", summary="List registered agents")
async def list_agents():
    """List all available research agents and their capabilities (A2A discovery)."""
    return {"agents": orchestrator.list_agents(), "count": len(orchestrator.agents)}


@router.get("/agents/{agent_name}", summary="Get agent card")
async def get_agent_card(agent_name: str):
    """Get an agent's capabilities card (A2A agent card)."""
    agent = orchestrator.get_agent(agent_name)
    :
        if not agent:
        return {"error": f"Agent '{agent_name}' not found"}
    return agent.get_agent_card()


@router.post("/agents/delegate", summary="Delegate task to an agent")
async def delegate_task(task: str, payload: dict, preferred_agent: Optional[str] = None):
    """Delegate a research task to the most suitable agent."""
    result = await orchestrator.delegate_task(task, payload, preferred_agent)
    return result


@router.post("/agents/message", summary="Send A2A message")
async def send_message(sender: str, recipient: str, msg_type: str, payload: dict):
    """Send an A2A protocol message between agents."""
    msg = AgentMessage(sender, recipient, msg_type, payload)
    response = await orchestrator.send_message(msg)
    return {
        "message_id": response.id,
        "sender": response.sender,
        "recipient": response.recipient,
        "msg_type": response.msg_type,
        "payload": response.payload,
        "conversation_id": response.conversation_id,
    }


@router.post("/agents/literature-review", summary="Run literature review")
async def run_literature_review(topic: str, max_papers: int = 10, include_graph: bool = False):
    """Run an autonomous literature review on a topic."""
    agent = LiteratureReviewAgent()
    result = await agent.execute_task({
        "topic": topic, "max_papers": max_papers, "include_graph": include_graph,
    })
    return result


@router.post("/agents/gap-analysis", summary="Run gap analysis")
async def run_gap_analysis(topic: str = "", max_papers: int = 15):
    """Run autonomous research gap analysis."""
    agent = GapAnalysisAgent()
    result = await agent.execute_task({"topic": topic, "max_papers": max_papers})
    return result


@router.post("/agents/write-section", summary="Draft a paper section")
async def write_section(section_type: str = "related_work", topic: str = "",
                        style: str = "academic", max_papers: int = 8):
    """Draft an academic paper section with citations."""
    agent = WritingAgent()
    result = await agent.execute_task({
        "section_type": section_type, "topic": topic,
        "style": style, "max_papers": max_papers,
    })
    return result
