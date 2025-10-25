"""
Configuration management for Forwardgram application.
"""

import yaml
import os
import logging
from typing import Dict, List, Optional, Any
from .data_types import GlobalConfig, ChannelConfig, ChannelSettings, ConfigList


class ConfigurationManager:
    """Manages loading and validation of configuration files."""

    @staticmethod
    def load_global_config(
        config_path: str, tags_path: Optional[str] = None
    ) -> GlobalConfig:
        """Load global configuration from YAML file."""
        try:
            with open(config_path, "r", encoding="utf-8") as file:
                config_data = yaml.safe_load(file)

            config_tags = None
            if tags_path and os.path.exists(tags_path):
                with open(tags_path, "r", encoding="utf-8") as file:
                    config_tags = yaml.safe_load(file)

            return GlobalConfig(
                api_id=config_data["api_id"],
                api_hash=config_data["api_hash"],
                env=config_data["env"],
                session_name=config_data["session_name"],
                logging_level=config_data["logging_level"],
                db_config=config_data["db_config"],
                global_tags=config_tags["global_tags"],
            )
        except Exception as e:
            logging.error(f"Error loading global config: {e}")
            raise

    @staticmethod
    def load_channel_configs(config_directory: str) -> ConfigList:
        """Load all channel configurations from directory."""
        configs = []

        if not os.path.exists(config_directory):
            logging.warning(f"Config directory does not exist: {config_directory}")
            return configs

        try:
            for filename in os.listdir(config_directory):
                if filename.endswith(".yml") or filename.endswith(".yaml"):
                    config_path = os.path.join(config_directory, filename)
                    config = ConfigurationManager._load_single_channel_config(
                        config_path
                    )
                    if config:
                        configs.append(config)
        except Exception as e:
            logging.error(f"Error loading channel configs: {e}")

        return configs

    @staticmethod
    def _load_single_channel_config(config_path: str) -> Optional[ChannelConfig]:
        """Load a single channel configuration file."""
        try:
            with open(config_path, "r", encoding="utf-8") as file:
                config_data = yaml.safe_load(file)

            # Parse channel settings default
            default_settings_data = config_data.get("channel_settings_default", {})
            channel_settings_default = ConfigurationManager._parse_channel_settings(
                default_settings_data
            )

            # Parse input channels
            input_channels = {}
            input_channels_data = config_data.get("input_channels", {})

            for channel_id, channel_data in input_channels_data.items():
                channel_settings = ConfigurationManager._parse_channel_settings(
                    channel_data, default_settings_data
                )
                input_channels[channel_id] = channel_settings

            config_name = os.path.splitext(os.path.basename(config_path))[0]

            return ChannelConfig(
                name=config_name,
                redirector_channel_id=config_data.get("redirector_channel_id"),
                output_channel_id=config_data["output_channel_id"],
                input_channels=input_channels,
                channel_settings_default=channel_settings_default,
            )
        except Exception as e:
            logging.error(f"Error loading config file {config_path}: {e}")
            return None

    @staticmethod
    def _parse_channel_settings(
        channel_data: Dict[str, Any], defaults: Dict[str, Any] = None
    ) -> ChannelSettings:
        """Parse channel settings with defaults."""
        if defaults is None:
            defaults = {}

        # Merge defaults with channel-specific settings
        merged_data = {**defaults, **channel_data}

        return ChannelSettings(
            close_queue_interval=merged_data.get(
                "close_queue_interval", 2700
            ),  # 45 minutes default
            links=merged_data.get("links", True),
            users=merged_data.get("users", True),
            emails=merged_data.get("emails", True),
            hash_tags=merged_data.get("hash_tags", True),
            english_part_of_message=merged_data.get("english_part_of_message", True),
            media_without_message=merged_data.get("media_without_message", False),
            media_doc_image_without_message=merged_data.get(
                "media_doc_image_without_message", False
            ),
            media_doc_video_without_message=merged_data.get(
                "media_doc_video_without_message", False
            ),
            clean_media_message=merged_data.get("clean_media_message", False),
            progressive_values=merged_data.get("progressive_values"),
            remove_keywords=merged_data.get("remove_keywords"),
            allowed_keywords=merged_data.get("allowed_keywords"),
            disallowed_keywords=merged_data.get("disallowed_keywords"),
            prices=merged_data.get("prices"),
            prices_per_channel=merged_data.get("prices_per_channel"),
            tags=merged_data.get("tags"),
            brand_id=merged_data.get("brand_id"),
        )

    @staticmethod
    def validate_configuration(
        global_config: GlobalConfig, channel_configs: ConfigList
    ) -> bool:
        """Validate configuration completeness and consistency."""
        try:
            # Validate global config
            if not global_config.api_id or not global_config.api_hash:
                logging.error("Missing Telegram API credentials")
                return False

            if not global_config.db_config:
                logging.error("Missing database configuration")
                return False

            # Validate channel configs
            if not channel_configs:
                logging.warning("No channel configurations found")
                return False

            for config in channel_configs:
                if not config.output_channel_id:
                    logging.error(f"Missing output_channel_id in config {config.name}")
                    return False

                if not config.input_channels:
                    logging.error(f"No input channels defined in config {config.name}")
                    return False

            logging.info("Configuration validation passed")
            return True

        except Exception as e:
            logging.error(f"Configuration validation error: {e}")
            return False
