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
            profile_path = os.path.join("src", "data", "profiles", f"{user_id}_{guild_id}.json")
            
            # Load user profile
            profile = {}
            if os.path.exists(profile_path):
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
            
            if "achievements" not in profile:
                profile["achievements"] = {}
            
            new_achievements = []
            
            # Check each achievement
            for achievement in self.achievements["achievements"]:
                achievement_id = achievement["id"]
                
                # Skip if already achieved
                if achievement_id in profile["achievements"]:
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
                    # Award achievement
                    profile["achievements"][achievement_id] = {
                        "achieved_at": datetime.now().isoformat(),
                        "reward_claimed": False
                    }
                    
                    # Apply rewards
                    if "reward" in achievement:
                        reward = achievement["reward"]
                        if "coins" in reward:
                            await self.economy_utils.add_coins(
                                user_id, guild_id, reward["coins"], f"achievement_{achievement_id}"
                            )
                        if "good_deed_points" in reward:
                            user_data["economy"]["good_deed_points"] += reward["good_deed_points"]
                    
                    new_achievements.append(achievement)
            
            # Save updated profile
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
            
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
            
            # Load profile
            profile_path = os.path.join("src", "data", "profiles", f"{target_user.id}_{interaction.guild.id}.json")
            profile = {}
            if os.path.exists(profile_path):
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
            
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
            achievement_count = len(profile.get("achievements", {}))
            total_achievements = len(self.achievements["achievements"])
            
            embed.add_field(
                name="🏆 Achievements",
                value=f"**{achievement_count}/{total_achievements}** unlocked",
                inline=True
            )
            
            # Add recent achievements (last 3)
            if "achievements" in profile:
                recent_achievements = list(profile["achievements"].keys())[-3:]
                if recent_achievements:
                    achievement_text = ""
                    for ach_id in recent_achievements:
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
            # Load user profile
            profile_path = os.path.join("src", "data", "profiles", f"{interaction.user.id}_{interaction.guild.id}.json")
            profile = {}
            if os.path.exists(profile_path):
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
            
            user_data = await self.economy_utils.get_user_data(interaction.user.id, interaction.guild.id)
            
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
                    is_achieved = achievement["id"] in profile.get("achievements", {})
                    
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
                    embed.add_field(
                        name=f"{category.title()} ({len([a for a in achievements_list if a['id'] in profile.get('achievements', {})])}/{len(achievements_list)})",
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
            # This would require scanning all user files in the server
            # For now, we'll use the existing economy leaderboard and extend it
            
            leaderboard_data = await self.economy_utils.get_leaderboard(interaction.guild.id, limit)
            
            if not leaderboard_data:
                await interaction.followup.send(
                    "📊 No user data found for this server yet. Be the first to start earning!",
                    ephemeral=True
                )
                return
            
            # Sort based on selected type
            if type.value == "gdp":
                leaderboard_data.sort(key=lambda x: x["good_deed_points"], reverse=True)
                title = "🌟 Good Deed Points Leaderboard"
                value_key = "good_deed_points"
                icon = "🌟"
            elif type.value == "achievements":
                # This would require loading profiles - for now use a placeholder
                leaderboard_data.sort(key=lambda x: x["total_earned"], reverse=True)
                title = "🏆 Achievements Leaderboard"
                value_key = "total_earned"
                icon = "🏆"
            elif type.value == "earned":
                leaderboard_data.sort(key=lambda x: x["total_earned"], reverse=True)
                title = "💰 Total Earned Leaderboard"
                value_key = "total_earned"
                icon = "💰"
            elif type.value == "games":
                leaderboard_data.sort(key=lambda x: x.get("games_played", 0), reverse=True)
                title = "🎮 Games Played Leaderboard"
                value_key = "games_played"
                icon = "🎮"
            else:  # coins
                title = "🪙 Ilm Coins Leaderboard"
                value_key = "ilm_coins"
                icon = "🪙"
            
            # Create embed
            embed = discord.Embed(
                title=title,
                color=discord.Color.blue(),
                description=f"Top {limit} users in {interaction.guild.name}"
            )
            
            # Build leaderboard text
            leaderboard_text = ""
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟", "⏸️", "⏸️", "⏸️", "⏸️", "⏸️"]
            
            for i, user_data in enumerate(leaderboard_data[:limit]):
                try:
                    user = await self.bot.fetch_user(user_data["user_id"])
                    username = user.display_name
                except:
                    username = f"User {user_data['user_id']}"
                
                medal = medals[i] if i < len(medals) else f"{i+1}."
                value = user_data.get(value_key, 0)
                
                if type.value == "achievements":
                    # Placeholder for achievements count
                    value = user_data.get("total_earned", 0) // 1000
                
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


async def setup(bot: commands.Bot):
    """Add the profile cog to the bot."""
    await bot.add_cog(ProfileCog(bot))
    logger.info("Profile cog loaded successfully")