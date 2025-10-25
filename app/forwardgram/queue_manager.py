"""
Queue management for Forwardgram application.
Handles message queue operations with timer logic preserved.
"""

import logging
from typing import Dict, List, Optional, Any
from aio_timers import Timer
from .data_types import MessageQueue, ChannelConfig, TimerDict
from .database_manager import DatabaseManager


class QueueManager:
    """Manages message queues with preserved timer logic."""

    def __init__(self, database_manager: DatabaseManager, configs: List[ChannelConfig]):
        self.db_manager = database_manager
        self.configs = configs
        self.queues: List[Dict[str, Any]] = []  # Preserves original structure

        # Timer management - preserves original structure
        self.close_queue_timers: TimerDict = {}
        self.update_queue_timers: Dict[int, Timer] = {}

        # Initialize per-config timer structures
        self._initialize_timer_structures()

        self.logger = logging.getLogger(__name__)

    def _initialize_timer_structures(self) -> None:
        """Initialize timer structures for each config."""
        for config in self.configs:
            self.close_queue_timers[config.name] = {}

    def load_initial_queues(self) -> None:
        """Load initial queues from database - preserves original logic."""
        try:
            db_queues = self.db_manager.load_queues()

            for db_queue in db_queues:
                self.logger.debug(f"Loaded queue from DB: {db_queue}")

                # Parse initial data and create queue - preserves original structure
                queue = {
                    "qid": db_queue.qid,
                    "config_name": db_queue.config_name,
                    "channel_id": db_queue.channel_id,
                    "min_id": db_queue.data.get("min_id", 0),
                    "max_id": db_queue.data.get("max_id", 0),
                    "open": db_queue.data.get("open", True),
                    "messages": [],  # Always empty on load, as per original
                }

                self.logger.debug(f"Queue from row: {queue}")
                self.queues.append(queue)

                # Start closing timer if queue is open - preserves original logic
                if queue["open"]:
                    self.start_closing_channel_queue(queue)

            if len(db_queues):
                self.logger.debug(f"Queue(s) was loaded on start: {db_queues}")
                self.logger.info(
                    f"Loaded initial data from db: {len(db_queues)} queue(s)."
                )

        except Exception as e:
            self.logger.error(f"Error loading initial queues: {e}")

    def get_channel_queue(
        self,
        channel_id: str,
        config_name: str,
        create_not_existing: bool = True,
        open: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Get queue or create new - preserves original logic exactly."""
        queue = next(
            (
                queue
                for queue in self.queues
                if queue["channel_id"] == channel_id
                and queue["config_name"] == config_name
                and queue["open"] == open
            ),
            None,
        )

        # Add new item if queue doesn't exist - preserves original logic
        if queue is None and create_not_existing:
            queue = {
                "qid": 0,
                "channel_id": channel_id,
                "config_name": config_name,
                "min_id": 0,
                "max_id": 0,
                "messages": [],
                "open": True,
            }
            self.queues.append(queue)
            self._create_queue_in_db(queue)
            return self.get_channel_queue(channel_id, config_name)
        else:
            return queue

    def init_channel_queue(self, message, channel_id: str, config_name: str) -> None:
        """Initialize channel queue - preserves original logic exactly."""
        queue = self.get_channel_queue(channel_id, config_name)

        # Set min_id only if it's 0, preserve max_id update - original logic
        queue["min_id"] = message.id if queue["min_id"] == 0 else queue["min_id"]
        # Always refresh max_id - original logic
        queue["max_id"] = message.id

        self.logger.debug(f"Inited new queue: {queue}")
        self._update_queue_in_db(queue)

        # Start closing timer - preserves original logic
        self.start_closing_channel_queue(queue)

    def refresh_channel_queue(self, channel_id: str, config_name: str) -> None:
        """Refresh channel queue - preserves original logic exactly."""
        queue = self.get_channel_queue(channel_id, config_name, False)
        # Restart the closing timer if queue exists - original logic
        if queue is not None:
            self.start_closing_channel_queue(queue)

    def close_channel_queue(self, queue: Dict[str, Any]) -> None:
        """Close channel queue - preserves original logic exactly."""
        queue["open"] = False
        self._update_queue_in_db(queue)

        # Remove timer - preserves original logic
        if queue["channel_id"] in self.close_queue_timers[queue["config_name"]]:
            del self.close_queue_timers[queue["config_name"]][queue["channel_id"]]

        self.logger.info(f"The queue for channel {queue['channel_id']} is closed.")

    def start_closing_channel_queue(self, queue: Dict[str, Any]) -> None:
        """Start closing timer - preserves original logic exactly."""
        channel_settings = self._get_channel_settings(
            queue["channel_id"], queue["config_name"]
        )

        # Cancel existing timer - preserves original logic
        if (
            self.close_queue_timers[queue["config_name"]].get(queue["channel_id"])
            is not None
        ):
            self.close_queue_timers[queue["config_name"]][queue["channel_id"]].cancel()

        # Get interval and evaluate if string - preserves original logic
        close_queue_interval = channel_settings["close_queue_interval"]
        close_queue_interval = (
            eval(close_queue_interval)
            if isinstance(close_queue_interval, str)
            else close_queue_interval
        )

        # Create new timer - preserves original logic
        self.close_queue_timers[queue["config_name"]][queue["channel_id"]] = Timer(
            close_queue_interval, self.close_channel_queue, [queue]
        )

    def delete_queue(self, queue: Dict[str, Any]) -> None:
        """Delete queue from memory and database."""
        try:
            # Create MessageQueue for database deletion
            db_queue = MessageQueue(
                qid=queue["qid"],
                config_name=queue["config_name"],
                channel_id=queue["channel_id"],
                data=self._prepare_queue_data_for_db(queue),
            )

            # Delete from database
            self.db_manager.delete_queue(db_queue)

            # Remove from memory
            if queue in self.queues:
                self.queues.remove(queue)

            self.logger.info(
                f"Deleted queue id {queue['qid']} for channel {queue['channel_id']} for config '{queue['config_name']}'."
            )

        except Exception as e:
            self.logger.error(f"Error deleting queue: {e}")

    def _create_queue_in_db(self, queue: Dict[str, Any]) -> None:
        """Create queue in database - preserves original logic."""
        try:
            db_queue = MessageQueue(
                qid=0,  # Will be set by database
                config_name=queue["config_name"],
                channel_id=queue["channel_id"],
                data=self._prepare_queue_data_for_db(queue),
            )

            queue_id = self.db_manager.create_queue(db_queue)
            queue["qid"] = queue_id

            self.logger.info(
                f"Created new queue id {queue['qid']} for channel id {queue['channel_id']} for config '{queue['config_name']}'."
            )

        except Exception as e:
            self.logger.error(f"Error creating queue in database: {e}")

    def _update_queue_in_db(self, queue: Dict[str, Any]) -> None:
        """Update queue in database with timeout - preserves original logic."""
        # Cancel existing update timer - preserves original logic
        if self.update_queue_timers.get(queue["qid"]) is not None:
            self.update_queue_timers[queue["qid"]].cancel()

        # Create new timer with 1 second delay - preserves original logic
        self.update_queue_timers[queue["qid"]] = Timer(
            1, self._update_queue_execution, [queue]
        )

    def _update_queue_execution(self, queue: Dict[str, Any]) -> None:
        """Execute queue update - preserves original logic."""
        try:
            db_queue = MessageQueue(
                qid=queue["qid"],
                config_name=queue["config_name"],
                channel_id=queue["channel_id"],
                data=self._prepare_queue_data_for_db(queue),
            )

            self.db_manager.update_queue(db_queue)

            self.logger.info(
                f"Updated queue id {queue['qid']} for channel id {queue['channel_id']} for config '{queue['config_name']}'."
            )

        except Exception as e:
            self.logger.error(f"Error updating queue in database: {e}")

    def _prepare_queue_data_for_db(self, queue: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare queue data for database storage - preserves original logic."""
        # Copy queue and remove non-data fields - preserves original logic
        data = queue.copy()
        for prop in ["qid", "config_name", "messages"]:
            if prop in data:
                del data[prop]

        return data

    def _get_channel_settings(
        self, channel_id: str, config_name: str
    ) -> Dict[str, Any]:
        """Get channel settings - simplified version for queue operations."""
        config = next(
            (config for config in self.configs if config.name == config_name), None
        )
        if config is None:
            return {}

        # Get default settings
        channel_settings = {}
        if (
            hasattr(config, "channel_settings_default")
            and config.channel_settings_default
        ):
            channel_settings = config.channel_settings_default.__dict__.copy()

        # Apply channel-specific overrides
        if hasattr(config, "input_channels") and channel_id in config.input_channels:
            channel_override = config.input_channels[channel_id]
            if hasattr(channel_override, "__dict__"):
                channel_settings.update(channel_override.__dict__)

        return channel_settings

    def cleanup_timers(self) -> None:
        """Cleanup all active timers."""
        # Cancel close queue timers
        for config_timers in self.close_queue_timers.values():
            for timer in config_timers.values():
                if timer:
                    timer.cancel()

        # Cancel update timers
        for timer in self.update_queue_timers.values():
            if timer:
                timer.cancel()

        self.logger.info("All queue timers cleaned up.")
