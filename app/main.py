"""
New OOP entry point for Forwardgram application.
Uses the new class-based architecture while maintaining backward compatibility.
"""

import sys
import asyncio
import logging

# Handle imports based on how the module is run
from forwardgram.app import create_forwardgram_app


async def main_async(
    global_config_path: str, tags_config_path: str = None, channel_names: list = None
) -> None:
    """Async main function using new OOP architecture."""
    try:
        # Create application instance
        app = create_forwardgram_app(global_config_path, tags_config_path)

        # Setup logging from global config
        logging.basicConfig(
            level=getattr(logging, app.global_config.logging_level, "INFO"),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        logging.getLogger("telethon").setLevel(level=logging.WARNING)

        # Handle channel discovery mode
        if channel_names:
            await app.setup_channel_discovery(channel_names)
            return

        # Run the application
        await app.run_application()

    except Exception as e:
        logging.error(f"Application failed: {e}")
        sys.exit(1)


def main(
    global_config_path: str = None,
    tags_config_path: str = None,
    channel_names: list = None,
) -> None:
    """Main entry point - synchronous wrapper."""
    # Handle command line arguments if not provided
    if global_config_path is None:
        if len(sys.argv) < 2:
            print(f"Usage: {sys.argv[0]} GLOBAL_CONFIG_PATH [TAGS_CONFIG_PATH]")
            sys.exit(1)

        global_config_path = sys.argv[1]
        tags_config_path = sys.argv[2] if len(sys.argv) > 2 else None

    # Run async main
    try:
        asyncio.run(main_async(global_config_path, tags_config_path, channel_names))
    except KeyboardInterrupt:
        # Gracefully handle Ctrl+C
        logging.getLogger(__name__).info("Application interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
