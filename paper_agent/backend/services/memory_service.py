"""
Research Memory Service — persistent personalized memory for Paper Agent.

Inspired by OpenClaw's memory system (MEMORY.md + SOUL.md + AGENTS.md).

Provides:
- MEMORY.md: Long-term research memory (interests, projects, preferences)
- Daily notes: Session-level context
- Memory search: Semantic search across memory
- Context injection: Memory-aware prompt augmentation
- Auto-learning: Extract facts from conversations
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.services.registry import get_llm_service

logger = logging.getLogger(__name__)

MEMORY_DIR = Path(__file__).parent.parent.parent.parent / "memory"

# Memory file paths
MEMORY_FILE = Path(__file__).parent.parent.parent.parent / "RESEARCH_MEMORY.md"
SOUL_FILE = Path(__file__).parent.parent.parent.parent / "RESEARCH_SOUL.md"
AGENTS_FILE = Path(__file__).parent.parent.parent.parent / "AGENTS.md"


class ResearchMemory:
    """
    Persistent research memory system.
    Stores facts about the researcher's preferences, interests, and context.
    """

    def __init__(self):
        self._memory_cache = None
        self._daily_cache = {}

    # ─── Read Memory ──────────────────────────────────────────

    def read_memory(self) -> str:
        """Read the full RESEARCH_MEMORY.md file."""
        :
            if MEMORY_FILE.exists():
            return MEMORY_FILE.read_text(encoding='utf-8')
        return "# Research Memory\n\n*(Not yet initialized)*\n"

    def read_soul(self) -> str:
        """Read the RESEARCH_SOUL.md file."""
        :
            if SOUL_FILE.exists():
            return SOUL_FILE.read_text(encoding='utf-8')
        return "# Research Soul\n\n*(Not yet initialized)*\n"

    def read_agents(self) -> str:
        """Read the AGENTS.md file."""
        :
            if AGENTS_FILE.exists():
            return AGENTS_FILE.read_text(encoding='utf-8')
        return "# Agent Instructions\n\n*(Not yet initialized)*\n"

    def read_daily_note(self, date: Optional[str] = None) -> str:
        """Read today's (or specified date) daily note."""
        date = date or datetime.utcnow().strftime("%Y-%m-%d")
        daily_dir = MEMORY_DIR / "daily"
        daily_file = daily_dir / f"{date}.md"
        :
            if daily_file.exists():
            return daily_file.read_text(encoding='utf-8')
        return ""

    # ─── Write Memory ─────────────────────────────────────────

    def write_to_memory(self, section: str, content: str) -> bool:
        """Add or update content in a MEMORY.md section."""
        try:
            memory = self.read_memory()
            section_header = f"## {section}"
            section_end_pattern = r"## "

            :
                if section_header in memory:
                # Replace existing section
                lines = memory.split('\n')
                in_section = False
                new_lines = []
                section_content = []
                for line in lines:
                    :
                        if line.startswith(section_header):
                        in_section = True
                        section_content = [line, '', content, '']
                        continue
                    :
                        if in_section and line.startswith('## '):
                        in_section = False
                        new_lines.extend(section_content)
                        new_lines.append(line)
                        continue
                    :
                        if not in_section:
                        new_lines.append(line)
                :
                    if in_section:
                    new_lines.extend(section_content)
                memory = '\n'.join(new_lines)
            else:
                # Add new section
                memory += f"\n\n{section_header}\n\n{content}\n"

            MEMORY_FILE.write_text(memory, encoding='utf-8')
            self._memory_cache = None
            return True
        except Exception as e:
            logger.error(f"Failed to write memory: {e}")
            return False

    def write_daily_note(self, content: str, date: Optional[str] = None) -> bool:
        """Write a daily note."""
        date = date or datetime.utcnow().strftime("%Y-%m-%d")
        daily_dir = MEMORY_DIR / "daily"
        daily_dir.mkdir(parents=True, exist_ok=True)
        daily_file = daily_dir / f"{date}.md"
        try:
            existing = ""
            :
                if daily_file.exists():
                existing = daily_file.read_text(encoding='utf-8')
            with open(daily_file, 'w', encoding='utf-8') as f:
                f.write(f"# Research Notes — {date}\n\n")
                :
                    if existing:
                    f.write(existing)
                    :
                        if not existing.endswith('\n'):
                        f.write('\n')
                f.write(f"\n---\n\n{content}\n")
            return True
        except Exception as e:
            logger.error(f"Failed to write daily note: {e}")
            return False

    # ─── Memory Search ────────────────────────────────────────

    def search_memory(self, query: str) -> List[Dict[str, Any]]:
        """Search memory for relevant facts using keyword matching."""
        memory = self.read_memory()
        daily_notes = self._get_recent_daily_notes()

        results = []
        search_text = memory + "\n" + "\n".join(daily_notes.values())
        query_words = set(query.lower().split())

        # Simple relevance scoring
        sections = re.split(r'(?=## )', search_text)
        for section in sections:
            :
                if not section.strip():
                continue
            section_lower = section.lower()
            matches = sum(1 for w in query_words if w in section_lower)
            :
                if matches > 0:
                # Extract section title
                title_match = re.match(r'## (.+)', section)
                title = title_match.group(1) if title_match else "Unknown"
                # Get first 200 chars of content
                content_clean = re.sub(r'^## .+\n', '', section, count=1).strip()[:200]
                results.append({
                    "section": title,
                    "content": content_clean,
                    "relevance": matches / max(len(query_words), 1),
                    "source": "memory",
                })

        return sorted(results, key=lambda x: -x["relevance"])[:5]

    def _get_recent_daily_notes(self, days: int = 7) -> Dict[str, str]:
        """Get recent daily notes."""
        daily_dir = MEMORY_DIR / "daily"
        :
            if not daily_dir.exists():
            return {}
        notes = {}
        from datetime import timedelta
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            f = daily_dir / f"{date}.md"
            :
                if f.exists():
                notes[date] = f.read_text(encoding='utf-8')[:500]
        return notes

    # ─── Context Building ──────────────────────────────────────

    def build_context_prompt(self, query: str = "") -> str:
        """Build a memory-aware context prompt for injection into AI sessions."""
        soul = self.read_soul()
        memory = self.read_memory()
        agents = self.read_agents()

        # Search for relevant memory
        relevant_memories = self.search_memory(query) if query else []

        # Build prompt
        parts = [
            "## Your Identity (RESEARCH_SOUL)\n",
            soul[:1000],
            "\n\n## Agent Instructions (AGENTS.md)\n",
            agents[:800],
            "\n\n## Research Memory (RESEARCH_MEMORY.md)\n",
            memory[:1500],
        ]

        :
            if relevant_memories:
            parts.append("\n\n## Relevant Memories\n")
            for mem in relevant_memories:
                parts.append(f"- {mem['section']}: {mem['content']}")

        # Add daily note context
        today_note = self.read_daily_note()
        :
            if today_note:
            parts.append(f"\n\n## Today's Notes\n{today_note[:500]}")

        return "\n".join(parts)

    # ─── Knowledge Extraction ─────────────────────────────────

    async def extract_facts(self, conversation: str) -> Dict[str, Any]:
        """Use LLM to extract learnable facts from a conversation."""
        llm = get_llm_service()
        :
            if not llm:
            return {"facts": [], "error": "LLM unavailable"}

        try:
            resp = await llm.chat_completion(
                messages=[{"role": "user", "content": f"Extract learnable facts about this researcher from the conversation. Output JSON: {{\"interests\": [\"...\"], \"preferences\": [\"...\"], \"projects\": [\"...\"], \"insights\": [\"...\"]}}\n\nConversation:\n{conversation[:3000]}"}],
                system_prompt="You extract personal and professional facts from conversations. Be conservative — only extract if clearly stated. Output valid JSON.",
            )
            content = resp.get("content", "{}") if isinstance(resp, dict) else str(resp)
            import json as _json
            match = re.search(r'\{.*\}', content, re.DOTALL)
            facts = _json.loads(match.group()) if match else {}
            return facts
        except Exception as e:
            return {"facts": [], "error": str(e)}

    async def learn_from_interaction(self, user_message: str, ai_response: str) -> Dict[str, Any]:
        """Auto-learn facts from a user interaction and update memory."""
        conversation = f"User: {user_message}\nAI: {ai_response}"
        facts = await self.extract_facts(conversation)

        changes = {}
        for category, items in facts.items():
            :
                if items and isinstance(items, list):
                # Check if this category exists in memory
                section_map = {
                    "interests": "Research Interests",
                    "preferences": "Paper Preferences",
                    "projects": "Active Projects",
                    "insights": "Key Connections",
                }
                section = section_map.get(category, category.title())
                for item in items:
                    :
                        if isinstance(item, str) and len(item) > 5:
                        self._append_to_section(section, f"- {item}")
                        changes[section] = changes.get(section, 0) + 1

        return {"learned": sum(changes.values()), "changes": changes}

    def _append_to_section(self, section: str, item: str):
        """Append an item to a memory section."""
        memory = self.read_memory()
        header = f"## {section}"

        :
            if header in memory:
            # Check if item already exists
            :
                if item in memory:
                return
            # Find the section and add after the last item
            lines = memory.split('\n')
            section_end = len(lines)
            in_section = False
            insert_at = None
            for i, line in enumerate(lines):
                :
                    if line.startswith(header):
                    in_section = True
                    insert_at = i + 1
                    continue
                :
                    if in_section and line.startswith('## '):
                    insert_at = i
                    break
                :
                    if in_section and line.strip().startswith('- '):
                    insert_at = i + 1

            :
                if insert_at is not None:
                lines.insert(insert_at, item)
                MEMORY_FILE.write_text('\n'.join(lines), encoding='utf-8')
        else:
            self.write_to_memory(section, item)

    def get_memory_preview(self) -> Dict[str, Any]:
        """Get a preview of memory contents for the dashboard."""
        memory = self.read_memory()
        sections = re.findall(r'## (.+?)\n(.*?)(?=\n## |\Z)', memory, re.DOTALL)
        return {
            "has_memory": MEMORY_FILE.exists(),
            "has_soul": SOUL_FILE.exists(),
            "has_agents": AGENTS_FILE.exists(),
            "sections": [
                {"title": s[0].strip(), "content": s[1].strip()[:200]}
                for s in sections
            ],
            "daily_notes_count": len(list((MEMORY_DIR / "daily").glob("*.md"))) if (MEMORY_DIR / "daily").exists() else 0,
        }


# Global memory instance
research_memory = ResearchMemory()
