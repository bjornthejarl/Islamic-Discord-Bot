"""
Profile Cog for Discord Bot
Handles user profiles, achievements, and progression tracking.
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging
import json
import os
from typing import Optional
from datetime import datetime

from src.utils.economy_utils import EconomyUtils

logger = logging.getLogger(__name__)


class ProfileCog(commands.Cog):
    """User profile system with achievements and progression tracking."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.economy_utils = EconomyUtils()
        self.achievements = self.load_achievements()
    
    def load_achievements(self):
        """Load achievements configuration."""
        try:
            achievements_path = os.path.join("src", "data", "profiles", "achievements.json")
            if os.path.exists(achievements_path):
                with open(achievements_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Create default achievements
                default_achievements = {
                    "achievements": [
                        {
                            "id": "first_steps",
                            "name": "First Steps",
                            "description": "Complete your first quiz",
                            "icon": "🚶",
                            "category": "learning",
                            "requirement": {"quizzes_completed": 1},
                            "reward": {"coins": 50, "good_deed_points": 5}
                        },
                        {
                            "id": "quran_scholar",
                            "name": "Quran Scholar",
                            "description": "Complete 10 Quran-related quizzes",
                            "icon": "📖",
                            "category": "knowledge",
                            "requirement": {"quran_quizzes_completed": 10},
                            "reward": {"coins": 200, "good_deed_points": 20}
                        },
                        {
                            "id": "generous_soul",
                            "name": "Generous Soul",
                            "description": "Donate 1000 Ilm Coins to charity",
                            "icon": "💝",
                            "category": "charity",
                            "requirement": {"total_donated": 1000},
                            "reward": {"coins": 500, "good_deed_points": 50}
                        },
                        {
                            "id": "daily_devotee",
                            "name": "Daily Devotee",
                            "description": "Maintain a 7-day daily reward streak",
                            "icon": "🔥",
                            "category": "consistency",
                            "requirement": {"daily_streak": 7},
                            "reward": {"coins": 300, "good_deed_points": 25}
                        },
                        {
                            "id": "knowledge_seeker",
                            "name": "Knowledge Seeker",
                            "description": "Complete 25 total games and quizzes",
                            "icon": "🧠",
                            "category": "learning",
                            "requirement": {"games_played": 25},
                            "reward": {"coins": 400, "good_deed_points": 30}
                        },
                        {
                            "id": "verse_master",
                            "name": "Verse Master",
                            "description": "Correctly match 15 Quran verses",
                            "icon": "🎯",
                            "category": "knowledge",
                            "requirement": {"verse_matches_correct": 15},
                            "reward": {"coins": 350, "good_deed_points": 35}
                        },
                        {
                            "id": "hadith_expert",
                            "name": "Hadith Expert",
                            "description": "Complete 10 Hadith trivia games",
                            "icon": "📜",
                            "category": "knowledge",
                            "requirement": {"hadith_games_completed": 10},
                            "reward": {"coins": 250, "good_deed_points": 20}
                        },
                        {
                            "id": "community_pillar",
                            "name": "Community Pillar",
                            "description": "Reach 100 Good Deed Points",
                            "icon": "🌟",
                            "category": "charity",
                            "requirement": {"good_deed_points": 100},
                            "reward": {"coins": 600, "good_deed_points": 50}
                        },
                        {
                            "id": "wealth_of_knowledge",
                            "name": "Wealth of Knowledge",
                            "description": "Earn 5000 total Ilm Coins",
                            "icon": "💰",
                            "category": "economy",
                            "requirement": {"total_earned": 5000},
                            "reward": {"coins": 1000, "good_deed_points": 75}
                        },
                        {
                            "id": "islamic_artisan",
                            "name": "Islamic Artisan",
                            "description": "Purchase 5 different shop items",
                            "icon": "🛍️",
                            "category": "economy",
                            "requirement": {"unique_items_purchased": 5},
                            "reward": {"coins": 450, "good_deed_points": 40}
                        }
                    ]
                }
                os.makedirs(os.path.dirname(achievements_path), exist_ok=True)
                with open(achievements_path, 'w', encoding='utf-8') as f:
                    json.dump(default_achievements, f, indent=2, ensure_ascii=False)
                return default_achievements
        except Exception as e:
            logger.error(f"Error loading achievements: {e}")
            return {"achievements": []}
    
    async def check_achievements(self, user_id: int, guild_id: int, user_data: dict):
        """Check and award achievements based on user progress."""
        try:
            # Load obtained achievements from DB
            rows = await self.economy_utils.db.fetchall(
                "SELECT achievement_id FROM user_achievements WHERE user_id = ? AND guild_id = ?",
                (user_id, guild_id)
            )
            obtained_achievements = {row['achievement_id'] for row in rows}
            
            new_achievements = []
            
            # Check each achievement
            for achievement in self.achievements["achievements"]:
                achievement_id = achievement["id"]
                
                # Skip if already achieved
                if achievement_id in obtained_achievements:
                    continue
                
                # Check requirements
                requirement_met = True
                for req_key, req_value in achievement["requirement"].items():
                    if req_key in user_data["economy"]:
                        if user_data["economy"][req_key] < req_value:
                            requirement_met = False
                            break
                    elif req_key in user_data["activities"]:
                        if user_data["activities"][req_key] < req_value:
                            requirement_met = False
                            break
                    else:
                        requirement_met = False
                        break
                
                if requirement_met:
                    # Award achievement in DB
                    try:
                        await self.economy_utils.db.execute(
                            "INSERT INTO user_achievements (user_id, guild_id, achievement_id) VALUES (?, ?, ?)",
                            (user_id, guild_id, achievement_id)
                        )
                        await self.economy_utils.db.commit()
                        
                        # Apply rewards
                        if "reward" in achievement:
                            reward = achievement["reward"]
                            if "coins" in reward:
                                await self.economy_utils.add_coins(
                                    user_id, guild_id, reward["coins"], f"achievement_{achievement_id}"
                                )
                            if "good_deed_points" in reward:
                                # Update GDP directly as add_coins doesn't touch GDP
                                await self.economy_utils.db.execute(
                                    "UPDATE users SET good_deed_points = good_deed_points + ? WHERE user_id = ? AND guild_id = ?",
                                    (reward["good_deed_points"], user_id, guild_id)
                                )
                                await self.economy_utils.db.commit()
                        
                        new_achievements.append(achievement)
                        obtained_achievements.add(achievement_id)
                        
                    except Exception as e:
                        logger.error(f"Error awarding achievement {achievement_id}: {e}")
            
            return new_achievements
            
        except Exception as e:
            logger.error(f"Error checking achievements: {e}")
            return []
    
    @app_commands.command(name="profile", description="View your profile and achievements")
    @app_commands.describe(user="View another user's profile")
    async def profile(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """Display user profile with stats and achievements."""
        await interaction.response.defer()
        
        try:
            target_user = user if user else interaction.user
            
            # Get user data
            user_data = await self.economy_utils.get_user_data(target_user.id, interaction.guild.id)
            
            # Get achievements
            rows = await self.economy_utils.db.fetchall(
                "SELECT achievement_id FROM user_achievements WHERE user_id = ? AND guild_id = ?",
                (target_user.id, interaction.guild.id)
            )
            user_achievements = [row['achievement_id'] for row in rows]
            
            # Create profile embed
            embed = discord.Embed(
                title=f"👤 {target_user.display_name}'s Profile",
                color=target_user.color if target_user.color else discord.Color.blue(),
                description=f"Islamic learning journey of {target_user.mention}"
            )
            
            # Add economy stats
            economy = user_data["economy"]
            activities = user_data["activities"]
            
            embed.add_field(
                name="💰 Economy",
                value=(
                    f"**Ilm Coins:** {economy['ilm_coins']:,} IC\n"
                    f"**Good Deed Points:** {economy['good_deed_points']} GDP\n"
                    f"**Total Earned:** {economy['total_earned']:,} IC\n"
                    f"**Total Donated:** {economy['total_donated']:,} IC"
                ),
                inline=True
            )
            
            # Add activity stats
            embed.add_field(
                name="📊 Activities",
                value=(
                    f"**Games Played:** {activities['games_played']}\n"
                    f"**Quizzes Completed:** {activities['quizzes_completed']}\n"
                    f"**Daily Streak:** {activities['daily_streak']} days\n"
                    f"**Learning Time:** {activities['total_learning_time'] // 60} mins"
                ),
                inline=True
            )
            
            # Add achievements count
            achievement_count = len(user_achievements)
            total_achievements = len(self.achievements["achievements"])
            
            embed.add_field(
                name="🏆 Achievements",
                value=f"**{achievement_count}/{total_achievements}** unlocked",
                inline=True
            )
            
            # Add recent achievements (last 3 - loosely approximating by taking last in list, 
            # though DB retrieval order isn't guaranteed without ORDER BY. 
            # For strictness we could select achieved_at)
            
            if user_achievements:
                # Re-fetch with date sorting to get actual recent ones
                recent_rows = await self.economy_utils.db.fetchall(
                    "SELECT achievement_id FROM user_achievements WHERE user_id = ? AND guild_id = ? ORDER BY achieved_at DESC LIMIT 3",
                    (target_user.id, interaction.guild.id)
                )
                recent_ids = [r['achievement_id'] for r in recent_rows]
                
                achievement_text = ""
                for ach_id in recent_ids:
                    achievement = next((a for a in self.achievements["achievements"] if a["id"] == ach_id), None)
                    if achievement:
                        achievement_text += f"{achievement['icon']} {achievement['name']}\n"
                
                if achievement_text:
                    embed.add_field(
                        name="✨ Recent Achievements",
                        value=achievement_text,
                        inline=False
                    )
            
            # Calculate user level based on total earned
            level = (economy["total_earned"] // 1000) + 1
            embed.set_footer(text=f"Level {level} • Keep learning and growing in knowledge!")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in profile command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while loading the profile. Please try again.",
                ephemeral=True
            )
    
    @app_commands.command(name="achievements", description="View all available achievements and your progress")
    async def achievements(self, interaction: discord.Interaction):
        """Display all achievements and user progress."""
        await interaction.response.defer()
        
        try:
            user_data = await self.economy_utils.get_user_data(interaction.user.id, interaction.guild.id)
            
            # Get achievements
            rows = await self.economy_utils.db.fetchall(
                "SELECT achievement_id FROM user_achievements WHERE user_id = ? AND guild_id = ?",
                (interaction.user.id, interaction.guild.id)
            )
            user_achievements = {row['achievement_id'] for row in rows}
            
            # Create achievements embed
            embed = discord.Embed(
                title="🏆 Achievements",
                color=discord.Color.gold(),
                description="Track your progress in Islamic learning and good deeds"
            )
            
            achieved_count = 0
            categories = {}
            
            # Organize achievements by category
            for achievement in self.achievements["achievements"]:
                category = achievement["category"]
                if category not in categories:
                    categories[category] = []
                categories[category].append(achievement)
            
            # Add achievements by category
            for category, achievements_list in categories.items():
                category_text = ""
                
                for achievement in achievements_list:
                    is_achieved = achievement["id"] in user_achievements
                    
                    if is_achieved:
                        achieved_count += 1
                        category_text += f"✅ **{achievement['name']}** - {achievement['description']}\n"
                    else:
                        # Show progress for unachieved
                        progress_text = ""
                        for req_key, req_value in achievement["requirement"].items():
                            current_value = 0
                            if req_key in user_data["economy"]:
                                current_value = user_data["economy"][req_key]
                            elif req_key in user_data["activities"]:
                                current_value = user_data["activities"][req_key]
                            
                            progress = min(current_value / req_value * 100, 100)
                            progress_text += f" ({current_value}/{req_value})"
                        
                        category_text += f"❌ {achievement['name']} - {achievement['description']}{progress_text}\n"
                
                if category_text:
                    # Count for category
                    cat_achieved = len([a for a in achievements_list if a['id'] in user_achievements])
                    embed.add_field(
                        name=f"{category.title()} ({cat_achieved}/{len(achievements_list)})",
                        value=category_text,
                        inline=False
                    )
            
            total_achievements = len(self.achievements["achievements"])
            embed.set_footer(text=f"Progress: {achieved_count}/{total_achievements} achievements unlocked")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in achievements command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while loading achievements. Please try again.",
                ephemeral=True
            )
    
    @app_commands.command(name="profile_leaderboard", description="View detailed server leaderboards including achievements")
    @app_commands.describe(
        type="Leaderboard type",
        limit="Number of users to show (max 15)"
    )
    @app_commands.choices(type=[
        app_commands.Choice(name="Ilm Coins", value="coins"),
        app_commands.Choice(name="Good Deed Points", value="gdp"),
        app_commands.Choice(name="Achievements", value="achievements"),
        app_commands.Choice(name="Total Earned", value="earned"),
        app_commands.Choice(name="Games Played", value="games")
    ])
    async def profile_leaderboard(self, interaction: discord.Interaction, type: app_commands.Choice[str], limit: app_commands.Range[int, 1, 15] = 10):
        """Display detailed server leaderboard."""
        await interaction.response.defer()
        
        try:
            # We need customized queries for this compared to economy_utils.get_leaderboard
            
            if type.value == "achievements":
                # Special query for achievements count
                rows = await self.economy_utils.db.fetchall(
                    """
                    SELECT user_id, COUNT(*) as count 
                    FROM user_achievements 
                    WHERE guild_id = ? 
                    GROUP BY user_id 
                    ORDER BY count DESC 
                    LIMIT ?
                    """,
                    (interaction.guild.id, limit)
                )
                leaderboard_data = [{"user_id": r["user_id"], "value": r["count"]} for r in rows]
                title = "🏆 Achievements Leaderboard"
                icon = "🏆"
                
            else:
                # Use standard users table
                order_col = "ilm_coins"
                if type.value == "gdp": order_col = "good_deed_points"
                elif type.value == "earned": order_col = "total_earned"
                elif type.value == "games": order_col = "games_played"
                
                rows = await self.economy_utils.db.fetchall(
                    f"SELECT user_id, {order_col} as value FROM users WHERE guild_id = ? ORDER BY {order_col} DESC LIMIT ?",
                    (interaction.guild.id, limit)
                )
                leaderboard_data = [{"user_id": r["user_id"], "value": r["value"]} for r in rows]
                
                if type.value == "gdp":
                    title = "🌟 Good Deed Points Leaderboard"
                    icon = "🌟"
                elif type.value == "earned":
                    title = "💰 Total Earned Leaderboard"
                    icon = "💰"
                elif type.value == "games":
                    title = "🎮 Games Played Leaderboard"
                    icon = "🎮"
                else:
                    title = "🪙 Ilm Coins Leaderboard"
                    icon = "🪙"
            
            if not leaderboard_data:
                await interaction.followup.send(
                    "📊 No user data found for this server yet. Be the first to start earning!",
                    ephemeral=True
                )
                return
            
            # Create embed
            embed = discord.Embed(
                title=title,
                color=discord.Color.blue(),
                description=f"Top {limit} users in {interaction.guild.name}"
            )
            
            # Build leaderboard text
            leaderboard_text = ""
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            
            for i, entry in enumerate(leaderboard_data):
                try:
                    user = await self.bot.fetch_user(entry["user_id"])
                    username = user.display_name
                except:
                    username = f"User {entry['user_id']}"
                
                medal = medals[i] if i < len(medals) else f"{i+1}."
                value = entry["value"]
                
                leaderboard_text += f"{medal} **{username}** - {value:,} {icon}\n"
            
            embed.add_field(
                name="Rankings",
                value=leaderboard_text or "No data available",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in leaderboard command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while fetching the leaderboard. Please try again.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Add the profile cog to the bot."""
    await bot.add_cog(ProfileCog(bot))
    logger.info("Profile cog loaded successfully")
