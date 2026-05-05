"""
Platform Integration Hub — connect Paper Agent to DingTalk, Feishu, Slack, WeCom.

Supports:
- DingTalk robot webhook (钉钉机器人)
- Feishu/Lark bot webhook (飞书机器人)
- Slack Incoming Webhook
- WeCom/WeChat Work bot (企业微信机器人)
- Generic webhook with customizable templates
"""

import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)


class Platform(str, Enum):
    DINGTALK = "dingtalk"
    FEISHU = "feishu"
    SLACK = "slack"
    WECOM = "wecom"
    GENERIC = "generic"


class MessageType(str, Enum):
    TEXT = "text"
    MARKDOWN = "markdown"
    CARD = "card"
    NEWS = "news"


# ─── Message Builders ────────────────────────────────────────

def build_dingtalk_message(content: str, msg_type: MessageType = MessageType.MARKDOWN, title: str = "Paper Agent") -> dict:
    """Build a DingTalk robot message."""
    if msg_type == MessageType.TEXT:
        return {"msgtype": "text", "text": {"content": content[:2000]}}
    return {
        "msgtype": "markdown",
        "markdown": {
            "title": title[:200],
            "text": content[:5000],
        },
    }


def build_feishu_message(content: str, msg_type: MessageType = MessageType.MARKDOWN, title: str = "Paper Agent") -> dict:
    """Build a Feishu/Lark bot message."""
    if msg_type == MessageType.TEXT:
        return {"msg_type": "text", "content": json.dumps({"text": content[:2000]})}
    return {
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": title[:100]}, "template": "blue"},
            "elements": [{"tag": "markdown", "content": content[:4000]}],
        },
    }


def build_slack_message(content: str, msg_type: MessageType = MessageType.MARKDOWN) -> dict:
    """Build a Slack message."""
    if msg_type == MessageType.TEXT:
        return {"text": content[:3000]}
    return {
        "text": "Paper Agent Notification",
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": content[:3000]}},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": f"Paper Agent · {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"}]},
        ],
    }


def build_wecom_message(content: str, msg_type: MessageType = MessageType.MARKDOWN) -> dict:
    """Build a WeCom bot message."""
    if msg_type == MessageType.TEXT:
        return {"msgtype": "text", "text": {"content": content[:2000]}}
    return {
        "msgtype": "markdown",
        "markdown": {"content": content[:4096]},
    }


# ─── Signature ───────────────────────────────────────────────

def sign_dingtalk_request(timestamp: int, secret: str) -> str:
    """Sign a DingTalk webhook request."""
    string_to_sign = f"{timestamp}\n{secret}"
    signature = hmac.new(secret.encode(), string_to_sign.encode(), hashlib.sha256).digest()
    return base64.b64encode(signature).decode()


# ─── Template ────────────────────────────────────────────────

RESEARCH_DIGEST_TEMPLATE = """# 📚 Research Digest — {date}

## 📊 Library Overview
- Total Papers: **{total_papers}**
- Read: **{read}** | Reading: **{reading}** | To Read: **{to_read}**

## 🔬 Highlight
{highlight}

## 📖 Recent Activity
{activity}

## 🎯 Reading Queue
{queue} papers waiting for your attention."""


DAILY_BRIEFING_TEMPLATE = """## 🌅 Daily Research Briefing — {date}

**Reading Progress:** {read_progress}% complete ({read}/{total} papers)

### 📌 Today's Priorities
{priorities}

### 🔍 New This Week
{new_papers}

### ⚡ Quick Stats
- Reading sessions: {sessions}
- Time spent: {minutes} min
- Pages read: {pages}"""


def render_template(template: str, **kwargs) -> str:
    """Simple template renderer."""
    result = template
    for k, v in kwargs.items():
        result = result.replace(f"{{{k}}}", str(v))
    return result


# ─── Integration Service ─────────────────────────────────────

class IntegrationService:
    """Send notifications to external platforms."""

    def __init__(self):
        self._client = None

    async def _get_client(self):
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=15)
        return self._client

    async def send(self, platform: Platform, webhook_url: str, content: str,
                   msg_type: MessageType = MessageType.MARKDOWN,
                   title: str = "Paper Agent", secret: str = None) -> Dict[str, Any]:
        """Send a message to an external platform."""
        client = await self._get_client()
        headers = {"Content-Type": "application/json"}

        try:
            if platform == Platform.DINGTALK:
                payload = build_dingtalk_message(content, msg_type, title)
                if secret:
                    timestamp = int(datetime.utcnow().timestamp() * 1000)
                    sign = sign_dingtalk_request(timestamp, secret)
                    webhook_url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"
                resp = await client.post(webhook_url, json=payload, headers=headers)

            elif platform == Platform.FEISHU:
                payload = build_feishu_message(content, msg_type, title)
                resp = await client.post(webhook_url, json=payload, headers=headers)

            elif platform == Platform.SLACK:
                payload = build_slack_message(content, msg_type)
                resp = await client.post(webhook_url, json=payload, headers=headers)

            elif platform == Platform.WECOM:
                payload = build_wecom_message(content, msg_type)
                resp = await client.post(webhook_url, json=payload, headers=headers)

            else:
                payload = {"text": content[:3000], "source": "paper-agent"}
                resp = await client.post(webhook_url, json=payload, headers=headers)

            resp.raise_for_status()
            return {"success": True, "status_code": resp.status_code, "platform": platform.value}

        except Exception as e:
            logger.error(f"Failed to send to {platform.value}: {e}")
            return {"success": False, "error": str(e), "platform": platform.value}

    async def send_daily_briefing(self, platform: Platform, webhook_url: str,
                                  stats: Dict[str, Any], priorities: List[str],
                                  secret: str = None) -> Dict[str, Any]:
        """Send a formatted daily research briefing."""
        content = render_template(
            DAILY_BRIEFING_TEMPLATE,
            date=datetime.utcnow().strftime("%b %d, %Y"),
            read_progress=stats.get("read_progress", 0),
            read=stats.get("read", 0),
            total=stats.get("total", 0),
            priorities="\n".join(f"- {p}" for p in priorities[:5]) or "No priorities set",
            new_papers=stats.get("new_papers", "None"),
            sessions=stats.get("sessions", 0),
            minutes=stats.get("minutes", 0),
            pages=stats.get("pages", 0),
        )
        return await self.send(platform, webhook_url, content, title="Daily Briefing", secret=secret)

    async def send_digest(self, platform: Platform, webhook_url: str,
                          stats: Dict[str, Any], highlight: str = "",
                          activity: str = "", secret: str = None) -> Dict[str, Any]:
        """Send a formatted research digest."""
        content = render_template(
            RESEARCH_DIGEST_TEMPLATE,
            date=datetime.utcnow().strftime("%b %d, %Y"),
            total_papers=stats.get("total", 0),
            read=stats.get("read", 0),
            reading=stats.get("reading", 0),
            to_read=stats.get("to_read", 0),
            highlight=highlight or "No highlights this period.",
            activity=activity or "No recent activity.",
            queue=stats.get("to_read", 0),
        )
        return await self.send(platform, webhook_url, content, title="Research Digest", secret=secret)

    async def close(self):
        if self._client:
            await self._client.aclose()


# Global integration service instance
integration_service = IntegrationService()
