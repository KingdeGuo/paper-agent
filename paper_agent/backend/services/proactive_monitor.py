"""
Proactive Research Monitor — cron-style automated paper discovery and alerts.

Inspired by OpenClaw's cron/heartbeat system.
Runs scheduled tasks to discover new papers, check deadlines, and send digests.
"""

import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ProactiveMonitor:
    """
    Proactive research monitor that runs scheduled tasks:
    - Daily: check for new papers matching alerts
    - Daily: generate morning briefing
    - Weekly: generate research digest
    - Ongoing: monitor conference deadlines
    """

    def __init__(self):
        self._task = None
        self._running = False

    async def start(self, interval_hours: int = 6):
        """Start the proactive monitoring loop."""
        if self._running:
            logger.warning("Monitor already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop(interval_hours))
        logger.info(f"Proactive monitor started (interval: {interval_hours}h)")

    async def stop(self):
        """Stop the monitoring loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Proactive monitor stopped")

    async def _run_loop(self, interval_hours: int):
        """Main monitoring loop."""
        last_daily = None
        last_weekly = None

        while self._running:
            now = datetime.utcnow()
            today = now.strftime("%Y-%m-%d")

            try:
                # Daily tasks (run once per day)
                if last_daily != today:
                    await self._run_daily_tasks()
                    last_daily = today

                # Weekly tasks (run on Mondays)
                week_num = now.isocalendar()[1]
                if last_weekly != week_num and now.weekday() == 0:
                    await self._run_weekly_tasks()
                    last_weekly = week_num

                # Always check conference deadlines
                await self._check_deadlines()

            except Exception as e:
                logger.error(f"Monitor cycle failed: {e}")

            await asyncio.sleep(interval_hours * 3600)

    async def _run_daily_tasks(self):
        """Run daily research tasks."""
        logger.info("Running daily research tasks...")

        # 1. Check research alerts
        try:
            from backend.services.registry import get_db
            db = get_db()
            if db:
                async with db.async_session_maker() as session:
                    from sqlalchemy import text as sa_text
                    # Check alerts and create notifications for new matches
                    alerts = (await session.execute(sa_text(
                        "SELECT id, name, query FROM research_alerts WHERE user_id = 'default' AND is_active = 1"
                    ))).fetchall()

                    for alert_id, name, query in alerts:
                        vs = getattr(__import__('backend.services.registry', fromlist=['get_vector_service']), 'get_vector_service')()
                        if vs:
                            results = vs.search_similar(query, limit=3)
                            for r in results:
                                if r.get("score", 0) > 0.5:
                                    import uuid
                                    nid = str(uuid.uuid4())
                                    await session.execute(sa_text(
                                        "INSERT INTO alert_history (id, alert_id, user_id, document_id, message) "
                                        "VALUES (:id, :aid, 'default', :did, :msg)"),
                                        {"id": nid, "aid": alert_id,
                                         "did": r.get("document_id", ""),
                                         "msg": f"New paper matches your alert '{name}'"})

                    await session.commit()
                    logger.info(f"Checked {len(alerts)} alerts")
        except Exception as e:
            logger.warning(f"Alert check failed: {e}")

        # 2. Generate and send daily briefing
        try:
            from backend.api.routes.research_assistant import daily_agenda
            from backend.services.registry import get_db
            db = get_db()
            if db:
                # Use the LLM to generate a briefing
                briefing = await daily_agenda(db=db)
                if briefing and briefing.get("ai_focus_suggestion"):
                    # Store as notification
                    async with db.async_session_maker() as session:
                        import uuid

                        from sqlalchemy import text as sa_text
                        await session.execute(sa_text(
                            "INSERT INTO notifications (id, user_id, title, message, notification_type, source) "
                            "VALUES (:id, 'default', :t, :m, 'daily_briefing', 'monitor')"),
                            {"id": str(uuid.uuid4()),
                             "t": f"Daily Research Briefing - {briefing.get('date', '')}",
                             "m": briefing.get("ai_focus_suggestion", "")})
                        await session.commit()
                    logger.info("Daily briefing generated")
        except Exception as e:
            logger.warning(f"Daily briefing failed: {e}")

    async def _run_weekly_tasks(self):
        """Run weekly research tasks."""
        logger.info("Running weekly research tasks...")

        try:
            from backend.services.registry import get_db, get_llm_service
            db = get_db()
            llm = get_llm_service()
            if db and llm:
                from backend.api.routes.research_assistant import weekly_briefing
                briefing = await weekly_briefing(db=db, llm_service=llm)
                if briefing and briefing.get("ai_highlight"):
                    async with db.async_session_maker() as session:
                        import uuid

                        from sqlalchemy import text as sa_text
                        await session.execute(sa_text(
                            "INSERT INTO notifications (id, user_id, title, message, notification_type, source) "
                            "VALUES (:id, 'default', :t, :m, 'weekly_digest', 'monitor')"),
                            {"id": str(uuid.uuid4()),
                             "t": f"Weekly Research Digest - {briefing.get('week_ending', '')}",
                             "m": briefing.get("ai_highlight", "")})
                        await session.commit()
                    logger.info("Weekly digest generated")
        except Exception as e:
            logger.warning(f"Weekly digest failed: {e}")

    async def _check_deadlines(self):
        """Check for upcoming conference deadlines."""
        try:
            from backend.services.registry import get_db
            db = get_db()
            if db:
                from datetime import datetime as dt
                from datetime import timedelta

                from sqlalchemy import text as sa_text
                async with db.async_session_maker() as session:
                    now = dt.utcnow().isoformat()
                    week_from_now = (dt.utcnow() + timedelta(days=7)).isoformat()

                    upcoming = (await session.execute(sa_text(
                        "SELECT id, venue_name, submission_deadline FROM conference_trackers "
                        "WHERE user_id = 'default' AND submission_deadline IS NOT NULL "
                        "AND submission_deadline > :now AND submission_deadline < :week"),
                        {"now": now, "week": week_from_now})).fetchall()

                    for u in upcoming:
                        # Check if already notified
                        existing = (await session.execute(sa_text(
                            "SELECT id FROM notifications WHERE reference_id = :rid AND notification_type = 'deadline' AND is_dismissed = 0"),
                            {"rid": u[0]})).fetchone()
                        if not existing:
                            import uuid
                            await session.execute(sa_text(
                                "INSERT INTO notifications (id, user_id, title, message, notification_type, source, reference_id) "
                                "VALUES (:id, 'default', :t, :m, 'deadline', 'monitor', :rid)"),
                                {"id": str(uuid.uuid4()),
                                 "t": f"⏰ Deadline approaching: {u[1]}",
                                 "m": f"Submission deadline for {u[1]} is in less than 7 days.",
                                 "rid": u[0]})
                    await session.commit()
                    if upcoming:
                        logger.info(f"Found {len(upcoming)} upcoming deadlines")
        except Exception as e:
            logger.warning(f"Deadline check failed: {e}")


# Global monitor
proactive_monitor = ProactiveMonitor()
