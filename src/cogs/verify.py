"""
Verify Cog for Discord Verify Bot.
Contains slash commands for verifying users with gender-specific roles.
"""

import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from src.config import Config
from src.utils.checks import (
    has_female_verifier_role,
    has_male_verifier_role,
    is_not_bot,
    bot_has_manage_roles_permission,
)


class VerifyCog(commands.Cog):
    """Cog containing verification commands."""
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.logger = logging.getLogger(__name__)
    
    @app_commands.command(name="verify_female", description="Verify a user as female")
    @app_commands.check(has_female_verifier_role)
    @app_commands.check(bot_has_manage_roles_permission)
    @app_commands.describe(user="The user to verify as female")
    async def verify_female(
        self,
        interaction: discord.Interaction,
        user: discord.Member
    ) -> None:
        """Verify a user as female by assigning the female role.
        
        Args:
            interaction: The interaction that triggered the command
            user: The member to verify
        """
        await self._verify_user(interaction, user, Config.FEMALE_ROLE_ID, Config.FEMALE_REMOVE_ROLE_ID, "female")
    
    @app_commands.command(name="verify_male", description="Verify a user as male")
    @app_commands.check(has_male_verifier_role)
    @app_commands.check(bot_has_manage_roles_permission)
    @app_commands.describe(user="The user to verify as male")
    async def verify_male(
        self,
        interaction: discord.Interaction,
        user: discord.Member
    ) -> None:
        """Verify a user as male by assigning the male role.
        
        Args:
            interaction: The interaction that triggered the command
            user: The member to verify
        """
        await self._verify_user(interaction, user, Config.MALE_ROLE_ID, Config.MALE_REMOVE_ROLE_ID, "male")
    
    async def _verify_user(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        role_id: int,
        remove_role_id: int,
        gender: str
    ) -> None:
        """Internal method to handle user verification logic.
        
        Args:
            interaction: The interaction that triggered the command
            user: The member to verify
            role_id: The role ID to assign
            remove_role_id: The role ID to remove
            gender: The gender being assigned (for messages)
        """
        try:
            # Check if target is a bot
            await is_not_bot(user)
            
            # Get the role from the guild
            role = interaction.guild.get_role(role_id)
            if not role:
                await interaction.response.send_message(
                    f"Error: The {gender} role (ID: {role_id}) was not found in this server. "
                    "Please contact an administrator.",
                    ephemeral=True
                )
                return
            
            # Check if user already has the role
            if role in user.roles:
                await interaction.response.send_message(
                    f"{user.mention} is already verified as {gender}.",
                    ephemeral=True
                )
                return
            
            # Assign the role
            await user.add_roles(role)
            
            # Remove the remove_role if it exists
            remove_role = interaction.guild.get_role(remove_role_id)
            role_removed = False
            if remove_role and remove_role in user.roles:
                await user.remove_roles(remove_role)
                role_removed = True
            
            # Log the action
            self.logger.info(
                f"User {interaction.user} (ID: {interaction.user.id}) verified "
                f"{user} (ID: {user.id}) as {gender}"
            )
            if role_removed:
                self.logger.info(
                    f"Removed role {remove_role_id} from user {user} (ID: {user.id})"
                )
            
            # Send success response
            if role_removed:
                await interaction.response.send_message(
                    f"Successfully verified {user.mention} as {gender} and removed the unverified role.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"Successfully verified {user.mention} as {gender}.",
                    ephemeral=True
                )
            
        except app_commands.CheckFailure as e:
            # Permission or check failures
            await interaction.response.send_message(str(e), ephemeral=True)
        except discord.Forbidden:
            # Bot lacks permissions
            await interaction.response.send_message(
                "I don't have permission to manage roles. Please check my permissions.",
                ephemeral=True
            )
            self.logger.error(f"Bot lacks permissions to manage roles in guild {interaction.guild_id}")
        except Exception as e:
            # Unexpected errors
            self.logger.error(f"Error in verify command: {e}")
            await interaction.response.send_message(
                "An unexpected error occurred. Please try again later.",
                ephemeral=True
            )
    
    @verify_female.error
    @verify_male.error
    async def verify_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        """Global error handler for verify commands.
        
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
        else:
            self.logger.error(f"Unhandled error in verify command: {error}")
            await interaction.response.send_message(
                "An unexpected error occurred. Please try again later.",
                ephemeral=True
            )


async def setup(bot: commands.Bot) -> None:
    """Set up the verify cog.
    
    Args:
        bot: The bot instance
    """
    await bot.add_cog(VerifyCog(bot))