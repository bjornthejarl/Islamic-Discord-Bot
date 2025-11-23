"""
Economy Cog for Discord Bot
Handles currency system, daily rewards, transfers, and leaderboards.
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional

from src.utils.economy_utils import EconomyUtils

logger = logging.getLogger(__name__)


class EconomyCog(commands.Cog):
    """Economy system with Halal-compliant currency and rewards."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.economy_utils = EconomyUtils()
    
    @app_commands.command(name="balance", description="Check your Ilm Coins and Good Deed Points balance")
    @app_commands.describe(user="Check another user's balance (moderators only)")
    async def balance(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """Check user's economy balance."""
        await interaction.response.defer()
        
        try:
            # Determine which user to check
            target_user = user if user else interaction.user
            
            # Only allow users to check their own balance unless they're moderators
            if user and user != interaction.user:
                # Check if user has moderation permissions
                if not interaction.user.guild_permissions.manage_messages:
                    await interaction.followup.send(
                        "❌ You can only check your own balance unless you have moderation permissions.",
                        ephemeral=True
                    )
                    return
            
            # Get user data
            user_data = await self.economy_utils.get_user_data(target_user.id, interaction.guild.id)
            economy_data = user_data["economy"]
            
            # Create embed
            embed = discord.Embed(
                title=f"💰 {target_user.display_name}'s Balance",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="🪙 Ilm Coins",
                value=f"**{economy_data['ilm_coins']:,}** IC",
                inline=True
            )
            
            embed.add_field(
                name="🌟 Good Deed Points", 
                value=f"**{economy_data['good_deed_points']}** GDP",
                inline=True
            )
            
            embed.add_field(
                name="📊 Statistics",
                value=(
                    f"**Total Earned**: {economy_data['total_earned']:,} IC\n"
                    f"**Total Spent**: {economy_data['total_spent']:,} IC\n"
                    f"**Total Donated**: {economy_data['total_donated']:,} IC"
                ),
                inline=False
            )
            
            # Add daily streak info if checking own balance
            if target_user == interaction.user:
                activities = user_data["activities"]
                if activities["daily_streak"] > 0:
                    embed.add_field(
                        name="🔥 Current Streak",
                        value=f"**{activities['daily_streak']}** days",
                        inline=True
                    )
            
            embed.set_footer(text="Keep learning and earning Ilm Coins!")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in balance command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while checking the balance. Please try again.",
                ephemeral=True
            )
    
    @app_commands.command(name="daily", description="Claim your daily Ilm Coins reward with streak bonuses")
    async def daily(self, interaction: discord.Interaction):
        """Claim daily reward with streak bonuses."""
        await interaction.response.defer()
        
        try:
            result = await self.economy_utils.claim_daily_reward(
                interaction.user.id, 
                interaction.guild.id
            )
            
            if not result["success"]:
                await interaction.followup.send(
                    f"❌ {result['message']}",
                    ephemeral=True
                )
                return
            
            # Create success embed
            embed = discord.Embed(
                title="🎁 Daily Reward Claimed!",
                color=discord.Color.green(),
                description=result["message"]
            )
            
            embed.add_field(
                name="📊 Reward Breakdown",
                value=(
                    f"**Base Reward**: {result['base_reward']} IC\n"
                    f"**Streak Bonus**: +{result['streak_bonus']} IC\n"
                    f"**Total Received**: {result['reward']} IC"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🔥 Current Streak",
                value=f"**Day {result['streak']}**",
                inline=True
            )
            
            # Add weekly bonus info if applicable
            if "weekly_bonus" in result:
                embed.add_field(
                    name="🌟 Weekly Bonus!",
                    value=f"+{result['weekly_bonus']} IC",
                    inline=True
                )
            
            # Calculate next bonus
            next_bonus_day = 7 - (result["streak"] % 7)
            if next_bonus_day == 7:
                next_bonus_day = 0
            
            if next_bonus_day > 0:
                embed.add_field(
                    name="📅 Next Bonus",
                    value=f"**{next_bonus_day}** days until weekly bonus!",
                    inline=False
                )
            
            embed.set_footer(text="Come back tomorrow to continue your streak!")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in daily command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while claiming your daily reward. Please try again.",
                ephemeral=True
            )
    
    @app_commands.command(name="leaderboard", description="View server leaderboards for various metrics")
    @app_commands.describe(
        type="Ranking category",
        scope="Time period scope",
        limit="Number of users to show (max 20)"
    )
    @app_commands.choices(
        type=[
            app_commands.Choice(name="Coins", value="coins"),
            app_commands.Choice(name="Good Deed Points", value="gdp"),
            app_commands.Choice(name="Total Earned", value="earned")
        ],
        scope=[
            app_commands.Choice(name="Global", value="global"),
            app_commands.Choice(name="Monthly", value="monthly"),
            app_commands.Choice(name="Weekly", value="weekly")
        ]
    )
    async def leaderboard(
        self, 
        interaction: discord.Interaction, 
        type: app_commands.Choice[str] = None,
        scope: app_commands.Choice[str] = None,
        limit: app_commands.Range[int, 1, 20] = 10
    ):
        """Display server leaderboard."""
        await interaction.response.defer()
        
        try:
            # Default to coins if not specified
            leaderboard_type = type.value if type else "coins"
            leaderboard_scope = scope.value if scope else "global"
            
            # Get leaderboard data
            leaderboard_data = await self.economy_utils.get_leaderboard(
                interaction.guild.id, 
                limit
            )
            
            if not leaderboard_data:
                await interaction.followup.send(
                    "📊 No economy data found for this server yet. Be the first to earn some Ilm Coins!",
                    ephemeral=True
                )
                return
            
            # Sort based on selected type
            if leaderboard_type == "gdp":
                leaderboard_data.sort(key=lambda x: x["good_deed_points"], reverse=True)
                title_suffix = "Good Deed Points"
                value_key = "good_deed_points"
                icon = "🌟"
            elif leaderboard_type == "earned":
                leaderboard_data.sort(key=lambda x: x["total_earned"], reverse=True)
                title_suffix = "Total Earned"
                value_key = "total_earned"
                icon = "💰"
            else:  # coins
                title_suffix = "Ilm Coins"
                value_key = "ilm_coins"
                icon = "🪙"
            
            # Create embed
            embed = discord.Embed(
                title=f"🏆 {leaderboard_scope.title()} {title_suffix} Leaderboard",
                color=discord.Color.blue(),
                description=f"Top {limit} users in {interaction.guild.name}"
            )
            
            # Build leaderboard text
            leaderboard_text = ""
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            
            for i, user_data in enumerate(leaderboard_data):
                try:
                    user = await self.bot.fetch_user(user_data["user_id"])
                    username = user.display_name
                except:
                    username = f"User {user_data['user_id']}"
                
                medal = medals[i] if i < len(medals) else f"{i+1}."
                value = user_data[value_key]
                
                leaderboard_text += f"{medal} **{username}** - {value:,} {icon}\n"
            
            embed.add_field(
                name="Rankings",
                value=leaderboard_text or "No data available",
                inline=False
            )
            
            # Find current user's position
            current_user_pos = None
            for i, user_data in enumerate(leaderboard_data):
                if user_data["user_id"] == interaction.user.id:
                    current_user_pos = i + 1
                    break
            
            if current_user_pos:
                embed.set_footer(text=f"Your position: #{current_user_pos} - Keep going!")
            else:
                embed.set_footer(text="You're not on the leaderboard yet. Start earning!")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in leaderboard command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while fetching the leaderboard. Please try again.",
                ephemeral=True
            )
    
    @app_commands.command(name="transfer", description="Transfer Ilm Coins to another user")
    @app_commands.describe(
        user="User to transfer coins to",
        amount="Amount to transfer (10-1000)",
        message="Optional transfer note"
    )
    async def transfer(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        amount: app_commands.Range[int, 10, 1000],
        message: Optional[str] = None
    ):
        """Transfer coins to another user."""
        await interaction.response.defer()
        
        try:
            # Prevent self-transfer
            if user.id == interaction.user.id:
                await interaction.followup.send(
                    "❌ You cannot transfer coins to yourself.",
                    ephemeral=True
                )
                return
            
            # Prevent transferring to bots
            if user.bot:
                await interaction.followup.send(
                    "❌ You cannot transfer coins to bots.",
                    ephemeral=True
                )
                return
            
            # Perform transfer
            success = await self.economy_utils.transfer_coins(
                interaction.user.id,
                user.id,
                interaction.guild.id,
                amount
            )
            
            if not success:
                await interaction.followup.send(
                    "❌ Transfer failed. You may not have enough coins, or the amount is outside allowed limits.",
                    ephemeral=True
                )
                return
            
            # Create success embed
            embed = discord.Embed(
                title="💸 Transfer Successful",
                color=discord.Color.green(),
                description=f"✅ Sent **{amount:,} Ilm Coins** to {user.mention}"
            )
            
            if message:
                embed.add_field(
                    name="💬 Note",
                    value=f"\"{message}\"",
                    inline=False
                )
            
            # Get sender's new balance
            sender_data = await self.economy_utils.get_user_data(interaction.user.id, interaction.guild.id)
            embed.add_field(
                name="📊 Your New Balance",
                value=f"**{sender_data['economy']['ilm_coins']:,}** Ilm Coins",
                inline=False
            )
            
            embed.set_footer(text="Generosity is rewarded in Islam! 🌟")
            
            await interaction.followup.send(embed=embed)
            
            # Notify recipient (if they allow DMs)
            try:
                recipient_embed = discord.Embed(
                    title="🎁 You Received a Gift!",
                    color=discord.Color.gold(),
                    description=f"**{interaction.user.display_name}** sent you **{amount:,} Ilm Coins**!"
                )
                
                if message:
                    recipient_embed.add_field(
                        name="💬 Message",
                        value=f"\"{message}\"",
                        inline=False
                    )
                
                await user.send(embed=recipient_embed)
            except:
                # User has DMs disabled, that's okay
                pass
            
        except Exception as e:
            logger.error(f"Error in transfer command: {e}")
            await interaction.followup.send(
                "❌ An error occurred during the transfer. Please try again.",
                ephemeral=True
            )
    
    @app_commands.command(name="donate", description="Donate Ilm Coins to community funds")
    @app_commands.describe(
        amount="Amount to donate",
        cause="Donation purpose"
    )
    @app_commands.choices(
        cause=[
            app_commands.Choice(name="General Community Fund", value="general"),
            app_commands.Choice(name="Education & Learning", value="education"),
            app_commands.Choice(name="Charity Projects", value="charity"),
            app_commands.Choice(name="Server Maintenance", value="community")
        ]
    )
    async def donate(
        self,
        interaction: discord.Interaction,
        amount: app_commands.Range[int, 10, 10000],
        cause: app_commands.Choice[str] = None
    ):
        """Donate coins to community causes."""
        await interaction.response.defer()
        
        try:
            cause_name = cause.name if cause else "General Community Fund"
            cause_value = cause.value if cause else "general"
            
            # Remove coins for donation
            success = await self.economy_utils.remove_coins(
                interaction.user.id,
                interaction.guild.id,
                amount,
                f"donation_{cause_value}"
            )
            
            if not success:
                await interaction.followup.send(
                    "❌ Donation failed. You may not have enough coins.",
                    ephemeral=True
                )
                return
            
            # Update user's donation total
            user_data = await self.economy_utils.get_user_data(interaction.user.id, interaction.guild.id)
            user_data["economy"]["total_donated"] += amount
            await self.economy_utils.save_user_data(interaction.user.id, interaction.guild.id, user_data)
            
            # Add Good Deed Points (1 GDP per 20 coins donated)
            gdp_earned = amount // 20
            user_data["economy"]["good_deed_points"] += gdp_earned
            
            await self.economy_utils.save_user_data(interaction.user.id, interaction.guild.id, user_data)
            
            # Create success embed
            embed = discord.Embed(
                title="🕌 Donation Received",
                color=discord.Color.green(),
                description=f"✅ Donated **{amount:,} Ilm Coins** to **{cause_name}**"
            )
            
            embed.add_field(
                name="🌟 Good Deed Points",
                value=f"+{gdp_earned} GDP",
                inline=True
            )
            
            embed.add_field(
                name="📊 Total Donated",
                value=f"{user_data['economy']['total_donated']:,} IC",
                inline=True
            )
            
            # Add Islamic quote about charity
            charity_quotes = [
                "\"Those who spend their wealth in charity day and night, secretly and openly—their reward is with their Lord...\" (Quran 2:274)",
                "\"The example of those who spend their wealth in the Way of Allah is that of a grain that sprouts seven ears, in every ear there are a hundred grains...\" (Quran 2:261)",
                "\"You will not attain righteousness until you spend from what you love. And whatever you spend of anything, indeed, Allah is Knowing of it.\" (Quran 3:92)"
            ]
            
            import random
            embed.add_field(
                name="📖 Islamic Wisdom",
                value=random.choice(charity_quotes),
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in donate command: {e}")
            await interaction.followup.send(
                "❌ An error occurred during the donation. Please try again.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Add the economy cog to the bot."""
    await bot.add_cog(EconomyCog(bot))
    logger.info("Economy cog loaded successfully")