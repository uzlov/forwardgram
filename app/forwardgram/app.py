"""
Main Forwardgram application orchestrator class.
Integrates all components and preserves original application logic.
"""

import logging
import random
import mysql.connector
from typing import Dict, List, Optional, Any, Union
from telethon.tl.types import Message

from .data_types import GlobalConfig, ConfigList, ChannelConfig, ChannelSettings
from .database_manager import DatabaseManager
from .queue_manager import QueueManager
from .scheduler_manager import SchedulerManager
from .telegram_client import TelegramClientManager
from .message_processor import MessageProcessor
from .config_manager import ConfigurationManager


class ForwardgramApp:
    """Main application orchestrator class."""

    # For the testing.
    SENDING_INTERVAL = 15
    SENDING_MESSAGE_INTERVAL_MIN = 5
    SENDING_MESSAGE_INTERVAL_MAX = 15
    SENDING_TIME_LIMIT = 60 * 15

    # Constants from original forwardgram.py
    # SENDING_INTERVAL = 60 * 45  # 45 minutes
    # SENDING_MESSAGE_INTERVAL_MIN = 10  # 10 seconds
    # SENDING_MESSAGE_INTERVAL_MAX = 20  # 20 seconds
    # SENDING_TIME_LIMIT = 60 * 30  # 30 minutes

    def __init__(self, global_config: GlobalConfig, channel_configs: ConfigList):
        self.global_config = global_config
        self.channel_configs = channel_configs

        # Component managers
        self.db_manager: Optional[DatabaseManager] = None
        self.queue_manager: Optional[QueueManager] = None
        self.scheduler_manager: Optional[SchedulerManager] = None
        self.telegram_manager: Optional[TelegramClientManager] = None
        self.message_processor: Optional[MessageProcessor] = None

        self.logger = logging.getLogger(__name__)

        # Initialize components
        self._initialize_components()

    def _initialize_components(self) -> None:
        """Initialize all component managers."""
        try:
            # Database manager
            self.db_manager = DatabaseManager(
                self.global_config.db_config, self.global_config.env
            )

            # Queue manager
            self.queue_manager = QueueManager(self.db_manager, self.channel_configs)

            # Scheduler manager
            self.scheduler_manager = SchedulerManager(self.channel_configs)

            # Telegram client manager
            self.telegram_manager = TelegramClientManager(
                self.global_config, self.channel_configs
            )

            # Message processor
            self.message_processor = MessageProcessor(
                self.global_config.global_tags or {}
            )

            self.logger.info("All components initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing components: {e}")
            raise

    async def setup_channel_discovery(self, channel_names: List[str]) -> None:
        """Setup channel discovery - preserves original logic."""
        if channel_names:
            await self.telegram_manager.setup_channel_discovery(channel_names)

    async def initialize_application(self) -> None:
        """Initialize the complete application."""
        try:
            # Initialize database connection
            self.db_manager.initialize_connection()

            # Create tables if needed
            if not self.db_manager.is_table_exist(self.db_manager.table_name):
                self.db_manager.create_data_table()

            # Initialize Telegram client
            await self.telegram_manager.initialize_client()

            # Resolve channel entities
            await self.telegram_manager.resolve_channel_entities()

            # Load initial queues
            self.queue_manager.load_initial_queues()

            # Setup event handlers
            self._setup_event_handlers()

            # Start scheduler
            self.scheduler_manager.start_scheduler()

            self.logger.info("Application initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing application: {e}")
            raise

    def _setup_event_handlers(self) -> None:
        """Setup Telegram event handlers."""
        handlers = {
            "message_deleted": self._handle_message_deleted,
            "message_edited": self._handle_message_edited,
            "new_message": self._handle_new_message,
        }

        self.telegram_manager.register_event_handlers(handlers)

    async def _handle_message_deleted(self, event, config_name: str) -> None:
        """Handle message deleted event - preserves original logic."""
        channel_id = self._get_channel_id(event)
        if channel_id:
            self.logger.debug(f"Config_name: {config_name}")
            self.queue_manager.refresh_channel_queue(channel_id, config_name)
            self.logger.debug(
                f"Message(s) from channel {channel_id} for config '{config_name}' can to be deleted, if is still not sent."
            )

    async def _handle_message_edited(self, event, config_name: str) -> None:
        """Handle message edited event - preserves original logic."""
        channel_id = self._get_channel_id(event)
        if channel_id:
            self.logger.debug(f"Config_name: {config_name}")
            self.queue_manager.refresh_channel_queue(channel_id, config_name)
            self.logger.debug(
                f"Message from channel {event.chat.title} ({channel_id}) for config '{config_name}' can to be updated, if is still not sent."
            )

    async def _handle_new_message(self, event, config_name: str) -> None:
        """Handle new message event - preserves original logic."""
        channel_id = self._get_channel_id(event)
        if channel_id:
            self.logger.debug(f"Config_name: {config_name}")
            self.queue_manager.init_channel_queue(
                event.message, channel_id, config_name
            )
            self.logger.debug(
                f"Message from channel {event.chat.title} ({channel_id}) for config '{config_name}' can be forwarded."
            )
            self.logger.debug(f"Message {event.message}")

    def _get_channel_id(self, event) -> Optional[str]:
        """Get channel ID from event - preserves original logic."""
        channel_id = None
        if event.chat:
            channel_id = event.chat.id
        elif event.original_update:
            channel_id = event.original_update.channel_id

        return str(channel_id) if channel_id else None

    async def _send_messages_from_queues(self, channel_id: str = "") -> None:
        """Send messages from queues - preserves original logic."""
        # Get all queues
        queues = self.queue_manager.queues

        # New sending status per config
        new_sending_status = {}
        # Init the sending timer for the current job
        sending_timer = {}
        # Init the total counters for the current job
        total_counter = 0
        total_waiting_counter = 0

        for i, queue in enumerate(queues):
            # Don't send messages if sending still in progress
            if self.scheduler_manager.is_sending_in_progress(queue["config_name"]):
                self.logger.info(
                    f"The sending of messages for config '{queue['config_name']}' still in progress! We will send messages in next time."
                )
                continue

            # Init sending timer per config
            if sending_timer.get(queue["config_name"]) is None:
                sending_timer[queue["config_name"]] = 0

            total_waiting_counter += (
                0 if queue["min_id"] == 0 else queue["max_id"] - queue["min_id"] + 1
            )

            # Skip if queue is open, empty, or not matching channel filter
            if (
                queue["open"]
                or queue["min_id"] == 0
                or (channel_id and queue["channel_id"] != channel_id)
            ):
                continue

            # Populate messages for channel before send
            await self._populate_messages_in_queue(queue)

            # Init the counter for the current queue
            counter = 0
            while queue["messages"]:
                sending_timer[queue["config_name"]] += random.randrange(
                    self.SENDING_MESSAGE_INTERVAL_MIN, self.SENDING_MESSAGE_INTERVAL_MAX
                )

                # Create sending timer
                self.scheduler_manager.add_sending_timer(
                    queue["config_name"],
                    sending_timer[queue["config_name"]],
                    self._send_message_callback,
                    [queue["messages"][0], queue["config_name"]],
                )

                # Delete message from queue
                del queue["messages"][0]
                counter += 1

            # Start the sending of messages if timer is more than zero
            if sending_timer[queue["config_name"]] > 0:
                new_sending_status[queue["config_name"]] = {"in_progress": True}

            self.logger.info(
                f"The forwarding of the {counter} message(s) for config '{queue['config_name']}' was started for channel {queue['channel_id']}."
            )

            # Queue is empty and can be deleted
            self._delete_sent_queue(queue)
            total_counter += counter

            if sending_timer[queue["config_name"]] >= self.SENDING_TIME_LIMIT:
                break

        # Refresh global sending status per config
        for config_name, status in new_sending_status.items():
            self.scheduler_manager.set_sending_status(
                config_name, status["in_progress"]
            )

        self.logger.info(
            f"In total: ~{total_waiting_counter} message(s) in {len(queues)} queue(s) are awaiting the sending."
        )
        self.logger.info(
            f"The {total_counter} message(s) will be forwarded from all channels."
        )

    async def _send_message_callback(
        self, message: Union[Message, str, Dict[str, Any]], config_name: str
    ) -> None:
        """Send message callback - preserves original logic."""
        try:
            await self.telegram_manager.send_message_by_type(message, config_name)
        except Exception as e:
            self.logger.error(f"Error in send message callback: {e}")
        finally:
            # Remove the first timer
            self.scheduler_manager.remove_first_sending_timer(config_name)

    def _delete_sent_queue(self, queue: Dict[str, Any]) -> None:
        """Delete sent queue - preserves original logic."""
        self.queue_manager.delete_queue(queue)
        self.logger.info(
            f"The queue for channel {queue['channel_id']} for config '{queue['config_name']}' was deleted."
        )

    async def _populate_messages_in_queue(self, queue: Dict[str, Any]) -> None:
        """Populate messages in queue - preserves original logic."""
        # Get messages from channel
        messages = await self.telegram_manager.get_channel_history(
            queue["channel_id"], queue["min_id"], queue["max_id"]
        )

        # Add all messages to queue
        self._add_messages_to_queue(queue, messages)

    def _add_messages_to_queue(
        self, queue: Dict[str, Any], messages: List[Message]
    ) -> None:
        """Add messages to queue - preserves original logic."""
        channel_settings = self._get_channel_settings(
            queue["channel_id"], queue["config_name"]
        )

        for message in messages:
            if self.message_processor.is_message_allowed(message, channel_settings):
                # Execute all transformations for text in message
                self.message_processor.process_message_transformations(
                    message, queue["channel_id"], channel_settings
                )

                # Handle grouped messages (albums)
                if message.grouped_id is not None:
                    # The message is one from album
                    self._append_media_to_album(queue, message)
                    # Add text message after album if it exists and not duplicated
                    if message.message and not self._is_last_message_duplicated(
                        queue, message.message
                    ):
                        queue["messages"].append(message.message)
                else:
                    if not self._is_last_message_duplicated(queue, message.message):
                        queue["messages"].append(message)

    def _get_album_from_queue(
        self, queue: Dict[str, Any], grouped_id: int, create_not_exist: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get album from queue - preserves original logic."""
        message = next(
            (
                message
                for message in queue["messages"]
                if isinstance(message, dict)
                and message.get("grouped_id") is not None
                and message["grouped_id"] == grouped_id
            ),
            None,
        )

        # Add new item if album doesn't exist
        if message is None and create_not_exist:
            message = {"ids": [], "grouped_id": grouped_id, "files": []}
            queue["messages"].append(message)
            return self._get_album_from_queue(queue, grouped_id)
        else:
            return message

    def _append_media_to_album(self, queue: Dict[str, Any], message: Message) -> None:
        """Append media to album - preserves original logic."""
        album = self._get_album_from_queue(queue, message.grouped_id)
        album["files"].append(message.media)
        album["ids"].append(message.id)

    def _is_last_message_duplicated(self, queue: Dict[str, Any], text: str) -> bool:
        """Check if last message is duplicated - preserves original logic."""
        if not queue["messages"]:
            return False

        # Get the last message
        message = queue["messages"][-1]
        return (
            isinstance(message, dict)
            and message.get("message") is not None
            and message.message == text
        ) or (isinstance(message, str) and message == text)

    def _get_channel_settings(
        self, channel_id: str, config_name: str
    ) -> ChannelSettings:
        """Get channel settings - preserves original logic."""
        config = self._get_config_by_name(config_name)

        # Get default settings
        channel_settings = config.channel_settings_default.__dict__.copy()
        # Apply channel-specific overrides
        if config.input_channels[channel_id]:
            channel_settings.update(config.input_channels[channel_id].__dict__)

        return ChannelSettings(**channel_settings)

    def _get_config_by_name(self, config_name: str) -> ChannelConfig:
        """Get config by name - preserves original logic."""
        return next(
            config for config in self.channel_configs if config.name == config_name
        )

    async def run_application(self) -> None:
        """Run the main application."""
        try:
            await self.initialize_application()

            self.logger.info("Starting Forwardgram application...")
            await self.telegram_manager.run_until_disconnected()

        except Exception as e:
            self.logger.error(f"Application error: {e}")
            raise

        finally:
            await self.shutdown_application()

    async def shutdown_application(self) -> None:
        """Shutdown the application gracefully."""
        try:
            # Shutdown scheduler
            if self.scheduler_manager:
                self.scheduler_manager.shutdown_scheduler()

            # Cleanup queue timers
            if self.queue_manager:
                self.queue_manager.cleanup_timers()

            # Disconnect Telegram client
            if self.telegram_manager:
                await self.telegram_manager.disconnect()

            # Close database connection
            if self.db_manager:
                self.db_manager.close_connection()

            self.logger.info("Application was shutdown gracefully.")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


# Factory function to create application instance
def create_forwardgram_app(
    global_config_path: str, tags_config_path: str = None
) -> ForwardgramApp:
    """Factory function to create ForwardgramApp instance."""
    # Load global configuration
    global_config = ConfigurationManager.load_global_config(
        global_config_path, tags_config_path
    )

    # Load channel configurations
    config_directory = f"configs.{global_config.env}"
    channel_configs = ConfigurationManager.load_channel_configs(config_directory)

    return ForwardgramApp(global_config, channel_configs)
