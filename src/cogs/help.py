"""
Help Cog for Discord Bot
Provides comprehensive help information via DMs.
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)


class HelpCog(commands.Cog):
    """Help system that provides command information via DMs."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="help", description="Get comprehensive help information sent to your DMs")
    async def help_command(self, interaction: discord.Interaction):
        """Send a comprehensive help embed to the user's DMs."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Create main help embed
            main_embed = discord.Embed(
                title="🕌 Islamic Discord Bot - Help Center",
                color=discord.Color.blue(),
                description=(
                    "Welcome to the Islamic Discord Bot! This bot helps you learn about Islam "
                    "through educational games and an economy system based on Islamic principles.\n\n"
                    "**📖 All commands are slash commands** - type `/` to see available commands."
                )
            )
            
            main_embed.add_field(
                name="📚 Quick Start",
                value=(
                    "1. Use `/daily` to claim your daily Ilm Coins\n"
                    "2. Play `/quiz` to test your Islamic knowledge\n"
                    "3. Check `/balance` to see your progress\n"
                    "4. Use `/leaderboard` to see server rankings"
                ),
                inline=False
            )
            
            main_embed.set_footer(text="Scroll down for detailed command information!")
            
            # Create verification commands embed
            verify_embed = discord.Embed(
                title="✅ Verification Commands",
                color=discord.Color.green(),
                description="Commands for user verification and role management"
            )
            
            verify_embed.add_field(
                name="`/verify_female`",
                value="Verify a user as female (Female Verifier role required)",
                inline=False
            )
            
            verify_embed.add_field(
                name="`/verify_male`",
                value="Verify a user as male (Male Verifier role required)", 
                inline=False
            )
            
            # Create moderation commands embed
            mod_embed = discord.Embed(
                title="🛡️ Moderation Commands",
                color=discord.Color.red(),
                description="Server management and moderation tools"
            )
            
            mod_embed.add_field(
                name="`/ban`",
                value="Ban a user from the server",
                inline=False
            )
            
            mod_embed.add_field(
                name="`/kick`",
                value="Kick a user from the server",
                inline=False
            )
            
            mod_embed.add_field(
                name="`/mute`",
                value="Temporarily mute a user",
                inline=False
            )
            
            mod_embed.add_field(
                name="`/purge`",
                value="Delete messages (only messages older than 1 day)",
                inline=False
            )
            
            # Create economy commands embed
            economy_embed = discord.Embed(
                title="💰 Economy Commands",
                color=discord.Color.gold(),
                description="Manage your Ilm Coins and Good Deed Points"
            )
            
            economy_embed.add_field(
                name="`/balance`",
                value="Check your Ilm Coins and Good Deed Points",
                inline=False
            )
            
            economy_embed.add_field(
                name="`/daily`",
                value="Claim daily rewards with streak bonuses",
                inline=False
            )
            
            economy_embed.add_field(
                name="`/leaderboard`",
                value="View server rankings by coins, GDP, or total earned",
                inline=False
            )
            
            economy_embed.add_field(
                name="`/transfer`",
                value="Send Ilm Coins to another user (10-1000 coins)",
                inline=False
            )
            
            economy_embed.add_field(
                name="`/donate`",
                value="Donate coins to community funds and earn Good Deed Points",
                inline=False
            )
            
            # Create games commands embed
            games_embed = discord.Embed(
                title="🎮 Educational Games",
                color=discord.Color.purple(),
                description="Learn about Islam through interactive games"
            )
            
            games_embed.add_field(
                name="`/quiz`",
                value=(
                    "Islamic knowledge quiz with multiple categories:\n"
                    "• Quran • Hadith • Prophets • Prayer • Calendar\n"
                    "Earn coins based on difficulty and performance"
                ),
                inline=False
            )
            
            games_embed.add_field(
                name="`/verse_match`",
                value=(
                    "Match Quran verses to their correct surahs\n"
                    "Includes hints and difficulty levels"
                ),
                inline=False
            )
            
            games_embed.add_field(
                name="`/hadith_game`",
                value=(
                    "Hadith trivia with different modes:\n"
                    "• Completion • Knowledge • Narrator\n"
                    "Learn about Hadith sciences"
                ),
                inline=False
            )
            
            # Create tips and information embed
            tips_embed = discord.Embed(
                title="💡 Tips & Information",
                color=discord.Color.orange(),
                description="Helpful information to get the most from the bot"
            )
            
            tips_embed.add_field(
                name="🎁 Earning Ilm Coins",
                value=(
                    "• Daily rewards with streak bonuses\n"
                    "• Educational games and quizzes\n"
                    "• Community contributions\n"
                    "• Charity and generosity"
                ),
                inline=False
            )
            
            tips_embed.add_field(
                name="🌟 Good Deed Points",
                value=(
                    "• Earned through donations (1 GDP per 20 coins)\n"
                    "• Represent your charitable contributions\n"
                    "• Special rewards in future updates"
                ),
                inline=False
            )
            
            tips_embed.add_field(
                name="📊 Progression",
                value=(
                    "• Track your learning through games\n"
                    "• Compete on leaderboards\n"
                    "• More features coming soon!"
                ),
                inline=False
            )
            
            tips_embed.add_field(
                name="🕌 Islamic Principles",
                value=(
                    "• All games are educational and Halal-compliant\n"
                    "• No gambling or interest-based mechanics\n"
                    "• Encourages knowledge seeking and charity"
                ),
                inline=False
            )
            
            # Try to send all embeds to user's DMs
            try:
                await interaction.user.send(embed=main_embed)
                await interaction.user.send(embed=verify_embed)
                await interaction.user.send(embed=mod_embed)
                await interaction.user.send(embed=economy_embed)
                await interaction.user.send(embed=games_embed)
                await interaction.user.send(embed=tips_embed)
                
                success_embed = discord.Embed(
                    title="✅ Help Information Sent!",
                    color=discord.Color.green(),
                    description="I've sent a comprehensive help guide to your DMs! 📬\n\nIf you didn't receive it, please check your privacy settings and allow DMs from server members."
                )
                
                await interaction.followup.send(embed=success_embed, ephemeral=True)
                
            except discord.Forbidden:
                # User has DMs disabled
                error_embed = discord.Embed(
                    title="❌ Cannot Send DMs",
                    color=discord.Color.red(),
                    description=(
                        "I couldn't send you a DM with the help information.\n\n"
                        "**Please enable DMs in your privacy settings:**\n"
                        "1. Go to User Settings ⚙️\n"
                        "2. Click on Privacy & Safety\n"
                        "3. Enable 'Allow direct messages from server members'\n"
                        "4. Try the `/help` command again"
                    )
                )
                
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            error_embed = discord.Embed(
                title="❌ Error",
                color=discord.Color.red(),
                description="An error occurred while processing your help request. Please try again."
            )
            
            await interaction.followup.send(embed=error_embed, ephemeral=True)
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Send welcome message when bot joins a new guild."""
        try:
            # Find a system channel or first text channel
            channel = guild.system_channel
            if not channel:
                # Try to find first text channel where bot can send messages
                for ch in guild.text_channels:
                    if ch.permissions_for(guild.me).send_messages:
                        channel = ch
                        break
            
            if channel:
                welcome_embed = discord.Embed(
                    title="🕌 Islamic Bot Has Joined!",
                    color=discord.Color.blue(),
                    description=(
                        "Thank you for adding me to your server! "
                        "I'm here to help with Islamic education and community building.\n\n"
                        "**Get Started:**\n"
                        "• Use `/help` for a complete command guide\n"
                        "• Set up verification roles in `src/config.py`\n"
                        "• Use `/daily` to start earning Ilm Coins"
                    )
                )
                
                welcome_embed.add_field(
                    name="📚 Key Features",
                    value=(
                        "✅ User verification system\n"
                        "🛡️ Moderation tools\n"
                        "💰 Halal economy with Ilm Coins\n"
                        "🎮 Educational Islamic games\n"
                        "🌟 Good Deed Points for charity"
                    ),
                    inline=False
                )
                
                welcome_embed.set_footer(text="Use /help for detailed information!")
                
                await channel.send(embed=welcome_embed)
                
        except Exception as e:
            logger.error(f"Error sending welcome message to guild {guild.id}: {e}")


async def setup(bot: commands.Bot):
    """Add the help cog to the bot."""
    await bot.add_cog(HelpCog(bot))
    logger.info("Help cog loaded successfully")