"""
APScheduler integration for automatic updates

Schedules daily stock data updates from B3.
"""

import asyncio
import logging
from datetime import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Optional

from .services.auto_update import auto_update_service

logger = logging.getLogger(__name__)


class UpdateScheduler:
    """Manages scheduled updates"""

    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._update_task: Optional[asyncio.Task] = None

    def start(
        self,
        hour: int = 19,  # 7 PM (after market closes in Brazil)
        minute: int = 0,
        timezone: str = "America/Sao_Paulo"
    ):
        """
        Start the scheduler

        Args:
            hour: Hour to run update (0-23)
            minute: Minute to run update (0-59)
            timezone: Timezone for scheduling (default: Brazil)
        """
        if self.scheduler is not None:
            logger.warning("Scheduler already started")
            return

        self.scheduler = AsyncIOScheduler(timezone=timezone)

        # Add daily update job
        self.scheduler.add_job(
            self._run_scheduled_update,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="daily_stock_update",
            name="Daily B3 Stock Update",
            replace_existing=True
        )

        self.scheduler.start()
        logger.info(f"Scheduler started - daily updates at {hour:02d}:{minute:02d} {timezone}")

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler is not None:
            self.scheduler.shutdown()
            self.scheduler = None
            logger.info("Scheduler stopped")

    async def _run_scheduled_update(self):
        """Run the scheduled update (internal use only)"""
        try:
            logger.info("Starting scheduled update")
            result = await auto_update_service.run_update(force=False)
            logger.info(f"Scheduled update completed: {result}")
        except Exception as e:
            logger.error(f"Scheduled update failed: {e}", exc_info=True)

    def get_next_run_time(self) -> Optional[str]:
        """Get the next scheduled run time"""
        if self.scheduler is None:
            return None

        job = self.scheduler.get_job("daily_stock_update")
        if job is None:
            return None

        next_run = job.next_run_time
        return next_run.isoformat() if next_run else None

    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self.scheduler is not None and self.scheduler.running


# Singleton instance
scheduler = UpdateScheduler()
