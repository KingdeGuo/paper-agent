"""
Research Assistant Bot — multi-platform research assistant.

Inspired by OpenClaw's multi-channel architecture.
Allows researchers to interact with Paper Agent from Telegram, WhatsApp, Slack, etc.

Supports:
- Telegram bot integration
- Slack bot integration
- Generic webhook API for any platform
- Natural language research queries
- Proactive research monitoring (cron-style)
"""

import json
import logging
import httpx
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime

from backend.services.registry import get_db, get_llm_service, get_vector_service
from backend.services.graphrag_service import GraphRAGEngine, GraphRAGConfig

logger = logging.getLogger(__name__)


class BotPlatform(Enum):
    TELEGRAM = "telegram"
    SLACK = "slack"
    GENERIC = "generic"
    WECHAT = "wechat"


class ResearchBot:
    """
    Multi-platform research bot that handles natural language queries
    about the user's research library.
    """

    def __init__(self):
        self.intent_patterns = {
            "search": ["find", "search", "look for", "papers about", "articles about"],
            "summarize": ["summarize", "summary of", "what is", "tell me about"],
            "read": ["what to read", "reading list", "suggest", "recommend"],
            "analyze": ["analyze", "compare", "contrast", "trend", "pattern"],
            "stats": ["stats", "statistics", "how many", "overview", "dashboard"],
            "ask": ["ask", "question", "why", "how does", "what causes"],
            "alert": ["alert", "notify", "watch", "monitor"],
            "help": ["help", "what can you do", "commands", "guide"],
        }

    async def handle_message(self, message: str, platform: BotPlatform = BotPlatform.GENERIC,
                              user_id: str = "default") -> Dict[str, Any]:
        """
        Handle a natural language research query from any platform.
        
        Returns:
            {"reply": "...", "actions": [...], "type": "text|markdown|action"}
        """
        intent = self._detect_intent(message)

        if intent == "help":
            return self._help_response(platform)

        if intent == "stats":
            return await self._handle_stats(user_id)

        if intent == "read":
            return await self._handle_reading_suggestion(user_id)

        # Default: use GraphRAG for deep research question answering
        return await self._handle_research_question(message, user_id)

    def _detect_intent(self, message: str) -> str:
        """Detect user intent from message."""
        msg_lower = message.lower()
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if msg_lower.startswith(pattern) or f" {pattern} " in f" {msg_lower} ":
                    return intent
        return "ask"

    def _help_response(self, platform: BotPlatform) -> Dict:
        """Return help message based on platform."""
        return {
            "reply": (
                "📚 *Paper Agent — Research Assistant*\n\n"
                "I can help you with:\n"
                "• `Find papers about [topic]` — Search your library\n"
                "• `Summarize [paper title]` — Get AI summary\n"
                "• `What should I read?` — Reading suggestions\n"
                "• `Analyze trends` — Research trend analysis\n"
                "• `Stats` — Library statistics\n"
                "• `Ask [question]` — Deep research Q&A\n\n"
                "Try just asking a research question!"
            ),
            "type": "markdown",
            "actions": ["search", "summarize", "read", "analyze", "stats"],
        }

    async def _handle_stats(self, user_id: str) -> Dict:
        """Handle stats intent."""
        db = get_db()
        if not db:
            return {"reply": "Database unavailable.", "type": "text"}

        stats = await db.get_processing_stats() if hasattr(db, 'get_processing_stats') else {}
        reading_stats = {"read": 0, "reading": 0, "to_read": 0}
        try:
            from sqlalchemy import text as sa_text
            async with db.async_session_maker() as session:
                row = (await session.execute(sa_text(
                    "SELECT COUNT(*), SUM(CASE WHEN status='to_read' THEN 1 ELSE 0 END), "
                    "SUM(CASE WHEN status='reading' THEN 1 ELSE 0 END), "
                    "SUM(CASE WHEN status='read' THEN 1 ELSE 0 END) FROM reading_list"
                ))).fetchone()
                if row:
                    reading_stats = {"total": row[0] or 0, "to_read": row[1] or 0,
                                     "reading": row[2] or 0, "read": row[3] or 0}
        except: pass

        reply = (
            f"📊 *Library Statistics*\n\n"
            f"📄 Total papers: {stats.get('total', 0)}\n"
            f"✅ Processed: {stats.get('completed', 0)}\n"
            f"📖 Read: {reading_stats.get('read', 0)}\n"
            f"📖 Reading: {reading_stats.get('reading', 0)}\n"
            f"📋 To read: {reading_stats.get('to_read', 0)}\n"
            f"⚡ Progress: {reading_stats.get('read', 0) / max(reading_stats.get('total', 1), 1) * 100:.0f}%"
        )
        return {"reply": reply, "type": "markdown"}

    async def _handle_reading_suggestion(self, user_id: str) -> Dict:
        """Suggest what to read next."""
        db = get_db()
        vs = get_vector_service()
        if not db:
            return {"reply": "No papers in your library yet. Upload some first!", "type": "text"}

        docs = await db.get_documents(limit=20) if hasattr(db, 'get_documents') else []
        if not docs:
            return {"reply": "Your library is empty. Upload papers to get started!", "type": "text"}

        # Get unread papers
        reading_list_ids = set()
        try:
            from sqlalchemy import text as sa_text
            async with db.async_session_maker() as session:
                rows = (await session.execute(sa_text(
                    "SELECT document_id FROM reading_list WHERE user_id = 'default' AND status IN ('read', 'reading')"))).fetchall()
                reading_list_ids = {r[0] for r in rows}
        except: pass

        unread = [d for d in docs if d.id not in reading_list_ids]
        if not unread:
            unread = docs

        # Pick top 3
        suggestions = unread[:3]
        reply_lines = ["📖 *Reading Suggestions*\n"]
        for i, d in enumerate(suggestions, 1):
            authors = ', '.join((d.authors or [])[:2])
            reply_lines.append(f"{i}. *{d.title or d.filename}*")
            if authors:
                reply_lines.append(f"   by {authors} ({d.year or 'n.d.'})")

        return {"reply": "\n".join(reply_lines), "type": "markdown"}

    async def _handle_research_question(self, question: str, user_id: str) -> Dict:
        """Handle a research question with GraphRAG."""
        db = get_db()
        vs = get_vector_service()
        llm = get_llm_service()

        if not all([db, vs, llm]):
            return {"reply": "Research Q&A requires all services (database, vector search, LLM). Please check your configuration.", "type": "text"}

        try:
            engine = GraphRAGEngine(db, vs, llm, GraphRAGConfig(max_depth=2))
            result = await engine.retrieve(question)

            if result.get("total_sources", 0) == 0:
                return {"reply": f"I searched your library but couldn't find relevant papers for: '{question}'. Try rephrasing or uploading more papers on this topic.", "type": "text"}

            answer = result.get("answer", "")
            sources = result.get("sources", [])
            source_lines = "\n".join(f"• {s.get('title', 'Unknown')} (relevance: {s.get('relevance_score', 0):.2f})" for s in sources[:5])

            reply = f"*Research Answer*\n\n{answer}\n\n📚 *Sources:*\n{source_lines}"
            return {"reply": reply, "type": "markdown"}

        except Exception as e:
            logger.error(f"Bot research question failed: {e}")
            return {"reply": f"Sorry, I encountered an error processing your question: {e}", "type": "text"}

    async def send_to_platform(self, platform: BotPlatform, webhook_url: str,
                                message: str, secret: Optional[str] = None) -> Dict:
        """Send a message to a chat platform."""
        payloads = {
            BotPlatform.TELEGRAM: {"chat_id": None, "text": message, "parse_mode": "Markdown"},
            BotPlatform.SLACK: {"text": message},
            BotPlatform.GENERIC: {"message": message, "source": "paper-agent"},
        }

        payload = payloads.get(platform, payloads[BotPlatform.GENERIC])
        headers = {"Content-Type": "application/json"}
        if secret:
            headers["Authorization"] = f"Bearer {secret}"

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(webhook_url, json=payload, headers=headers)
                return {"success": resp.status_code < 400, "status_code": resp.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global bot instance
research_bot = ResearchBot()
