#!/usr/bin/env python3
"""
Discord Verify Bot Entry Point
Handles bot startup, command syncing, and cog loading.
"""

import os
import asyncio
import logging
import signal
from typing import Optional

import discord
from discord.ext import commands
from dotenv import load_dotenv

from src.config import Config
from src.logging_setup import setup_logging


class VerifyBot(commands.Bot):
    """Custom bot class with command syncing functionality."""
    
    def __init__(self) -> None:
        # Set up intents - members intent is required for role management
        # We don't need message_content intent since we only use slash commands
        intents = discord.Intents.default()
        intents.members = True  # This requires privileged gateway intents to be enabled
        intents.message_content = False  # Disable message content since we don't need it
        
        super().__init__(
            command_prefix="!",  # Set a dummy prefix to avoid NoneType errors
            intents=intents,
            help_command=None
        )
        
    async def setup_hook(self) -> None:
        """Called when the bot is starting up, before connecting to Discord."""
        # Load the verify cog
        await self.load_extension("src.cogs.verify")
        logging.info("Loaded verify cog")
        
        # Load the purge cog
        await self.load_extension("src.cogs.purge")
        logging.info("Loaded purge cog")
        
        # Load the moderation cog
        await self.load_extension("src.cogs.moderation")
        logging.info("Loaded moderation cog")
        
        # Load the economy cog
        await self.load_extension("src.cogs.economy")
        logging.info("Loaded economy cog")
        
        # Load the games cog
        await self.load_extension("src.cogs.games")
        logging.info("Loaded games cog")
        
        # Load the shop cog
        await self.load_extension("src.cogs.shop")
        logging.info("Loaded shop cog")
        
        # Load the profile cog
        await self.load_extension("src.cogs.profile")
        logging.info("Loaded profile cog")
        
        # Load the help cog
        await self.load_extension("src.cogs.help")
        logging.info("Loaded help cog")
        
        # Load the quran cog
        await self.load_extension("quran")
        logging.info("Loaded quran cog")
        
    async def on_ready(self) -> None:
        """Called when the bot has successfully connected to Discord."""
        logging.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logging.info(f"Connected to {len(self.guilds)} guilds")
        
        # Sync commands globally
        try:
            synced_commands = await self.tree.sync()
            logging.info(f"Synced {len(synced_commands)} commands globally")
            
            # Log the command names that were synced
            command_names = [cmd.name for cmd in synced_commands]
            logging.info(f"Synced commands: {', '.join(command_names)}")
            
        except Exception as e:
            logging.error(f"Failed to sync commands: {e}")


async def main() -> None:
    """Main entry point for the bot."""
    # Load environment variables from .env file in current directory
    load_dotenv()
    
    # Set up logging
    setup_logging()
    
    # Re-import config after loading environment variables to ensure latest values
    from importlib import reload
    from src import config
    reload(config)
    from src.config import Config
    
    # Validate configuration
    if not Config.DISCORD_TOKEN:
        logging.error("DISCORD_TOKEN environment variable is not set")
        logging.error("Please make sure you have a .env file with DISCORD_TOKEN in the same directory as bot.py")
        logging.error(f"Current working directory: {os.getcwd()}")
        logging.error(f"Looking for .env file at: {os.path.join(os.getcwd(), '.env')}")
        return
    
    # Create the bot
    bot = VerifyBot()
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logging.info("Received shutdown signal, closing bot gracefully...")
        asyncio.create_task(bot.close())
    
    # Register signal handlers for graceful shutdown
    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    except AttributeError:
        # signal.SIGTERM might not be available on Windows
        pass
    
    try:
        await bot.start(Config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        logging.info("Bot stopped by user (KeyboardInterrupt)")
    except discord.PrivilegedIntentsRequired as e:
        logging.error("Bot requires privileged intents that are not enabled in the Discord Developer Portal.")
        logging.error("Please go to https://discord.com/developers/applications/")
        logging.error("Select your application -> Bot -> Enable 'SERVER MEMBERS INTENT'")
        logging.error("Then try running the bot again.")
    except Exception as e:
        logging.error(f"Bot crashed: {e}")
    finally:
        if not bot.is_closed():
            await bot.close()
        logging.info("Bot has been shut down gracefully")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot shutdown completed")