"""
Purge Cog for Discord Verify Bot.
Contains slash commands for purging messages with various filters.
"""

import logging
import asyncio
from typing import Optional
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands

from src.config import Config
from src.utils.checks import is_guild_only, bot_has_manage_roles_permission


async def has_purge_permission(interaction: discord.Interaction) -> bool:
    """Check if the user has permission to use purge commands.
    
    Args:
        interaction: The interaction to check
        
    Returns:
        bool: True if user has permission
        
    Raises:
        app_commands.CheckFailure: If user lacks permission
    """
    await is_guild_only(interaction)
    
    # Server owner always has permission
    if interaction.user == interaction.guild.owner:
        return True
    
    # Role IDs for purge permission
    purge_roles_ids = [1438678850073661572, 1441277347360669718]
    
    # Check for specific roles
    member = interaction.user
    has_permission = False
    
    for role_id in purge_roles_ids:
        role = interaction.guild.get_role(role_id)
        if role and role in member.roles:
            has_permission = True
            break
    
    if not has_permission:
        raise app_commands.CheckFailure(
            "You don't have permission to use this command."
        )
    
    return True


async def bot_has_manage_messages_permission(interaction: discord.Interaction) -> bool:
    """Check if the bot has permission to manage messages.
    
    Args:
        interaction: The interaction to check
        
    Returns:
        bool: True if bot can manage messages
        
    Raises:
        app_commands.CheckFailure: If bot lacks permissions
    """
    if not interaction.guild:
        return True  # Guild check will fail separately
    
    bot_member = interaction.guild.me
    if not bot_member.guild_permissions.manage_messages:
        raise app_commands.CheckFailure(
            "I don't have permission to manage messages. Please contact a server administrator."
        )
    return True


class PurgeCog(commands.Cog):
    """Cog containing message purge commands."""
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.logger = logging.getLogger(__name__)
    
    @app_commands.command(name="purge", description="Purge messages with various filters")
    @app_commands.check(has_purge_permission)
    @app_commands.check(bot_has_manage_messages_permission)
    @app_commands.describe(
        number="Number of messages to purge (1-10000)",
        user="Optional: User to purge messages from",
        all_channels="Optional: Purge from all channels (use with @username)"
    )
    async def purge(
        self,
        interaction: discord.Interaction,
        number: app_commands.Range[int, 1, 10000],
        user: Optional[discord.Member] = None,
        all_channels: Optional[bool] = None
    ) -> None:
        """Purge messages with various filters.
        
        Args:
            interaction: The interaction that triggered the command
            number: Number of messages to purge (1-10000)
            user: Optional member to filter messages by
            all_channels: Whether to purge from all channels (only with user)
        """
        # Validate that all_channels is only used with user
        if all_channels and not user:
            await interaction.response.send_message(
                "The 'all_channels' option can only be used when specifying a user with @username.",
                ephemeral=True
            )
            return
        
        # Defer the response since purging can take time
        await interaction.response.defer(ephemeral=True)
        
        try:
            if all_channels and user:
                # Purge from all channels except excluded categories
                await self._purge_all_channels(interaction, number, user)
            elif user:
                # Purge from current channel for specific user
                await self._purge_channel_user(interaction, number, user)
            else:
                # Purge from current channel (all messages)
                await self._purge_channel(interaction, number)
                
        except Exception as e:
            self.logger.error(f"Error in purge command: {e}")
            await interaction.followup.send(
                "An unexpected error occurred while purging messages. Please try again later.",
                ephemeral=True
            )
    
    async def _purge_channel(self, interaction: discord.Interaction, number: int) -> None:
        """Purge messages from the current channel.
        
        Args:
            interaction: The interaction that triggered the command
            number: Number of messages to purge
        """
        channel = interaction.channel
        
        # Calculate cutoff time (1 day ago)
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=1)
        
        # Use purge method for bulk deletion
        def is_old_and_not_pinned(message):
            return not message.pinned and message.created_at < cutoff_time
        
        deleted = await channel.purge(limit=number, check=is_old_and_not_pinned)
        
        # Log the action
        self.logger.info(
            f"User {interaction.user} (ID: {interaction.user.id}) purged "
            f"{len(deleted)} messages from #{channel.name} (ID: {channel.id})"
        )
        
        await interaction.followup.send(
            f"Successfully purged {len(deleted)} messages from this channel (only messages older than 1 day).",
            ephemeral=True
        )
    
    async def _purge_channel_user(self, interaction: discord.Interaction, number: int, user: discord.Member) -> None:
        """Purge messages from a specific user in the current channel.
        
        Args:
            interaction: The interaction that triggered the command
            number: Number of messages to purge
            user: The member whose messages to purge
        """
        channel = interaction.channel
        
        # Calculate cutoff time (1 day ago)
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=1)
        
        def is_from_user_and_old(message):
            return message.author.id == user.id and not message.pinned and message.created_at < cutoff_time
        
        deleted = await channel.purge(limit=number, check=is_from_user_and_old)
        
        # Log the action
        self.logger.info(
            f"User {interaction.user} (ID: {interaction.user.id}) purged "
            f"{len(deleted)} messages from {user} (ID: {user.id}) in #{channel.name} (ID: {channel.id})"
        )
        
        await interaction.followup.send(
            f"Successfully purged {len(deleted)} messages from {user.mention} in this channel (only messages older than 1 day).",
            ephemeral=True
        )
    
    async def _purge_all_channels(self, interaction: discord.Interaction, number: int, user: discord.Member) -> None:
        """Purge messages from a specific user across all channels except excluded categories.
        
        Args:
            interaction: The interaction that triggered the command
            number: Number of messages to purge per channel
            user: The member whose messages to purge
        """
        guild = interaction.guild
        excluded_category_ids = [1438757411589722123, 1438672613957308438]
        total_deleted = 0
        
        # Calculate cutoff time (1 day ago)
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=1)
        
        # Get all text channels that are not in excluded categories
        channels_to_purge = []
        for channel in guild.text_channels:
            if channel.category_id not in excluded_category_ids:
                channels_to_purge.append(channel)
        
        # Purge messages from each channel
        for channel in channels_to_purge:
            try:
                def is_from_user_and_old(message):
                    return message.author.id == user.id and not message.pinned and message.created_at < cutoff_time
                
                deleted = await channel.purge(limit=number, check=is_from_user_and_old)
                total_deleted += len(deleted)
                
                # Small delay to avoid rate limits
                await asyncio.sleep(0.5)
                
            except Exception as e:
                self.logger.warning(f"Failed to purge messages in #{channel.name}: {e}")
                continue
        
        # Log the action
        self.logger.info(
            f"User {interaction.user} (ID: {interaction.user.id}) purged "
            f"{total_deleted} messages from {user} (ID: {user.id}) across {len(channels_to_purge)} channels"
        )
        
        await interaction.followup.send(
            f"Successfully purged {total_deleted} messages from {user.mention} across {len(channels_to_purge)} channels "
            f"(excluding categories {excluded_category_ids[0]} and {excluded_category_ids[1]}, only messages older than 1 day).",
            ephemeral=True
        )
    
    @purge.error
    async def purge_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        """Global error handler for purge commands.
        
        Args:
            interaction: The interaction that caused the error
            error: The error that occurred
        """
        if isinstance(error, app_commands.NoPrivateMessage):
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True
            )
        elif isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(str(error), ephemeral=True)
        elif isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(str(error), ephemeral=True)
        elif isinstance(error, app_commands.RangeError):
            await interaction.response.send_message(
                "Number must be between 1 and 10000.",
                ephemeral=True
            )
        else:
            self.logger.error(f"Unhandled error in purge command: {error}")
            await interaction.response.send_message(
                "An unexpected error occurred. Please try again later.",
                ephemeral=True
            )


async def setup(bot: commands.Bot) -> None:
    """Set up the purge cog.
    
    Args:
        bot: The bot instance
    """
    await bot.add_cog(PurgeCog(bot))