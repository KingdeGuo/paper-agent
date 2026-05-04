"""Research Memory API — persistent personalized memory for Paper Agent."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends

from backend.services.memory_service import research_memory

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/memory", summary="Get full research memory")
async def get_memory():
    """Read the full RESEARCH_MEMORY.md."""
    return {
        "memory": research_memory.read_memory(),
        "soul": research_memory.read_soul(),
        "agents": research_memory.read_agents(),
    }


@router.get("/memory/preview", summary="Get memory preview")
async def get_memory_preview():
    """Get a summary preview of memory contents."""
    return research_memory.get_memory_preview()


@router.post("/memory/write", summary="Write to research memory")
async def write_memory(section: str, content: str):
    """Write content to a specific section of RESEARCH_MEMORY.md."""
    success = research_memory.write_to_memory(section, content)
    return {"success": success, "section": section}


@router.post("/memory/daily-note", summary="Write daily note")
async def write_daily_note(content: str, date: Optional[str] = None):
    """Write a daily research note."""
    success = research_memory.write_daily_note(content, date)
    return {"success": success}


@router.get("/memory/daily-note", summary="Read daily note")
async def read_daily_note(date: Optional[str] = None):
    """Read a daily research note."""
    return {"content": research_memory.read_daily_note(date), "date": date or "today"}


@router.get("/memory/search", summary="Search research memory")
async def search_memory(query: str):
    """Search memory for relevant facts."""
    results = research_memory.search_memory(query)
    return {"query": query, "results": results, "count": len(results)}


@router.get("/memory/context", summary="Build memory context prompt")
async def get_memory_context(query: str = ""):
    """Build a memory-aware context prompt for AI injection."""
    context = research_memory.build_context_prompt(query)
    return {"context": context, "length": len(context)}


@router.post("/memory/learn", summary="Learn from interaction")
async def learn_from_interaction(user_message: str, ai_response: str):
    """Auto-learn facts from a user-AI interaction and update memory."""
    result = await research_memory.learn_from_interaction(user_message, ai_response)
    return result


@router.get("/memory/soul", summary="Get research soul")
async def get_soul():
    """Read the RESEARCH_SOUL.md."""
    return {"soul": research_memory.read_soul()}


@router.get("/memory/agents", summary="Get agent instructions")
async def get_agents():
    """Read the AGENTS.md."""
    return {"agents": research_memory.read_agents()}
