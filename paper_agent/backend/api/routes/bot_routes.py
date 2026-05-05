"""Research Bot API — multi-platform research assistant endpoints."""

import logging
from typing import Optional

from backend.services.research_bot import BotPlatform, research_bot
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/bot/message", summary="Handle a research message from any platform")
async def handle_message(
    message: str,
    platform: str = "generic",
    user_id: str = "default",
):
    """Handle a natural language research query. Works with Telegram, Slack, WhatsApp, etc."""
    try:
        bot_platform = BotPlatform(platform)
    except ValueError:
        bot_platform = BotPlatform.GENERIC

    result = await research_bot.handle_message(message, bot_platform, user_id)
    return result


@router.get("/bot/help", summary="Get bot commands/help")
async def bot_help(platform: str = "generic"):
    """Get help text for the research bot."""
    try:
        bot_platform = BotPlatform(platform)
    except ValueError:
        bot_platform = BotPlatform.GENERIC
    return research_bot._help_response(bot_platform)


@router.post("/bot/send", summary="Send proactive message to a platform")
async def send_proactive_message(
    webhook_url: str,
    message: str,
    platform: str = "generic",
    secret: Optional[str] = None,
):
    """Send a proactive research message to a chat platform (digest, alert, etc.)."""
    try:
        bot_platform = BotPlatform(platform)
    except ValueError:
        bot_platform = BotPlatform.GENERIC

    result = await research_bot.send_to_platform(bot_platform, webhook_url, message, secret)
    return result
