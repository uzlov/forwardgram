"""
Type definitions for the Forwardgram application.
"""

import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum


class QueueStatus(Enum):
    """Queue status enumeration."""

    OPEN = True
    CLOSED = False


@dataclass
class GlobalConfig:
    """Global configuration structure."""

    api_id: int
    api_hash: str
    env: str
    session_name: str
    logging_level: str
    db_config: Dict[str, Any]
    global_tags: Optional[Dict[str, Any]] = None


@dataclass
class ChannelSettings:
    """Channel-specific settings configuration."""

    close_queue_interval: int
    links: bool = True
    users: bool = True
    emails: bool = True
    hash_tags: bool = True
    english_part_of_message: bool = True
    media_without_message: bool = False
    media_doc_image_without_message: bool = False
    media_doc_video_without_message: bool = False
    clean_media_message: bool = False
    progressive_values: Optional[List[Dict[str, Union[int, float]]]] = None
    remove_keywords: Optional[List[str]] = None
    allowed_keywords: Optional[List[str]] = None
    disallowed_keywords: Optional[List[str]] = None
    prices: Optional[List[Dict[str, Any]]] = None
    prices_per_channel: Optional[Dict[str, List[Dict[str, Any]]]] = None
    tags: Optional[List[str]] = None
    brand_id: Optional[str] = None


@dataclass
class ChannelConfig:
    """Individual channel configuration."""

    name: str
    redirector_channel_id: Optional[str]
    output_channel_id: str
    input_channels: Dict[str, ChannelSettings]
    channel_settings_default: ChannelSettings


@dataclass
class MessageQueue:
    """Message queue data structure matching database schema."""

    qid: int  # Maps to existing 'qid' field
    config_name: str  # Maps to existing 'config_name' field
    channel_id: str  # Maps to existing 'channel_id' field
    data: Dict[str, Any]  # Maps to existing 'data' field (JSON)

    @classmethod
    def from_db_row(
        cls, qid: int, config_name: str, channel_id: str, data_json: str
    ) -> "MessageQueue":
        """Create MessageQueue from database row."""
        data = json.loads(data_json) if data_json else {}
        return cls(qid=qid, config_name=config_name, channel_id=channel_id, data=data)

    def to_db_data(self) -> str:
        """Convert data to JSON string for database storage."""
        return json.dumps(self.data)


@dataclass
class QueueData:
    """Structure of the data field in MessageQueue."""

    channel_id: str
    min_id: int
    max_id: int
    open: bool
    messages: List[Any] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "channel_id": self.channel_id,
            "min_id": self.min_id,
            "max_id": self.max_id,
            "open": self.open,
            "messages": self.messages,
        }


@dataclass
class TimerInfo:
    """Timer information for queue management."""

    timer_id: str
    config_name: str
    channel_id: str
    timer_type: str  # 'close', 'update', 'sending'


@dataclass
class SendingStatus:
    """Sending status tracking."""

    config_name: str
    in_progress: bool = False
    last_update: Optional[float] = None


# Type aliases for better readability
TimerDict = Dict[str, Dict[str, Any]]
EntityDict = Dict[str, Any]
ChannelEntityDict = Dict[str, List[Any]]
ConfigList = List[ChannelConfig]
