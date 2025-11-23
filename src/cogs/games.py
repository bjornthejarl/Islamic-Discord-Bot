"""
Games Cog for Discord Bot
Handles educational Islamic games with rewards and progression.
"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import logging
from typing import Optional

from src.utils.game_utils import GameUtils, GameSession
from src.utils.economy_utils import EconomyUtils

logger = logging.getLogger(__name__)


class GamesCog(commands.Cog):
    """Educational Islamic games with Halal-compliant rewards."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.game_utils = GameUtils()
        self.economy_utils = EconomyUtils()
        self.game_sessions = GameSession()
    
    @app_commands.command(name="quiz", description="Test your Islamic knowledge with multiple-choice questions")
    @app_commands.describe(
        category="Specific knowledge area",
        difficulty="Question difficulty level"
    )
    @app_commands.choices(
        category=[
            app_commands.Choice(name="Quran", value="quran"),
            app_commands.Choice(name="Hadith", value="hadith"),
            app_commands.Choice(name="Prophets", value="prophets"),
            app_commands.Choice(name="Prayer", value="prayer"),
            app_commands.Choice(name="Calendar", value="calendar"),
            app_commands.Choice(name="Random", value="random")
        ],
        difficulty=[
            app_commands.Choice(name="Easy", value="easy"),
            app_commands.Choice(name="Medium", value="medium"),
            app_commands.Choice(name="Hard", value="hard")
        ]
    )
    async def quiz(
        self, 
        interaction: discord.Interaction, 
        category: app_commands.Choice[str] = None,
        difficulty: app_commands.Choice[str] = None
    ):
        """Start an Islamic knowledge quiz."""
        await interaction.response.defer()
        
        try:
            # Get quiz question
            category_value = category.value if category else None
            difficulty_value = difficulty.value if difficulty else "medium"
            
            question = self.game_utils.get_quiz_question(category_value, difficulty_value)
            
            if not question:
                await interaction.followup.send(
                    "❌ No quiz questions available for the selected category/difficulty. Please try another combination.",
                    ephemeral=True
                )
                return
            
            # Create quiz embed
            embed = discord.Embed(
                title="🧠 Islamic Knowledge Quiz",
                color=discord.Color.blue(),
                description=f"**{question['question']}**"
            )
            
            # Add category and difficulty info
            embed.add_field(
                name="📚 Category",
                value=question['category'].title(),
                inline=True
            )
            
            embed.add_field(
                name="🎯 Difficulty", 
                value=question['difficulty'].title(),
                inline=True
            )
            
            embed.add_field(
                name="🏆 Points",
                value=f"{question['points']}",
                inline=True
            )
            
            # Create options with letters
            options_text = ""
            letters = ["A", "B", "C", "D"]
            for i, option in enumerate(question['options']):
                options_text += f"**{letters[i]}.** {option}\n"
            
            embed.add_field(
                name="📝 Options",
                value=options_text,
                inline=False
            )
            
            embed.set_footer(text="You have 30 seconds to answer! React with the corresponding letter.")
            
            # Send quiz message
            quiz_message = await interaction.followup.send(embed=embed)
            
            # Add reaction options
            for letter in letters[:len(question['options'])]:
                await quiz_message.add_reaction(f"{letter}\N{COMBINING ENCLOSING KEYCAP}")
            
            # Create game session
            session_data = {
                "question": question,
                "message_id": quiz_message.id,
                "correct_answer": question['correct_answer'],
                "options_letters": letters
            }
            
            session_id = self.game_sessions.create_session(
                interaction.user.id, 
                "quiz", 
                session_data
            )
            
            # Wait for reaction
            def check(reaction, user):
                return (
                    user.id == interaction.user.id and
                    reaction.message.id == quiz_message.id and
                    str(reaction.emoji) in [f"{l}\N{COMBINING ENCLOSING KEYCAP}" for l in letters[:len(question['options'])]]
                )
            
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                
                # Get selected answer
                selected_letter = str(reaction.emoji)[0]
                selected_index = letters.index(selected_letter)
                
                # Check if correct
                is_correct = selected_index == question['correct_answer']
                
                # Calculate rewards
                rewards = self.game_utils.calculate_game_rewards(
                    "quiz", 
                    question['difficulty'],
                    1.0 if is_correct else 0.5
                )
                
                # Give rewards
                if is_correct:
                    await self.economy_utils.add_coins(
                        interaction.user.id, 
                        interaction.guild.id, 
                        rewards["coins"],
                        "quiz_correct"
                    )
                    
                    result_embed = discord.Embed(
                        title="✅ Correct Answer!",
                        color=discord.Color.green(),
                        description=f"**{question['question']}**"
                    )
                    
                    result_embed.add_field(
                        name="🎉 Your Answer",
                        value=f"**{letters[selected_index]}.** {question['options'][selected_index]}",
                        inline=False
                    )
                    
                else:
                    result_embed = discord.Embed(
                        title="❌ Incorrect Answer",
                        color=discord.Color.red(),
                        description=f"**{question['question']}**"
                    )
                    
                    result_embed.add_field(
                        name="❌ Your Answer",
                        value=f"**{letters[selected_index]}.** {question['options'][selected_index]}",
                        inline=True
                    )
                    
                    result_embed.add_field(
                        name="✅ Correct Answer", 
                        value=f"**{letters[question['correct_answer']]}.** {question['options'][question['correct_answer']]}",
                        inline=True
                    )
                
                # Add explanation
                result_embed.add_field(
                    name="📖 Explanation",
                    value=question['explanation'],
                    inline=False
                )
                
                # Add rewards if correct
                if is_correct:
                    result_embed.add_field(
                        name="🎁 Rewards",
                        value=f"**+{rewards['coins']}** Ilm Coins",
                        inline=True
                    )
                
                await interaction.followup.send(embed=result_embed)
                
                # Update user activities
                user_data = await self.economy_utils.get_user_data(interaction.user.id, interaction.guild.id)
                user_data["activities"]["quizzes_completed"] += 1
                user_data["activities"]["games_played"] += 1
                if is_correct:
                    user_data["activities"]["total_learning_time"] += 300  # 5 minutes for quiz
                await self.economy_utils.save_user_data(interaction.user.id, interaction.guild.id, user_data)
                
            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title="⏰ Time's Up!",
                    color=discord.Color.orange(),
                    description="You didn't answer in time. The correct answer was:"
                )
                
                timeout_embed.add_field(
                    name="✅ Correct Answer",
                    value=f"**{letters[question['correct_answer']]}.** {question['options'][question['correct_answer']]}",
                    inline=False
                )
                
                timeout_embed.add_field(
                    name="📖 Explanation",
                    value=question['explanation'],
                    inline=False
                )
                
                await interaction.followup.send(embed=timeout_embed)
            
            # Clean up session
            self.game_sessions.end_session(session_id)
            
        except Exception as e:
            logger.error(f"Error in quiz command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while starting the quiz. Please try again.",
                ephemeral=False
            )
    
    @app_commands.command(name="verse_match", description="Match Quran verses to their correct surah names")
    @app_commands.describe(difficulty="Game difficulty level")
    @app_commands.choices(
        difficulty=[
            app_commands.Choice(name="Easy", value="easy"),
            app_commands.Choice(name="Medium", value="medium"),
            app_commands.Choice(name="Hard", value="hard")
        ]
    )
    async def verse_match(self, interaction: discord.Interaction, difficulty: app_commands.Choice[str] = None):
        """Start a Quran verse matching game."""
        await interaction.response.defer()
        
        try:
            difficulty_value = difficulty.value if difficulty else "medium"
            
            # Get verse match challenge
            verse_data = self.game_utils.get_verse_match(difficulty_value)
            
            if not verse_data:
                await interaction.followup.send(
                    "❌ No verse matching challenges available. Please try again later.",
                    ephemeral=True
                )
                return
            
            # Create embed
            embed = discord.Embed(
                title="📖 Quran Verse Match",
                color=discord.Color.green(),
                description=f"**Verse:**\n*\"{verse_data['verse_text']}\"*"
            )
            
            embed.add_field(
                name="🎯 Difficulty",
                value=verse_data['difficulty'].title(),
                inline=True
            )
            
            embed.add_field(
                name="🏆 Points", 
                value=f"{verse_data['points']}",
                inline=True
            )
            
            if verse_data.get('hint'):
                embed.add_field(
                    name="💡 Hint",
                    value=verse_data['hint'],
                    inline=False
                )
            
            # Create options with numbers
            options_text = ""
            numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
            for i, option in enumerate(verse_data['options']):
                options_text += f"{numbers[i]} {option}\n"
            
            embed.add_field(
                name="📚 Possible Surahs",
                value=options_text,
                inline=False
            )
            
            embed.set_footer(text="React with the number of the correct surah! You have 45 seconds.")
            
            # Send message
            game_message = await interaction.followup.send(embed=embed)
            
            # Add reactions
            for number in numbers[:len(verse_data['options'])]:
                await game_message.add_reaction(number)
            
            # Create session
            session_data = {
                "verse_data": verse_data,
                "message_id": game_message.id,
                "correct_index": verse_data['correct_index'],
                "options_numbers": numbers
            }
            
            session_id = self.game_sessions.create_session(
                interaction.user.id,
                "verse_match",
                session_data
            )
            
            # Wait for reaction
            def check(reaction, user):
                return (
                    user.id == interaction.user.id and
                    reaction.message.id == game_message.id and
                    str(reaction.emoji) in numbers[:len(verse_data['options'])]
                )
            
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=45.0, check=check)
                
                # Get selected answer
                selected_number = str(reaction.emoji)
                selected_index = numbers.index(selected_number)
                
                # Check if correct
                is_correct = selected_index == verse_data['correct_index']
                
                # Calculate rewards
                rewards = self.game_utils.calculate_game_rewards(
                    "verse_match",
                    verse_data['difficulty'],
                    1.0 if is_correct else 0.3
                )
                
                # Create result embed
                if is_correct:
                    await self.economy_utils.add_coins(
                        interaction.user.id,
                        interaction.guild.id,
                        rewards["coins"],
                        "verse_match_correct"
                    )
                    
                    result_embed = discord.Embed(
                        title="✅ Correct Match!",
                        color=discord.Color.green(),
                        description=f"*\"{verse_data['verse_text']}\"*"
                    )
                    
                    result_embed.add_field(
                        name="📖 Surah",
                        value=f"**{verse_data['surah_name']}** (Surah {verse_data['surah_number']}, Verse {verse_data['verse_number']})",
                        inline=False
                    )
                    
                else:
                    result_embed = discord.Embed(
                        title="❌ Incorrect Match",
                        color=discord.Color.red(),
                        description=f"*\"{verse_data['verse_text']}\"*"
                    )
                    
                    result_embed.add_field(
                        name="❌ Your Choice",
                        value=f"**{verse_data['options'][selected_index]}**",
                        inline=True
                    )
                    
                    result_embed.add_field(
                        name="✅ Correct Answer",
                        value=f"**{verse_data['surah_name']}**",
                        inline=True
                    )
                
                # Add rewards if correct
                if is_correct:
                    result_embed.add_field(
                        name="🎁 Rewards",
                        value=f"**+{rewards['coins']}** Ilm Coins",
                        inline=True
                    )
                
                await interaction.followup.send(embed=result_embed)
                
                # Update user activities
                user_data = await self.economy_utils.get_user_data(interaction.user.id, interaction.guild.id)
                user_data["activities"]["games_played"] += 1
                if is_correct:
                    user_data["activities"]["total_learning_time"] += 600  # 10 minutes for verse study
                await self.economy_utils.save_user_data(interaction.user.id, interaction.guild.id, user_data)
                
            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title="⏰ Time's Up!",
                    color=discord.Color.orange(),
                    description=f"*\"{verse_data['verse_text']}\"*"
                )
                
                timeout_embed.add_field(
                    name="✅ Correct Answer",
                    value=f"**{verse_data['surah_name']}** (Surah {verse_data['surah_number']}, Verse {verse_data['verse_number']})",
                    inline=False
                )
                
                await interaction.followup.send(embed=timeout_embed)
            
            # Clean up session
            self.game_sessions.end_session(session_id)
            
        except Exception as e:
            logger.error(f"Error in verse_match command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while starting the verse matching game. Please try again.",
                ephemeral=False
            )
    
    @app_commands.command(name="hadith_game", description="Learn about Hadith through interactive trivia")
    @app_commands.describe(mode="Game mode type")
    @app_commands.choices(
        mode=[
            app_commands.Choice(name="Completion", value="completion"),
            app_commands.Choice(name="Knowledge", value="knowledge"),
            app_commands.Choice(name="Narrator", value="narrator"),
            app_commands.Choice(name="Random", value="random")
        ]
    )
    async def hadith_game(self, interaction: discord.Interaction, mode: app_commands.Choice[str] = None):
        """Start a Hadith trivia game."""
        await interaction.response.defer()
        
        try:
            mode_value = mode.value if mode else None
            
            # Get hadith trivia
            trivia = self.game_utils.get_hadith_trivia(mode_value)
            
            if not trivia:
                await interaction.followup.send(
                    "❌ No Hadith trivia available. Please try again later.",
                    ephemeral=True
                )
                return
            
            # Create embed
            embed = discord.Embed(
                title="📜 Hadith Trivia",
                color=discord.Color.purple(),
                description=f"**{trivia['question']}**"
            )
            
            embed.add_field(
                name="🎮 Mode",
                value=trivia['type'].title(),
                inline=True
            )
            
            embed.add_field(
                name="🏆 Points",
                value=f"{trivia['points']}",
                inline=True
            )
            
            # Create options with letters
            options_text = ""
            letters = ["A", "B", "C", "D"]
            for i, option in enumerate(trivia['options']):
                options_text += f"**{letters[i]}.** {option}\n"
            
            embed.add_field(
                name="📝 Options",
                value=options_text,
                inline=False
            )
            
            embed.set_footer(text="You have 25 seconds to answer! React with the corresponding letter.")
            
            # Send message
            game_message = await interaction.followup.send(embed=embed)
            
            # Add reactions
            for letter in letters[:len(trivia['options'])]:
                await game_message.add_reaction(f"{letter}\N{COMBINING ENCLOSING KEYCAP}")
            
            # Create session
            session_data = {
                "trivia": trivia,
                "message_id": game_message.id,
                "correct_answer": trivia['correct_answer'],
                "options_letters": letters
            }
            
            session_id = self.game_sessions.create_session(
                interaction.user.id,
                "hadith_trivia",
                session_data
            )
            
            # Wait for reaction
            def check(reaction, user):
                return (
                    user.id == interaction.user.id and
                    reaction.message.id == game_message.id and
                    str(reaction.emoji) in [f"{l}\N{COMBINING ENCLOSING KEYCAP}" for l in letters[:len(trivia['options'])]]
                )
            
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=25.0, check=check)
                
                # Get selected answer
                selected_letter = str(reaction.emoji)[0]
                selected_index = letters.index(selected_letter)
                
                # Check if correct
                is_correct = selected_index == trivia['correct_answer']
                
                # Calculate rewards
                rewards = self.game_utils.calculate_game_rewards(
                    "hadith_trivia",
                    "medium",  # Hadith games are typically medium difficulty
                    1.0 if is_correct else 0.5
                )
                
                # Create result embed
                if is_correct:
                    await self.economy_utils.add_coins(
                        interaction.user.id,
                        interaction.guild.id,
                        rewards["coins"],
                        "hadith_game_correct"
                    )
                    
                    result_embed = discord.Embed(
                        title="✅ Correct Answer!",
                        color=discord.Color.green(),
                        description=f"**{trivia['question']}**"
                    )
                    
                    result_embed.add_field(
                        name="🎉 Your Answer",
                        value=f"**{letters[selected_index]}.** {trivia['options'][selected_index]}",
                        inline=False
                    )
                    
                else:
                    result_embed = discord.Embed(
                        title="❌ Incorrect Answer",
                        color=discord.Color.red(),
                        description=f"**{trivia['question']}**"
                    )
                    
                    result_embed.add_field(
                        name="❌ Your Answer",
                        value=f"**{letters[selected_index]}.** {trivia['options'][selected_index]}",
                        inline=True
                    )
                    
                    result_embed.add_field(
                        name="✅ Correct Answer",
                        value=f"**{letters[trivia['correct_answer']]}.** {trivia['options'][trivia['correct_answer']]}",
                        inline=True
                    )
                
                # Add explanation
                result_embed.add_field(
                    name="📖 Explanation",
                    value=trivia['explanation'],
                    inline=False
                )
                
                # Add rewards if correct
                if is_correct:
                    result_embed.add_field(
                        name="🎁 Rewards",
                        value=f"**+{rewards['coins']}** Ilm Coins",
                        inline=True
                    )
                
                await interaction.followup.send(embed=result_embed, ephemeral=True)
                
                # Update user activities
                user_data = await self.economy_utils.get_user_data(interaction.user.id, interaction.guild.id)
                user_data["activities"]["games_played"] += 1
                if is_correct:
                    user_data["activities"]["total_learning_time"] += 450  # 7.5 minutes for hadith study
                await self.economy_utils.save_user_data(interaction.user.id, interaction.guild.id, user_data)
                
            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title="⏰ Time's Up!",
                    color=discord.Color.orange(),
                    description="You didn't answer in time. The correct answer was:"
                )
                
                timeout_embed.add_field(
                    name="✅ Correct Answer",
                    value=f"**{letters[trivia['correct_answer']]}.** {trivia['options'][trivia['correct_answer']]}",
                    inline=False
                )
                
                timeout_embed.add_field(
                    name="📖 Explanation",
                    value=trivia['explanation'],
                    inline=False
                )
                
                await interaction.followup.send(embed=timeout_embed, ephemeral=True)
            
            # Clean up session
            self.game_sessions.end_session(session_id)
            
        except Exception as e:
            logger.error(f"Error in hadith_game command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while starting the Hadith game. Please try again.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Add the games cog to the bot."""
    await bot.add_cog(GamesCog(bot))
    logger.info("Games cog loaded successfully")