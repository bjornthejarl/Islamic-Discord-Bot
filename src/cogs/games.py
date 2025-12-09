"""
Games Cog for Discord Bot
Handles educational Islamic games with rewards and progression.
"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import logging
from typing import Optional, Dict, Any, List

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
    
    async def _create_game_embed(self, title: str, description: str, color: discord.Color, 
                               fields: List[Dict[str, Any]], footer: str = None) -> discord.Embed:
        """Helper to create consistent game embeds."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )
        
        for field in fields:
            embed.add_field(
                name=field['name'],
                value=field['value'],
                inline=field.get('inline', True)
            )
            
        if footer:
            embed.set_footer(text=footer)
            
        return embed

    async def _handle_game_reward(self, interaction: discord.Interaction, game_type: str, 
                                is_correct: bool, difficulty: str, correct_answer_text: str,
                                explanation: str, user_answer: str, question_text: str) -> None:
        """Helper to handle game rewards and result messages."""
        
        # Calculate rewards
        rewards = self.game_utils.calculate_game_rewards(
            game_type, 
            difficulty,
            1.0 if is_correct else 0.5
        )
        
        if is_correct:
            await self.economy_utils.add_coins(
                interaction.user.id, 
                interaction.guild.id, 
                rewards["coins"],
                f"{game_type}_correct"
            )
            
            embed = await self._create_game_embed(
                title="✅ Correct Answer!",
                description=f"**{question_text}**",
                color=discord.Color.green(),
                fields=[
                    {"name": "🎉 Your Answer", "value": user_answer, "inline": False},
                    {"name": "📖 Explanation", "value": explanation, "inline": False},
                    {"name": "🎁 Rewards", "value": f"**+{rewards['coins']}** Ilm Coins", "inline": True}
                ]
            )
        else:
            embed = await self._create_game_embed(
                title="❌ Incorrect Answer",
                description=f"**{question_text}**",
                color=discord.Color.red(),
                fields=[
                    {"name": "❌ Your Answer", "value": user_answer, "inline": True},
                    {"name": "✅ Correct Answer", "value": correct_answer_text, "inline": True},
                    {"name": "📖 Explanation", "value": explanation, "inline": False}
                ]
            )
        
        await interaction.followup.send(embed=embed)
        
        # Update user activities
        try:
            await self.economy_utils.increment_stat(interaction.user.id, interaction.guild.id, "games_played", 1)
            
            if game_type == "quiz":
                await self.economy_utils.increment_stat(interaction.user.id, interaction.guild.id, "quizzes_completed", 1)
                
        except Exception as e:
            logger.error(f"Error updating user stats: {e}")

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
            category_value = category.value if category else None
            difficulty_value = difficulty.value if difficulty else "medium"
            
            question = self.game_utils.get_quiz_question(category_value, difficulty_value)
            
            if not question:
                await interaction.followup.send(
                    "❌ No quiz questions available for the selected category/difficulty.",
                    ephemeral=True
                )
                return
            
            letters = ["A", "B", "C", "D"]
            options_text = ""
            for i, option in enumerate(question['options']):
                options_text += f"**{letters[i]}.** {option}\n"
            
            embed = await self._create_game_embed(
                title="🧠 Islamic Knowledge Quiz",
                description=f"**{question['question']}**",
                color=discord.Color.blue(),
                fields=[
                    {"name": "📚 Category", "value": question['category'].title(), "inline": True},
                    {"name": "🎯 Difficulty", "value": question['difficulty'].title(), "inline": True},
                    {"name": "🏆 Points", "value": str(question['points']), "inline": True},
                    {"name": "📝 Options", "value": options_text, "inline": False}
                ],
                footer="You have 30 seconds to answer! React with the corresponding letter."
            )
            
            quiz_message = await interaction.followup.send(embed=embed)
            
            for letter in letters[:len(question['options'])]:
                await quiz_message.add_reaction(f"{letter}\N{COMBINING ENCLOSING KEYCAP}")
            
            def check(reaction, user):
                return (
                    user.id == interaction.user.id and
                    reaction.message.id == quiz_message.id and
                    str(reaction.emoji) in [f"{l}\N{COMBINING ENCLOSING KEYCAP}" for l in letters[:len(question['options'])]]
                )
            
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                
                selected_letter = str(reaction.emoji)[0]
                selected_index = letters.index(selected_letter)
                is_correct = selected_index == question['correct_answer']
                
                user_answer = f"**{letters[selected_index]}.** {question['options'][selected_index]}"
                correct_answer = f"**{letters[question['correct_answer']]}.** {question['options'][question['correct_answer']]}"
                
                await self._handle_game_reward(
                    interaction, "quiz", is_correct, question['difficulty'],
                    correct_answer, question['explanation'], user_answer, question['question']
                )
                    
            except asyncio.TimeoutError:
                correct_answer = f"**{letters[question['correct_answer']]}.** {question['options'][question['correct_answer']]}"
                embed = await self._create_game_embed(
                    title="⏰ Time's Up!",
                    description="You didn't answer in time.",
                    color=discord.Color.orange(),
                    fields=[
                        {"name": "✅ Correct Answer", "value": correct_answer, "inline": False},
                        {"name": "📖 Explanation", "value": question['explanation'], "inline": False}
                    ]
                )
                await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in quiz command: {e}")
            await interaction.followup.send("❌ An error occurred. Please try again.", ephemeral=True)

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
            verse_data = self.game_utils.get_verse_match(difficulty_value)
            
            if not verse_data:
                await interaction.followup.send("❌ No verse matching challenges available.", ephemeral=True)
                return
            
            numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
            options_text = ""
            for i, option in enumerate(verse_data['options']):
                options_text += f"{numbers[i]} {option}\n"
            
            fields = [
                {"name": "🎯 Difficulty", "value": verse_data['difficulty'].title(), "inline": True},
                {"name": "🏆 Points", "value": str(verse_data['points']), "inline": True}
            ]
            
            if verse_data.get('hint'):
                fields.append({"name": "💡 Hint", "value": verse_data['hint'], "inline": False})
                
            fields.append({"name": "📚 Possible Surahs", "value": options_text, "inline": False})
            
            embed = await self._create_game_embed(
                title="📖 Quran Verse Match",
                description=f"**Verse:**\n*\"{verse_data['verse_text']}\"*",
                color=discord.Color.green(),
                fields=fields,
                footer="React with the number of the correct surah! You have 45 seconds."
            )
            
            game_message = await interaction.followup.send(embed=embed)
            
            for number in numbers[:len(verse_data['options'])]:
                await game_message.add_reaction(number)
            
            def check(reaction, user):
                return (
                    user.id == interaction.user.id and
                    reaction.message.id == game_message.id and
                    str(reaction.emoji) in numbers[:len(verse_data['options'])]
                )
            
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=45.0, check=check)
                
                selected_number = str(reaction.emoji)
                selected_index = numbers.index(selected_number)
                is_correct = selected_index == verse_data['correct_index']
                
                user_answer = f"**{verse_data['options'][selected_index]}**"
                correct_answer = f"**{verse_data['surah_name']}** (Surah {verse_data['surah_number']}, Verse {verse_data['verse_number']})"
                
                await self._handle_game_reward(
                    interaction, "verse_match", is_correct, verse_data['difficulty'],
                    correct_answer, "Verse match completed.", user_answer, f"*\"{verse_data['verse_text']}\"*"
                )
                
            except asyncio.TimeoutError:
                correct_answer = f"**{verse_data['surah_name']}** (Surah {verse_data['surah_number']}, Verse {verse_data['verse_number']})"
                embed = await self._create_game_embed(
                    title="⏰ Time's Up!",
                    description=f"*\"{verse_data['verse_text']}\"*",
                    color=discord.Color.orange(),
                    fields=[{"name": "✅ Correct Answer", "value": correct_answer, "inline": False}]
                )
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error in verse_match command: {e}")
            await interaction.followup.send("❌ An error occurred. Please try again.", ephemeral=True)

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
            trivia = self.game_utils.get_hadith_trivia(mode_value)
            
            if not trivia:
                await interaction.followup.send("❌ No Hadith trivia available.", ephemeral=True)
                return
            
            letters = ["A", "B", "C", "D"]
            options_text = ""
            for i, option in enumerate(trivia['options']):
                options_text += f"**{letters[i]}.** {option}\n"
            
            embed = await self._create_game_embed(
                title="📜 Hadith Trivia",
                description=f"**{trivia['question']}**",
                color=discord.Color.purple(),
                fields=[
                    {"name": "🎮 Mode", "value": trivia['type'].title(), "inline": True},
                    {"name": "🏆 Points", "value": str(trivia['points']), "inline": True},
                    {"name": "📝 Options", "value": options_text, "inline": False}
                ],
                footer="You have 25 seconds to answer! React with the corresponding letter."
            )
            
            game_message = await interaction.followup.send(embed=embed)
            
            for letter in letters[:len(trivia['options'])]:
                await game_message.add_reaction(f"{letter}\N{COMBINING ENCLOSING KEYCAP}")
            
            def check(reaction, user):
                return (
                    user.id == interaction.user.id and
                    reaction.message.id == game_message.id and
                    str(reaction.emoji) in [f"{l}\N{COMBINING ENCLOSING KEYCAP}" for l in letters[:len(trivia['options'])]]
                )
            
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=25.0, check=check)
                
                selected_letter = str(reaction.emoji)[0]
                selected_index = letters.index(selected_letter)
                is_correct = selected_index == trivia['correct_answer']
                
                user_answer = f"**{letters[selected_index]}.** {trivia['options'][selected_index]}"
                correct_answer = f"**{letters[trivia['correct_answer']]}.** {trivia['options'][trivia['correct_answer']]}"
                
                await self._handle_game_reward(
                    interaction, "hadith_trivia", is_correct, "medium",
                    correct_answer, trivia['explanation'], user_answer, trivia['question']
                )
                
            except asyncio.TimeoutError:
                correct_answer = f"**{letters[trivia['correct_answer']]}.** {trivia['options'][trivia['correct_answer']]}"
                embed = await self._create_game_embed(
                    title="⏰ Time's Up!",
                    description="You didn't answer in time.",
                    color=discord.Color.orange(),
                    fields=[
                        {"name": "✅ Correct Answer", "value": correct_answer, "inline": False},
                        {"name": "📖 Explanation", "value": trivia['explanation'], "inline": False}
                    ]
                )
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error in hadith_game command: {e}")
            await interaction.followup.send("❌ An error occurred. Please try again.", ephemeral=True)

    @app_commands.command(name="guess_reciter", description="Identify the famous Quran reciter from audio")
    async def guess_reciter(self, interaction: discord.Interaction):
        """Start a Guess the Reciter game."""
        await interaction.response.defer()
        
        try:
            challenge = self.game_utils.get_reciter_challenge()
            
            letters = ["A", "B", "C", "D"]
            options_text = ""
            for i, option in enumerate(challenge['options']):
                options_text += f"**{letters[i]}.** {option}\n"
            
            embed = await self._create_game_embed(
                title="🎧 Guess the Reciter",
                description=f"Listen to the recitation [here]({challenge['audio_url']}) and guess who it is!",
                color=discord.Color.teal(),
                fields=[
                    {"name": "🏆 Points", "value": str(challenge['points']), "inline": True},
                    {"name": "📝 Options", "value": options_text, "inline": False}
                ],
                footer="React with the letter! You have 30 seconds."
            )
            
            game_message = await interaction.followup.send(embed=embed)
            
            for letter in letters[:len(challenge['options'])]:
                await game_message.add_reaction(f"{letter}\N{COMBINING ENCLOSING KEYCAP}")
            
            def check(reaction, user):
                return (
                    user.id == interaction.user.id and
                    reaction.message.id == game_message.id and
                    str(reaction.emoji) in [f"{l}\N{COMBINING ENCLOSING KEYCAP}" for l in letters[:len(challenge['options'])]]
                )
            
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                
                selected_letter = str(reaction.emoji)[0]
                selected_index = letters.index(selected_letter)
                is_correct = selected_index == challenge['correct_index']
                
                user_answer = f"**{challenge['options'][selected_index]}**"
                correct_answer = f"**{challenge['correct_name']}**"
                
                await self._handle_game_reward(
                    interaction, "reciter_guess", is_correct, "medium",
                    correct_answer, "Reciter identified.", user_answer, "Who is the reciter?"
                )
                
            except asyncio.TimeoutError:
                embed = await self._create_game_embed(
                    title="⏰ Time's Up!",
                    description=f"The correct reciter was **{challenge['correct_name']}**.",
                    color=discord.Color.orange(),
                    fields=[]
                )
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error in guess_reciter command: {e}")
            await interaction.followup.send("❌ An error occurred.", ephemeral=True)


async def setup(bot: commands.Bot):
    """Add the games cog to the bot."""
    await bot.add_cog(GamesCog(bot))
    logger.info("Games cog loaded successfully")