"""
Logging setup for Discord Verify Bot.
Provides structured console logging with consistent formatting.
"""

import logging
import sys
from typing import Optional


def setup_logging(level: Optional[int] = logging.INFO) -> None:
    """Set up structured console logging for the bot.
    
    Args:
        level: Logging level (default: logging.INFO)
    """
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add our handler
    root_logger.addHandler(console_handler)
    
    # Set specific loggers to avoid spam
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    logging.info("Logging setup complete")