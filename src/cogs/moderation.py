"""
Moderation Cog for Discord Verify Bot.
Contains slash commands for ban, mute, and kick with role-based permissions.
"""

import logging
import asyncio
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from src.config import Config
from src.utils.checks import is_guild_only, bot_has_manage_roles_permission


# Role IDs for permission checks
BAN_ROLE_ID = 1438678850073661572
KICK_ROLES_IDS = [1438678850073661572, 1441277347360669718]
PURGE_ROLES_IDS = [1438678850073661572, 1441277347360669718]


async def has_ban_permission(interaction: discord.Interaction) -> bool:
    """Check if the user has permission to use ban commands.
    
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
    
    # Check for specific role
    member = interaction.user
    role = interaction.guild.get_role(BAN_ROLE_ID)
    
    if not role:
        raise app_commands.CheckFailure(
            "The required moderator role was not found in this server."
        )
    
    if role not in member.roles:
        raise app_commands.CheckFailure(
            "You don't have permission to use this command."
        )
    
    return True


async def has_kick_permission(interaction: discord.Interaction) -> bool:
    """Check if the user has permission to use kick commands.
    
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
    
    # Check for specific roles
    member = interaction.user
    has_permission = False
    
    for role_id in KICK_ROLES_IDS:
        role = interaction.guild.get_role(role_id)
        if role and role in member.roles:
            has_permission = True
            break
    
    if not has_permission:
        raise app_commands.CheckFailure(
            "You don't have permission to use this command."
        )
    
    return True


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
    
    # Check for specific roles
    member = interaction.user
    has_permission = False
    
    for role_id in PURGE_ROLES_IDS:
        role = interaction.guild.get_role(role_id)
        if role and role in member.roles:
            has_permission = True
            break
    
    if not has_permission:
        raise app_commands.CheckFailure(
            "You don't have permission to use this command."
        )
    
    return True


async def bot_has_ban_permission(interaction: discord.Interaction) -> bool:
    """Check if the bot has permission to ban members.
    
    Args:
        interaction: The interaction to check
        
    Returns:
        bool: True if bot can ban members
        
    Raises:
        app_commands.CheckFailure: If bot lacks permissions
    """
    if not interaction.guild:
        return True  # Guild check will fail separately
    
    bot_member = interaction.guild.me
    if not bot_member.guild_permissions.ban_members:
        raise app_commands.CheckFailure(
            "I don't have permission to ban members. Please contact a server administrator."
        )
    return True


async def bot_has_kick_permission(interaction: discord.Interaction) -> bool:
    """Check if the bot has permission to kick members.
    
    Args:
        interaction: The interaction to check
        
    Returns:
        bool: True if bot can kick members
        
    Raises:
        app_commands.CheckFailure: If bot lacks permissions
    """
    if not interaction.guild:
        return True  # Guild check will fail separately
    
    bot_member = interaction.guild.me
    if not bot_member.guild_permissions.kick_members:
        raise app_commands.CheckFailure(
            "I don't have permission to kick members. Please contact a server administrator."
        )
    return True


async def bot_has_moderate_members_permission(interaction: discord.Interaction) -> bool:
    """Check if the bot has permission to moderate members (for timeout/mute).
    
    Args:
        interaction: The interaction to check
        
    Returns:
        bool: True if bot can moderate members
        
    Raises:
        app_commands.CheckFailure: If bot lacks permissions
    """
    if not interaction.guild:
        return True  # Guild check will fail separately
    
    bot_member = interaction.guild.me
    if not bot_member.guild_permissions.moderate_members:
        raise app_commands.CheckFailure(
            "I don't have permission to timeout members. Please contact a server administrator."
        )
    return True


class ModerationCog(commands.Cog):
    """Cog containing moderation commands."""
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.logger = logging.getLogger(__name__)
    
    @app_commands.command(name="ban", description="Ban a user from the server")
    @app_commands.check(has_ban_permission)
    @app_commands.check(bot_has_ban_permission)
    @app_commands.describe(
        user="The user to ban",
        reason="The reason for the ban"
    )
    async def ban(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: Optional[str] = None
    ) -> None:
        """Ban a user from the server.
        
        Args:
            interaction: The interaction that triggered the command
            user: The member to ban
            reason: The reason for the ban
        """
        try:
            # Check if target is a bot
            if user.bot:
                await interaction.response.send_message(
                    "You cannot ban bots.",
                    ephemeral=True
                )
                return
            
            # Check if trying to ban self
            if user == interaction.user:
                await interaction.response.send_message(
                    "You cannot ban yourself.",
                    ephemeral=True
                )
                return
            
            # Check if trying to ban the server owner
            if user == interaction.guild.owner:
                await interaction.response.send_message(
                    "You cannot ban the server owner.",
                    ephemeral=True
                )
                return
            
            # Check if user has higher permissions
            if interaction.user != interaction.guild.owner and user.top_role >= interaction.user.top_role:
                await interaction.response.send_message(
                    "You cannot ban someone with equal or higher permissions than you.",
                    ephemeral=True
                )
                return
            
            # Ban the user
            if reason:
                await user.ban(reason=f"{reason} (Banned by {interaction.user})")
            else:
                await user.ban(reason=f"Banned by {interaction.user}")
            
            # Log the action
            self.logger.info(
                f"User {interaction.user} (ID: {interaction.user.id}) banned "
                f"{user} (ID: {user.id}) with reason: {reason or 'No reason provided'}"
            )
            
            # Send success response
            if reason:
                await interaction.response.send_message(
                    f"Successfully banned {user.mention} for: {reason}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"Successfully banned {user.mention}.",
                    ephemeral=True
                )
                
        except Exception as e:
            self.logger.error(f"Error in ban command: {e}")
            await interaction.response.send_message(
                "An unexpected error occurred while banning the user. Please try again later.",
                ephemeral=True
            )
    
    @app_commands.command(name="banid", description="Ban a user by their user ID")
    @app_commands.check(has_ban_permission)
    @app_commands.check(bot_has_ban_permission)
    @app_commands.describe(
        user_id="The user ID to ban",
        reason="The reason for the ban"
    )
    async def banid(
        self,
        interaction: discord.Interaction,
        user_id: str,
        reason: Optional[str] = None
    ) -> None:
        """Ban a user by their user ID. Useful for banning users who have left the server.
        
        Args:
            interaction: The interaction that triggered the command
            user_id: The ID of the user to ban
            reason: The reason for the ban
        """
        try:
            # Parse the user ID
            try:
                uid = int(user_id.strip())
            except ValueError:
                await interaction.response.send_message(
                    "Invalid user ID. Please provide a valid numeric user ID.",
                    ephemeral=True
                )
                return
            
            # Check if trying to ban self
            if uid == interaction.user.id:
                await interaction.response.send_message(
                    "You cannot ban yourself.",
                    ephemeral=True
                )
                return
            
            # Check if trying to ban the server owner
            if uid == interaction.guild.owner_id:
                await interaction.response.send_message(
                    "You cannot ban the server owner.",
                    ephemeral=True
                )
                return
            
            # Check if trying to ban the bot
            if uid == self.bot.user.id:
                await interaction.response.send_message(
                    "I cannot ban myself.",
                    ephemeral=True
                )
                return
            
            # Check if user is in the server and has higher role
            member = interaction.guild.get_member(uid)
            if member:
                if member.bot:
                    await interaction.response.send_message(
                        "You cannot ban bots.",
                        ephemeral=True
                    )
                    return
                
                if interaction.user != interaction.guild.owner and member.top_role >= interaction.user.top_role:
                    await interaction.response.send_message(
                        "You cannot ban someone with equal or higher permissions than you.",
                        ephemeral=True
                    )
                    return
            
            # Ban the user by ID
            user_object = discord.Object(id=uid)
            if reason:
                await interaction.guild.ban(user_object, reason=f"{reason} (Banned by {interaction.user})")
            else:
                await interaction.guild.ban(user_object, reason=f"Banned by {interaction.user}")
            
            # Log the action
            self.logger.info(
                f"User {interaction.user} (ID: {interaction.user.id}) banned "
                f"user ID {uid} with reason: {reason or 'No reason provided'}"
            )
            
            # Send success response
            if reason:
                await interaction.response.send_message(
                    f"Successfully banned user ID `{uid}` for: {reason}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"Successfully banned user ID `{uid}`.",
                    ephemeral=True
                )
                
        except discord.NotFound:
            await interaction.response.send_message(
                "User not found. Please check the user ID.",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have permission to ban this user.",
                ephemeral=True
            )
        except Exception as e:
            self.logger.error(f"Error in banid command: {e}")
            await interaction.response.send_message(
                "An unexpected error occurred while banning the user. Please try again later.",
                ephemeral=True
            )
    
    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.check(has_kick_permission)
    @app_commands.check(bot_has_kick_permission)
    @app_commands.describe(
        user="The user to kick",
        reason="The reason for the kick"
    )
    async def kick(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: Optional[str] = None
    ) -> None:
        """Kick a user from the server.
        
        Args:
            interaction: The interaction that triggered the command
            user: The member to kick
            reason: The reason for the kick
        """
        try:
            # Check if target is a bot
            if user.bot:
                await interaction.response.send_message(
                    "You cannot kick bots.",
                    ephemeral=True
                )
                return
            
            # Check if trying to kick self
            if user == interaction.user:
                await interaction.response.send_message(
                    "You cannot kick yourself.",
                    ephemeral=True
                )
                return
            
            # Check if trying to kick the server owner
            if user == interaction.guild.owner:
                await interaction.response.send_message(
                    "You cannot kick the server owner.",
                    ephemeral=True
                )
                return
            
            # Check if user has higher permissions
            if interaction.user != interaction.guild.owner and user.top_role >= interaction.user.top_role:
                await interaction.response.send_message(
                    "You cannot kick someone with equal or higher permissions than you.",
                    ephemeral=True
                )
                return
            
            # Kick the user
            if reason:
                await user.kick(reason=f"{reason} (Kicked by {interaction.user})")
            else:
                await user.kick(reason=f"Kicked by {interaction.user}")
            
            # Log the action
            self.logger.info(
                f"User {interaction.user} (ID: {interaction.user.id}) kicked "
                f"{user} (ID: {user.id}) with reason: {reason or 'No reason provided'}"
            )
            
            # Send success response
            if reason:
                await interaction.response.send_message(
                    f"Successfully kicked {user.mention} for: {reason}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"Successfully kicked {user.mention}.",
                    ephemeral=True
                )
                
        except Exception as e:
            self.logger.error(f"Error in kick command: {e}")
            await interaction.response.send_message(
                "An unexpected error occurred while kicking the user. Please try again later.",
                ephemeral=True
            )
    
    @app_commands.command(name="mute", description="Mute a user for a specified period")
    @app_commands.check(has_ban_permission)  # Use ban permission for mute as well
    @app_commands.check(bot_has_moderate_members_permission)
    @app_commands.describe(
        user="The user to mute",
        period="The period to mute for (e.g., 1h, 30m, 1d)",
        reason="The reason for the mute"
    )
    async def mute(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        period: str,
        reason: Optional[str] = None
    ) -> None:
        """Mute a user for a specified period using timeout.
        
        Args:
            interaction: The interaction that triggered the command
            user: The member to mute
            period: The period to mute for (e.g., 1h, 30m, 1d)
            reason: The reason for the mute
        """
        try:
            # Check if target is a bot
            if user.bot:
                await interaction.response.send_message(
                    "You cannot mute bots.",
                    ephemeral=True
                )
                return
            
            # Check if trying to mute self
            if user == interaction.user:
                await interaction.response.send_message(
                    "You cannot mute yourself.",
                    ephemeral=True
                )
                return
            
            # Check if trying to mute the server owner
            if user == interaction.guild.owner:
                await interaction.response.send_message(
                    "You cannot mute the server owner.",
                    ephemeral=True
                )
                return
            
            # Check if user has higher permissions
            if interaction.user != interaction.guild.owner and user.top_role >= interaction.user.top_role:
                await interaction.response.send_message(
                    "You cannot mute someone with equal or higher permissions than you.",
                    ephemeral=True
                )
                return
            
            # Parse the period
            seconds = self._parse_time(period)
            if seconds is None:
                await interaction.response.send_message(
                    "Invalid time format. Use formats like: 1h, 30m, 1d, 2w",
                    ephemeral=True
                )
                return
            
            # Maximum timeout is 28 days (2419200 seconds)
            if seconds > 2419200:
                await interaction.response.send_message(
                    "The maximum mute period is 28 days.",
                    ephemeral=True
                )
                return
            
            # Apply timeout
            duration = discord.utils.utcnow() + discord.timedelta(seconds=seconds)
            if reason:
                await user.timeout(duration, reason=f"{reason} (Muted by {interaction.user})")
            else:
                await user.timeout(duration, reason=f"Muted by {interaction.user}")
            
            # Log the action
            self.logger.info(
                f"User {interaction.user} (ID: {interaction.user.id}) muted "
                f"{user} (ID: {user.id}) for {period} with reason: {reason or 'No reason provided'}"
            )
            
            # Send success response
            if reason:
                await interaction.response.send_message(
                    f"Successfully muted {user.mention} for {period} for: {reason}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"Successfully muted {user.mention} for {period}.",
                    ephemeral=True
                )
                
        except Exception as e:
            self.logger.error(f"Error in mute command: {e}")
            await interaction.response.send_message(
                "An unexpected error occurred while muting the user. Please try again later.",
                ephemeral=True
            )
    
    def _parse_time(self, time_str: str) -> Optional[int]:
        """Parse a time string into seconds.
        
        Args:
            time_str: The time string to parse (e.g., 1h, 30m, 1d)
            
        Returns:
            Optional[int]: The number of seconds, or None if invalid
        """
        time_str = time_str.lower().strip()
        
        # Define multipliers
        multipliers = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400,
            'w': 604800
        }
        
        # Try to parse the time
        for unit, multiplier in multipliers.items():
            if time_str.endswith(unit):
                try:
                    number = float(time_str[:-1])
                    return int(number * multiplier)
                except ValueError:
                    return None
        
        # If no unit specified, assume minutes
        try:
            return int(float(time_str) * 60)
        except ValueError:
            return None
    
    @ban.error
    @banid.error
    @kick.error
    @mute.error
    async def moderation_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        """Global error handler for moderation commands.
        
        Args:
            interaction: The interaction that caused the error
            error: The error that occurred
        """
        if isinstance(error, app_commands.NoPrivateMessage):
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True
            )
        elif isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(str(error), ephemeral=True)
        else:
            self.logger.error(f"Unhandled error in moderation command: {error}")
            await interaction.response.send_message(
                "An unexpected error occurred. Please try again later.",
                ephemeral=True
            )


async def setup(bot: commands.Bot) -> None:
    """Set up the moderation cog.
    
    Args:
        bot: The bot instance
    """
    await bot.add_cog(ModerationCog(bot))