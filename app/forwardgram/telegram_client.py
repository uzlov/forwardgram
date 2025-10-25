"""
Telegram client management for Forwardgram application.
Handles client initialization, session management, and message operations.
"""

import logging
import sys
from typing import Dict, List, Optional, Any, Union
from telethon import TelegramClient, events
from telethon.tl.types import InputChannel, Message
from .data_types import GlobalConfig, ChannelConfig


class TelegramClientManager:
    """Manages Telegram client operations and channel entities."""

    def __init__(self, global_config: GlobalConfig, configs: List[ChannelConfig]):
        self.global_config = global_config
        self.configs = configs

        # Telegram client
        self.client: Optional[TelegramClient] = None

        # Channel entities storage - preserves original structure
        self.input_channels_entities_per_config: Dict[str, List[InputChannel]] = {}
        self.output_channel_entity: Dict[str, Optional[InputChannel]] = {}

        self.logger = logging.getLogger(__name__)

    async def initialize_client(self) -> None:
        """Initialize Telegram client - preserves original logic."""
        try:
            session_name = f"{self.global_config.session_name}_{self.global_config.env}"
            self.client = TelegramClient(
                session_name, self.global_config.api_id, self.global_config.api_hash
            )

            await self.client.start()
            self.logger.info(
                f"Telegram client initialized with session: {session_name}"
            )

        except Exception as e:
            self.logger.error(f"Error initializing Telegram client: {e}")
            raise

    async def resolve_channel_entities(self) -> None:
        """Resolve channel entities for all configs - preserves original logic."""
        try:
            # Initialize per-config structures
            for config in self.configs:
                self.input_channels_entities_per_config[config.name] = []
                self.output_channel_entity[config.name] = None

            # Resolve entities by iterating through dialogs - preserves original approach
            for config in self.configs:
                await self._resolve_config_entities(config)

            self.logger.info("Channel entities resolved successfully")

        except Exception as e:
            self.logger.error(f"Error resolving channel entities: {e}")
            raise

    async def _resolve_config_entities(self, config: ChannelConfig) -> None:
        """Resolve entities for single config - preserves original logic."""
        channel_ids = list(config.input_channels.keys())

        async for dialog in self.client.iter_dialogs():
            dialog_id = str(dialog.entity.id)

            # Handle input channels
            if dialog_id in channel_ids:
                input_channel = InputChannel(
                    dialog.entity.id, dialog.entity.access_hash
                )
                self.input_channels_entities_per_config[config.name].append(
                    input_channel
                )
                self.logger.info(
                    f"Listening to {dialog.name} channel (name:{dialog.entity.username}, id:{dialog.entity.id})."
                )

            # Handle output channel
            if dialog_id == config.output_channel_id:
                self.output_channel_entity[config.name] = InputChannel(
                    dialog.entity.id, dialog.entity.access_hash
                )

        # Validate output channel exists - preserves original validation
        if self.output_channel_entity[config.name] is None:
            error_msg = f"Config '{config.name}'. Could not find the channel {config.output_channel_id} in the user's dialogs"
            self.logger.error(error_msg)
            sys.exit(1)

        input_count = len(self.input_channels_entities_per_config[config.name])
        self.logger.info(
            f"Config '{config.name}'. Listening on {input_count} channels. Forwarding messages to {config.output_channel_id}."
        )

    async def setup_channel_discovery(self, channel_names: List[str]) -> None:
        """Setup channel discovery for new channels - preserves original logic."""
        if not channel_names:
            return

        self.logger.info("Channel discovery mode enabled")

        async for dialog in self.client.iter_dialogs():
            if dialog.name in channel_names:
                self.logger.debug(
                    f"{dialog.name} (name:{dialog.entity.username}, id:{dialog.entity.id})"
                )

        sys.exit(0)

    async def send_message_by_type(
        self, message: Union[Message, str, Dict[str, Any]], config_name: str
    ) -> None:
        """Send message by type - preserves original logic exactly."""
        try:
            output_entity = self.output_channel_entity.get(config_name)
            if not output_entity:
                raise ValueError(f"No output channel entity for config '{config_name}'")

            # Handle grouped messages (albums) - preserves original logic
            if isinstance(message, dict) and message.get("grouped_id") is not None:
                await self.client.send_file(output_entity, message["files"])
            else:
                # Handle regular messages and strings
                await self.client.send_message(output_entity, message)

        except Exception as e:
            self.logger.error(f"Can't send the message: {message}")
            self.logger.error(e, exc_info=False)
            raise

    async def get_channel_history(
        self, channel_id: str, min_id: int, max_id: int
    ) -> List[Message]:
        """Get channel message history - preserves original logic exactly."""
        try:
            messages = []

            async for message in self.client.iter_messages(
                int(channel_id), min_id=min_id - 1, max_id=max_id + 1
            ):
                messages.insert(0, message)  # Preserve original order

            return messages

        except Exception as e:
            self.logger.error(f"Error getting channel history for {channel_id}: {e}")
            return []

    def register_event_handlers(self, handlers: Dict[str, Any]) -> None:
        """Register Telegram event handlers."""
        try:
            for (
                config_name,
                input_channels,
            ) in self.input_channels_entities_per_config.items():
                self._register_config_handlers(config_name, input_channels, handlers)

            self.logger.info("Event handlers registered successfully")

        except Exception as e:
            self.logger.error(f"Error registering event handlers: {e}")
            raise

    def _register_config_handlers(
        self,
        config_name: str,
        input_channels: List[InputChannel],
        handlers: Dict[str, Any],
    ) -> None:
        """Register handlers for specific config."""
        # Message deleted handler
        if "message_deleted" in handlers:

            @self.client.on(events.MessageDeleted(chats=input_channels))
            async def deleted_handler(event, cfg_name=config_name):
                await handlers["message_deleted"](event, cfg_name)

        # Message edited handler
        if "message_edited" in handlers:

            @self.client.on(events.MessageEdited(chats=input_channels))
            async def edited_handler(event, cfg_name=config_name):
                await handlers["message_edited"](event, cfg_name)

        # New message handler
        if "new_message" in handlers:

            @self.client.on(events.NewMessage(chats=input_channels))
            async def new_handler(event, cfg_name=config_name):
                await handlers["new_message"](event, cfg_name)

    async def run_until_disconnected(self) -> None:
        """Run client until disconnected."""
        try:
            await self.client.run_until_disconnected()
        except Exception as e:
            self.logger.error(f"Client disconnected with error: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect the client."""
        try:
            if self.client and self.client.is_connected():
                await self.client.disconnect()
                self.logger.info("Telegram client disconnected")
        except Exception as e:
            self.logger.error(f"Error disconnecting client: {e}")

    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self.client is not None and self.client.is_connected()

    def __enter__(self):
        """Context manager entry."""
        self.initialize_client()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
