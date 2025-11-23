"""
Utility checks for Discord Verify Bot.
Contains reusable permission checks and validation functions.
"""

import discord
from discord import app_commands
from discord.ext import commands

from src.config import Config


async def is_guild_only(interaction: discord.Interaction) -> bool:
    """Check if the command is being used in a guild (not DMs).
    
    Args:
        interaction: The interaction to check
        
    Returns:
        bool: True if in a guild, False otherwise
    """
    if not interaction.guild:
        raise app_commands.NoPrivateMessage(
            "This command can only be used in a server."
        )
    return True


async def has_female_verifier_role(interaction: discord.Interaction) -> bool:
    """Check if the user has the female verifier role.
    
    Args:
        interaction: The interaction to check
        
    Returns:
        bool: True if user has the role, False otherwise
        
    Raises:
        app_commands.MissingPermissions: If user lacks the required role
    """
    await is_guild_only(interaction)
    
    member = interaction.user
    role = interaction.guild.get_role(Config.FEMALE_VERIFIER_ROLE_ID)
    
    if not role:
        raise app_commands.CheckFailure(
            f"Female verifier role (ID: {Config.FEMALE_VERIFIER_ROLE_ID}) not found in this server."
        )
    
    if role not in member.roles:
        raise app_commands.MissingPermissions(
            f"You need the {role.name} role to use this command."
        )
    
    return True


async def has_male_verifier_role(interaction: discord.Interaction) -> bool:
    """Check if the user has the male verifier role.
    
    Args:
        interaction: The interaction to check
        
    Returns:
        bool: True if user has the role, False otherwise
        
    Raises:
        app_commands.MissingPermissions: If user lacks the required role
    """
    await is_guild_only(interaction)
    
    member = interaction.user
    role = interaction.guild.get_role(Config.MALE_VERIFIER_ROLE_ID)
    
    if not role:
        raise app_commands.CheckFailure(
            f"Male verifier role (ID: {Config.MALE_VERIFIER_ROLE_ID}) not found in this server."
        )
    
    if role not in member.roles:
        raise app_commands.MissingPermissions(
            f"You need the {role.name} role to use this command."
        )
    
    return True


async def is_not_bot(member: discord.Member) -> bool:
    """Check if the target member is not a bot.
    
    Args:
        member: The member to check
        
    Returns:
        bool: True if member is not a bot
        
    Raises:
        app_commands.CheckFailure: If member is a bot
    """
    if member.bot:
        raise app_commands.CheckFailure("You cannot verify bots.")
    return True


async def bot_has_manage_roles_permission(interaction: discord.Interaction) -> bool:
    """Check if the bot has permission to manage roles.
    
    Args:
        interaction: The interaction to check
        
    Returns:
        bool: True if bot can manage roles
        
    Raises:
        app_commands.CheckFailure: If bot lacks permissions
    """
    if not interaction.guild:
        return True  # Guild check will fail separately
    
    bot_member = interaction.guild.me
    if not bot_member.guild_permissions.manage_roles:
        raise app_commands.CheckFailure(
            "I don't have permission to manage roles. Please contact a server administrator."
        )
    return True