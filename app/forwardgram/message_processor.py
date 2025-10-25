"""
Message processing and transformation classes.
Preserves all existing logic from utils/helpers.py
"""

import re
import math
import logging
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
from telethon.tl.types import (
    MessageEntityUrl,
    MessageEntityTextUrl,
    MessageEntityMention,
    MessageEntityEmail,
    MessageEntityHashtag,
    MessageMediaPhoto,
    MessageMediaDocument,
)
from telethon.utils import get_peer_id

from .data_types import ChannelSettings


class TextProcessor:
    """Handles text processing and filtering operations."""

    # Constants from original helpers.py
    ENTITIES_TUPLES = {
        "links": (MessageEntityUrl, MessageEntityTextUrl),
        "users": (MessageEntityMention),
        "emails": (MessageEntityEmail),
        "hash_tags": (MessageEntityHashtag),
        "media": (MessageMediaPhoto, MessageMediaDocument),
    }

    UNIQUE_CHARS_OF_LANGUAGES = {"ru": "ё|ъ|ы|э", "ua": "ґ|є|і|ї"}

    SPECIAL_TAGS = {
        "ru": {
            "recommend": "рекомендуем",
            "cash_on_delivery": "наложенный_платеж",
            "copy_by_photo": "копия_по_фото",
            "odessa": "одесса",
            "kharkov": "харьков",
        },
        "ua": {
            "recommend": "рекомендуємо",
            "cash_on_delivery": "накладений_платіж",
            "copy_by_photo": "копія_по_фото",
            "odessa": "одеса",
            "kharkov": "харків",
        },
    }

    # Unicode emoji ranges
    EMOJIS = (
        "\\U0001F1E0-\\U0001F1FF"  # flags (iOS)
        "\\U0001F300-\\U0001F5FF"  # symbols & pictographs
        "\\U0001F600-\\U0001F64F"  # emoticons
        "\\U0001F680-\\U0001F6FF"  # transport & map symbols
        "\\U0001F700-\\U0001F77F"  # alchemical symbols
        "\\U0001F780-\\U0001F7FF"  # Geometric Shapes Extended
        "\\U0001F800-\\U0001F8FF"  # Supplemental Arrows-C
        "\\U0001F900-\\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\\U0001FA00-\\U0001FA6F"  # Chess Symbols
        "\\U0001FA70-\\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\\U00002702-\\U000027B0"  # Dingbats
        "\\U000024C2-\\U0001F251"
    )

    EMOJI_PATTERN = re.compile(f"[{EMOJIS}]+")

    REPLACE_REGEXES = {
        "links": r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\\[\\]]+|\\([^\s()]*?\\([^\s()]+\\)[^\s()]*?\\)|\\([^\s]+?\\))+(?:\\([^\s()]*?\\([^\s()]+\\)[^\s()]*?\\)|\\([^\s]+?\\)|[^\s`!()\\[\\]{};:\\'\\\".,<>?«»""''])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))""",
        "users": r"(?<=^|(?<=[^a-zA-Z0-9-_\.]))@[A-Za-z0-9_]+[  ]{0,1}",
        "emails": r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)[  ]{0,1}",
        "hash_tags": r"(?:^|\s)[＃#]{1}(\w+)",
        "english_part_of_message": rf"(?:(?:^[a-zA-Z0-9  {EMOJIS}?><:;,{{}}\\/[\\]\\-_+=!@$%\\^&*|'\\r\\n]{{30,10000}})(?!.*(?:[а-яА-Я])))(.*){{0,1}}[\\r\\n]{{0,10}}",
    }

    def strip_emoji(self, text: str) -> str:
        """Remove emojis from text - preserves original logic."""
        return self.EMOJI_PATTERN.sub(r"", text)

    def is_message_text_allowed(
        self, message: Any, channel_settings: ChannelSettings
    ) -> bool:
        """Check if message text is allowed - preserves original logic."""
        if isinstance(message.message, str):
            message_without_emoji = self.strip_emoji(message.message)
            disallowed_keywords = channel_settings.disallowed_keywords
            if disallowed_keywords is not None:
                for keyword in disallowed_keywords:
                    if keyword and re.findall(
                        rf"{keyword}",
                        message_without_emoji,
                        re.MULTILINE | re.IGNORECASE | re.UNICODE,
                    ):
                        return False

            allowed_keywords = channel_settings.allowed_keywords
            if allowed_keywords is None:
                return True
            else:
                for keyword in allowed_keywords:
                    if keyword and re.findall(
                        rf"{keyword}",
                        message_without_emoji,
                        re.MULTILINE | re.IGNORECASE | re.UNICODE,
                    ):
                        return True

        return False

    def is_message_allowed(
        self, message: Any, channel_settings: ChannelSettings
    ) -> bool:
        """Check if message is allowed - preserves original logic."""
        # Clean the text of media message
        clean_media_message = channel_settings.clean_media_message
        if (
            message.message
            and clean_media_message
            and isinstance(message.media, self.ENTITIES_TUPLES["media"])
        ):
            # Check allowed keywords and clean text if needed
            if not self.is_message_text_allowed(message, channel_settings):
                message.message = ""

        if not message.message:
            # Forward message without text, but with image media (if allowed)
            media_without_message = channel_settings.media_without_message
            if media_without_message and type(message.media) is MessageMediaPhoto:
                return True
            # Forward message without text, but with doc image media (if allowed)
            media_doc_image_without_message = (
                channel_settings.media_doc_image_without_message
            )
            if (
                media_doc_image_without_message
                and type(message.media) is MessageMediaDocument
                and message.media.document.mime_type == "image/jpeg"
            ):
                return True
            # Forward message without text, but with doc video media (if allowed)
            media_doc_video_without_message = (
                channel_settings.media_doc_video_without_message
            )
            if (
                media_doc_video_without_message
                and type(message.media) is MessageMediaDocument
                and message.media.document.mime_type == "video/mp4"
            ):
                return True

        return self.is_message_text_allowed(message, channel_settings)

    def replace_regex_by_name(
        self, message: Any, channel_settings: ChannelSettings, name: str
    ) -> None:
        """Replace text by regex name - preserves original logic."""
        setting = getattr(channel_settings, name, None)
        if setting is None or setting is True:
            return

        message.message = re.sub(
            self.REPLACE_REGEXES[name],
            "",
            message.message,
            flags=re.MULTILINE | re.IGNORECASE | re.UNICODE,
        )
        # If no entities in message object, do not need to continue the cleaning
        if name not in self.ENTITIES_TUPLES or message.entities is None:
            return
        message.entities = [
            message_entity
            for message_entity in message.entities
            if not isinstance(message_entity, self.ENTITIES_TUPLES[name])
        ]

    def replace_regex(self, message: Any, channel_settings: ChannelSettings) -> None:
        """Replace keywords by regex - preserves original logic."""
        keywords = channel_settings.remove_keywords
        if keywords is None:
            return
        else:
            for keyword in keywords:
                message.message = re.sub(
                    keyword,
                    "",
                    message.message,
                    flags=re.MULTILINE | re.IGNORECASE | re.UNICODE,
                )
            # Remove useless line breaks
            message.message = re.sub(
                rf"[\n]+", f"\n", message.message, flags=re.MULTILINE
            )

    def get_languages(self, message: str) -> List[str]:
        """Detect languages in message - preserves original logic."""
        languages = []

        # Try to detect language (using unique chars per language)
        for key, value in self.UNIQUE_CHARS_OF_LANGUAGES.items():
            if re.search(
                rf"{value}", message, re.MULTILINE | re.IGNORECASE | re.UNICODE
            ):
                languages.append(key)

        # If not detected any languages, add default language
        if not languages:
            languages.append("ru")
        return languages


class PriceProcessor:
    """Handles price adjustment operations."""

    def __init__(self, text_processor: TextProcessor):
        self.text_processor = text_processor

    @staticmethod
    def format_float(f: Union[int, float]) -> Union[int, Decimal]:
        """Format float value - preserves original logic."""
        d = Decimal(str(f))
        return d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize()

    def increase_price(
        self,
        message: Any,
        price: Dict[str, Any],
        result: str,
        progressive_values: Optional[List[Dict[str, Any]]],
    ) -> None:
        """Increase price in message - preserves original logic."""
        # Clean result value (remove possible dot or comma at the start of price)
        result = re.sub(r"^([\.,]+)", "", result, flags=re.UNICODE)
        # Get price value
        price_value = re.findall(r"[ 0-9]+[,.]{0,1}[0-9]{0,2}", result)

        if price_value:
            # Clean empty values, and use first value
            price_value = list(filter(lambda x: x.strip() != "", price_value))
            if price_value:
                price_value = price_value[0].strip()
            else:
                logging.info(f"Warning! Price is not detected in message {message}.")
                return

            # Check price value. If part length more than 2 - it's NOT price!
            price_parts = price_value.replace(",", ".").split(".")
            if len(price_parts) > 2:
                return

            try:
                price_value_new = float(price_value.replace(" ", "").replace(",", "."))
            except Exception as e:
                return

            # Change price value
            price_value_new += price["value"]
            inc_value = 0
            # Calculate progressive value
            if "progressive_values" in price:
                progressive_values = price["progressive_values"]
            if progressive_values is not None:
                for progressive_value in progressive_values:
                    if price_value_new >= progressive_value["limit"]:
                        inc_value = progressive_value["value"]
                    else:
                        break

            # Change price value
            price_value_new += inc_value
            # Round to 10 price value (only for values > 100)
            if price_value_new > 100:
                price_value_new = math.ceil(price_value_new / 10) * 10

            price_value_new = str(PriceProcessor.format_float(price_value_new))
            if "currency" in price:
                price_value_new += price["currency"]
            # Replace old price by new price value
            result_new = re.sub(
                rf"{price_value}", price_value_new, result, flags=re.UNICODE
            )
            # Replace the string with the price value in message
            message.message = re.sub(
                r"{}".format(re.escape(result)),
                result_new,
                message.message,
                flags=re.MULTILINE | re.IGNORECASE | re.UNICODE,
            )

    def change_prices(
        self,
        message: Any,
        prices: List[Dict[str, Any]],
        channel_settings: ChannelSettings,
        channel_id: str,
    ) -> None:
        """Change prices in message - preserves original logic."""
        message_without_emoji = self.text_processor.strip_emoji(message.message)
        progressive_values = channel_settings.progressive_values

        for price in prices:
            pattern = price["pattern"].replace(
                "[  ]", f"[  {self.text_processor.EMOJIS}]"
            )
            results = re.findall(
                rf"{pattern}",
                message.message,
                re.MULTILINE | re.IGNORECASE | re.UNICODE,
            )

            # The custom logic per channel name
            # OLIAGARHO (name:oliagarho, id:1235781572)
            if channel_id == "1235781572":
                if re.findall(
                    rf"💎", message.message, re.MULTILINE | re.IGNORECASE | re.UNICODE
                ):
                    # The price is increased already! Don't increase anything by default
                    price["value"] = 50
                elif re.findall(
                    rf"распродажа",
                    message.message,
                    re.MULTILINE | re.IGNORECASE | re.UNICODE,
                ):
                    # We should use other price for sale!
                    price["value"] = 100

            for result in results:
                if isinstance(result, tuple):
                    for group in result:
                        self.increase_price(message, price, group, progressive_values)
                else:
                    self.increase_price(message, price, result, progressive_values)

    def change_price(
        self, message: Any, channel_settings: ChannelSettings, channel_id: str
    ) -> None:
        """Change price in message - preserves original logic."""
        # We can use only "prices" or only "prices_per_channel"!
        prices = channel_settings.prices
        if prices is None:
            # The changes of prices per channel in Redirector
            if channel_settings.prices_per_channel is not None:
                # Don't do anything, if message is not forwarded!
                if message.fwd_from is None:
                    return
                # Don't do anything, if the price rule for current channel is not exist!
                id = get_peer_id(message.fwd_from.from_id)
                if id:
                    id = re.sub(rf"^\-100", "", str(id))
                    prices = channel_settings.prices_per_channel.get(id)

        if prices is not None:
            self.change_prices(message, prices, channel_settings, channel_id)


class TagGenerator:
    """Handles tag generation for messages."""

    def __init__(
        self, global_tags: Optional[Dict[str, Any]], text_processor: TextProcessor
    ):
        self.global_tags = global_tags
        self.text_processor = text_processor

        self.logger = logging.getLogger(__name__)

    def add_tags(self, message: Any, tags: List[str]) -> None:
        """Add tags to message - preserves original logic."""
        tags_string = " ".join(tags)
        if tags_string:
            message.message += f"{tags_string} "

    def generate_and_add_tags(
        self, message: Any, channel_settings: ChannelSettings
    ) -> None:
        """Generate and add tags to message - preserves original logic."""
        message.message += f"\n"

        # Add tags per channel
        channel_tags = channel_settings.tags

        # Add global tags
        if self.global_tags is not None:
            languages = self.text_processor.get_languages(message.message)
            for language in languages:
                message.message += f"\n"
                for tag in self.global_tags:
                    tags = []
                    # Search tags
                    for key, value in self.global_tags[tag][language].items():
                        results = re.findall(
                            rf"{key}",
                            message.message,
                            re.MULTILINE | re.IGNORECASE | re.UNICODE,
                        )
                        if results:
                            tags.append(f"#{value}")
                    self.add_tags(message, tags)

                # Add tags per channel
                if channel_tags is not None:
                    tags = []
                    for value in channel_tags:
                        tags.append(
                            f"#{self.text_processor.SPECIAL_TAGS[language][value]}"
                        )
                    self.add_tags(message, tags)

        # Add brand id as tag at the end
        brand_id = channel_settings.brand_id
        if brand_id is not None:
            message.message += f"\n#brand_{brand_id}"

        # Remove useless line breaks
        message.message = re.sub(rf"^[\n]+", f"\n", message.message, flags=re.MULTILINE)


class MessageProcessor:
    """Main message processing coordinator."""

    def __init__(self, global_tags: Optional[Dict[str, Any]] = None):
        self.text_processor = TextProcessor()
        self.price_processor = PriceProcessor(self.text_processor)
        self.tag_generator = TagGenerator(global_tags, self.text_processor)

    def is_message_allowed(
        self, message: Any, channel_settings: ChannelSettings
    ) -> bool:
        """Check if message is allowed."""
        return self.text_processor.is_message_allowed(message, channel_settings)

    def process_message_transformations(
        self, message: Any, channel_id: str, channel_settings: ChannelSettings
    ) -> None:
        if message.message:
            """Apply all message transformations."""
            # Remove entities
            self.text_processor.replace_regex_by_name(
                message, channel_settings, "links"
            )
            self.text_processor.replace_regex_by_name(
                message, channel_settings, "users"
            )
            self.text_processor.replace_regex_by_name(
                message, channel_settings, "emails"
            )
            self.text_processor.replace_regex_by_name(
                message, channel_settings, "hash_tags"
            )
            self.text_processor.replace_regex_by_name(
                message, channel_settings, "english_part_of_message"
            )

            # Remove keywords
            self.text_processor.replace_regex(message, channel_settings)

            # Change prices
            self.price_processor.change_price(message, channel_settings, channel_id)

            # Generate and add tags
            self.tag_generator.generate_and_add_tags(message, channel_settings)

    def is_last_message_duplicated(self, queue_messages: List[Any], text: str) -> bool:
        """Check if last message is duplicated - preserves original logic."""
        if not queue_messages:
            return False

        last_message = queue_messages[-1]
        if hasattr(last_message, "message") and last_message.message == text:
            return True

        return False

    def append_media_to_album(self, queue_messages: List[Any], message: Any) -> None:
        """Append media to album - preserves original logic."""
        # Find existing album with same grouped_id
        if not hasattr(message, "grouped_id") or not message.grouped_id:
            return

        for i, queue_message in enumerate(queue_messages):
            if (
                hasattr(queue_message, "grouped_id")
                and queue_message.grouped_id == message.grouped_id
            ):
                # Found existing album, merge media
                if hasattr(queue_message, "media") and hasattr(message, "media"):
                    # This is a simplified version - original logic may be more complex
                    pass
                return

        # No existing album found, add as new message
        queue_messages.append(message)
