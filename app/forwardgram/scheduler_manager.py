"""
Scheduler management for Forwardgram application.
Handles AsyncIOScheduler integration and sending status tracking.
"""

import logging
import random
from typing import Dict, List, Any, Callable
from pytz import utc
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aio_timers import Timer
from .data_types import ChannelConfig


class SchedulerManager:
    """Manages job scheduling and sending status tracking."""

    def __init__(self, configs: List[ChannelConfig]):
        self.configs = configs
        self.scheduler = AsyncIOScheduler(timezone=utc)

        # Sending status tracking - preserves original structure
        self.sending_status: Dict[str, Dict[str, bool]] = {}

        # Sending timers - preserves original structure
        self.sending_timers: Dict[str, List[Timer]] = {}

        # Initialize per-config structures
        self._initialize_sending_structures()

        self.logger = logging.getLogger(__name__)

    def _initialize_sending_structures(self) -> None:
        """Initialize sending structures for each config."""
        for config in self.configs:
            self.sending_status[config.name] = {"in_progress": False}
            self.sending_timers[config.name] = []

    def start_scheduler(self) -> None:
        """Start the AsyncIOScheduler."""
        try:
            if not self.scheduler.running:
                self.scheduler.start()
                self.logger.info("Scheduler started successfully")
        except Exception as e:
            self.logger.error(f"Error starting scheduler: {e}")
            raise

    def shutdown_scheduler(self) -> None:
        """Shutdown the AsyncIOScheduler."""
        try:
            self.cleanup_all_timers()
            if self.scheduler.running:
                self.scheduler.shutdown()
                self.logger.info("Scheduler shutdown successfully")
        except Exception as e:
            self.logger.error(f"Error shutting down scheduler: {e}")

    def add_periodic_job(
        self,
        func: Callable,
        interval_seconds: int,
        job_id: str = None,
        args: List[Any] = None,
    ) -> None:
        """Add periodic job to scheduler."""
        try:
            self.scheduler.add_job(
                func, "interval", seconds=interval_seconds, id=job_id, args=args or []
            )
            self.logger.info(
                f"Added periodic job '{job_id}' with {interval_seconds}s interval"
            )
        except Exception as e:
            self.logger.error(f"Error adding periodic job: {e}")

    def add_cron_job(
        self,
        func: Callable,
        minute: str = None,
        hour: str = None,
        job_id: str = None,
        args: List[Any] = None,
    ) -> None:
        """Add cron-style job to scheduler."""
        try:
            self.scheduler.add_job(
                func, "cron", minute=minute, hour=hour, id=job_id, args=args or []
            )
            self.logger.info(f"Added cron job '{job_id}' at {hour}:{minute}")
        except Exception as e:
            self.logger.error(f"Error adding cron job: {e}")

    def remove_job(self, job_id: str) -> None:
        """Remove job from scheduler."""
        try:
            self.scheduler.remove_job(job_id)
            self.logger.info(f"Removed job '{job_id}'")
        except Exception as e:
            self.logger.error(f"Error removing job: {e}")

    def is_sending_in_progress(self, config_name: str) -> bool:
        """Check if sending is in progress for config."""
        return self.sending_status.get(config_name, {}).get("in_progress", False)

    def set_sending_status(self, config_name: str, in_progress: bool) -> None:
        """Set sending status for config."""
        if config_name not in self.sending_status:
            self.sending_status[config_name] = {}

        self.sending_status[config_name]["in_progress"] = in_progress

        if in_progress:
            self.logger.info(f"Started sending messages for config '{config_name}'")
        else:
            self.logger.info(f"Stopped sending messages for config '{config_name}'")

    def add_sending_timer(
        self,
        config_name: str,
        delay_seconds: int,
        callback: Callable,
        args: List[Any] = None,
    ) -> None:
        """Add sending timer for message delivery."""
        if config_name not in self.sending_timers:
            self.sending_timers[config_name] = []

        timer = Timer(delay_seconds, callback, args or [])
        self.sending_timers[config_name].append(timer)

    def remove_first_sending_timer(self, config_name: str) -> None:
        """Remove first sending timer - preserves original logic."""
        if config_name in self.sending_timers and self.sending_timers[config_name]:
            self.sending_timers[config_name].pop(0)

            # Stop sending if no more timers - preserves original logic
            if not self.sending_timers[config_name]:
                self.set_sending_status(config_name, False)

    def get_sending_timer_count(self, config_name: str) -> int:
        """Get number of active sending timers for config."""
        return len(self.sending_timers.get(config_name, []))

    def clear_sending_timers(self, config_name: str) -> None:
        """Clear all sending timers for config."""
        if config_name in self.sending_timers:
            # Cancel all active timers
            for timer in self.sending_timers[config_name]:
                if timer:
                    timer.cancel()

            self.sending_timers[config_name].clear()
            self.set_sending_status(config_name, False)

    def setup_default_jobs(
        self,
        send_messages_callback: Callable,
        sending_interval: int = 2700,
    ) -> None:
        """Setup default jobs - preserves original job structure."""
        try:
            # Main sending job - preserves original interval (45 minutes = 2700 seconds)
            self.add_periodic_job(
                send_messages_callback, sending_interval, job_id="main_sending", args=[]
            )

            # Setup redirector jobs for each config
            for config in self.configs:
                if (
                    hasattr(config, "redirector_channel_id")
                    and config.redirector_channel_id
                ):
                    # Random interval between 3-9 minutes - preserves original logic
                    interval = 60 * random.randrange(3, 10)
                    self.add_periodic_job(
                        send_messages_callback,
                        interval,
                        job_id=f"redirector_{config.name}",
                        args=[config.redirector_channel_id],
                    )

            self.logger.info("Default jobs setup completed")

        except Exception as e:
            self.logger.error(f"Error setting up default jobs: {e}")

    def cleanup_all_timers(self) -> None:
        """Cleanup all sending timers."""
        for config_name in list(self.sending_timers.keys()):
            self.clear_sending_timers(config_name)

        self.logger.info("All sending timers cleaned up")

    def __enter__(self):
        """Context manager entry."""
        self.start_scheduler()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown_scheduler()
