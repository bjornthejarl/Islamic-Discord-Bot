"""
Quran Cog for Discord Verify Bot.
Contains slash commands for playing Quran audio with interactive controls.
"""

import logging
import os
import random
from typing import Optional, Dict, List
import asyncio

import discord
from discord import app_commands
from discord.ext import commands

from src.config import Config


class QuranCog(commands.Cog):
    """Cog containing Quran audio playback commands."""
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        
        # Available speakers
        self.speakers = ["abdulbasit", "hudhaify", "mishary", "soudais"]
        
        # Store active playback sessions per guild
        self.active_sessions: Dict[int, Dict] = {}
        
        # Surah names for display (first 114 surahs)
        self.surah_names = {
            1: "Al-Fatihah", 2: "Al-Baqarah", 3: "Ali 'Imran", 4: "An-Nisa", 5: "Al-Ma'idah",
            6: "Al-An'am", 7: "Al-A'raf", 8: "Al-Anfal", 9: "At-Tawbah", 10: "Yunus",
            11: "Hud", 12: "Yusuf", 13: "Ar-Ra'd", 14: "Ibrahim", 15: "Al-Hijr",
            16: "An-Nahl", 17: "Al-Isra", 18: "Al-Kahf", 19: "Maryam", 20: "Taha",
            21: "Al-Anbiya", 22: "Al-Hajj", 23: "Al-Mu'minun", 24: "An-Nur", 25: "Al-Furqan",
            26: "Ash-Shu'ara", 27: "An-Naml", 28: "Al-Qasas", 29: "Al-Ankabut", 30: "Ar-Rum",
            31: "Luqman", 32: "As-Sajdah", 33: "Al-Ahzab", 34: "Saba", 35: "Fatir",
            36: "Ya-Sin", 37: "As-Saffat", 38: "Sad", 39: "Az-Zumar", 40: "Ghafir",
            41: "Fussilat", 42: "Ash-Shura", 43: "Az-Zukhruf", 44: "Ad-Dukhan", 45: "Al-Jathiyah",
            46: "Al-Ahqaf", 47: "Muhammad", 48: "Al-Fath", 49: "Al-Hujurat", 50: "Qaf",
            51: "Adh-Dhariyat", 52: "At-Tur", 53: "An-Najm", 54: "Al-Qamar", 55: "Ar-Rahman",
            56: "Al-Waqi'ah", 57: "Al-Hadid", 58: "Al-Mujadilah", 59: "Al-Hashr", 60: "Al-Mumtahanah",
            61: "As-Saff", 62: "Al-Jumu'ah", 63: "Al-Munafiqun", 64: "At-Taghabun", 65: "At-Talaq",
            66: "At-Tahrim", 67: "Al-Mulk", 68: "Al-Qalam", 69: "Al-Haqqah", 70: "Al-Ma'arij",
            71: "Nuh", 72: "Al-Jinn", 73: "Al-Muzzammil", 74: "Al-Muddaththir", 75: "Al-Qiyamah",
            76: "Al-Insan", 77: "Al-Mursalat", 78: "An-Naba", 79: "An-Nazi'at", 80: "Abasa",
            81: "At-Takwir", 82: "Al-Infitar", 83: "Al-Mutaffifin", 84: "Al-Inshiqaq", 85: "Al-Buruj",
            86: "At-Tariq", 87: "Al-A'la", 88: "Al-Ghashiyah", 89: "Al-Fajr", 90: "Al-Balad",
            91: "Ash-Shams", 92: "Al-Layl", 93: "Ad-Duha", 94: "Ash-Sharh", 95: "At-Tin",
            96: "Al-'Alaq", 97: "Al-Qadr", 98: "Al-Bayyinah", 99: "Az-Zalzalah", 100: "Al-'Adiyat",
            101: "Al-Qari'ah", 102: "At-Takathur", 103: "Al-'Asr", 104: "Al-Humazah", 105: "Al-Fil",
            106: "Quraysh", 107: "Al-Ma'un", 108: "Al-Kawthar", 109: "Al-Kafirun", 110: "An-Nasr",
            111: "Al-Masad", 112: "Al-Ikhlas", 113: "Al-Falaq", 114: "An-Nas"
        }

    async def get_available_surahs(self, speaker: str) -> List[int]:
        """Get list of available surahs for a speaker."""
        try:
            speaker_path = os.path.join("src", "audio", speaker)
            if not os.path.exists(speaker_path):
                return []
                
            files = os.listdir(speaker_path)
            surahs = []
            
            for file in files:
                if file.endswith('.mp3'):
                    # Extract number from filename (handles both "001.mp3" and "1.mp3")
                    number_str = file.split('.')[0]
                    # Remove non-numeric characters
                    number_str = ''.join(filter(str.isdigit, number_str))
                    try:
                        surah_num = int(number_str)
                        surahs.append(surah_num)
                    except ValueError:
                        continue
                        
            return sorted(surahs)
        except Exception as e:
            self.logger.error(f"Error getting available surahs for {speaker}: {e}")
            return []

    async def play_audio(self, interaction: discord.Interaction, speaker: str, surah: int) -> None:
        """Play audio for the specified surah and speaker."""
        try:
            # Get voice client
            voice_client = interaction.guild.voice_client
            
            if not voice_client:
                await interaction.followup.send(
                    "Bot is not connected to a voice channel.", 
                    ephemeral=True
                )
                return

            # Check if audio file exists
            audio_path = os.path.join("src", "audio", speaker, f"{surah:03d}.mp3")
            if not os.path.exists(audio_path):
                # Try without leading zeros
                audio_path = os.path.join("src", "audio", speaker, f"{surah}.mp3")
                if not os.path.exists(audio_path):
                    await interaction.followup.send(
                        f"Audio file for Surah {surah} not found for {speaker}.",
                        ephemeral=True
                    )
                    return

            # Stop current playback if any
            if voice_client.is_playing():
                voice_client.stop()

            # Play the audio with proper FFmpeg options
            try:
                voice_client.play(
                    discord.FFmpegPCMAudio(
                        audio_path,
                        before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                        options="-vn"
                    ),
                    after=lambda e: self.logger.error(f"Player error: {e}") if e else None
                )
            except Exception as e:
                self.logger.error(f"Error starting audio playback: {e}")
                await interaction.followup.send(
                    "Failed to start audio playback. Please try again.",
                    ephemeral=True
                )
                return

            # Update session info with voice channel
            if interaction.guild.id in self.active_sessions:
                self.active_sessions[interaction.guild.id].update({
                    'voice_channel': voice_client.channel.id
                })
            else:
                # Create session if it doesn't exist
                self.active_sessions[interaction.guild.id] = {
                    'speaker': speaker,
                    'surah': surah,
                    'message': None,
                    'voice_channel': voice_client.channel.id
                }

            self.logger.info(f"Playing Surah {surah} by {speaker} in guild {interaction.guild.id}")

        except Exception as e:
            self.logger.error(f"Error playing audio: {e}")
            await interaction.followup.send(
                "An error occurred while trying to play the audio.",
                ephemeral=True
            )

    def create_control_panel(self, speaker: str, surah: int) -> discord.Embed:
        """Create the control panel embed with buttons."""
        embed = discord.Embed(
            title="🎵 Quran Player",
            description=f"**Now Playing:** Surah {surah} ({self.surah_names.get(surah, 'Unknown')})\n"
                       f"**Reciter:** {speaker.title()}",
            color=0x2b2d31
        )
        
        embed.add_field(
            name="Controls",
            value="Use the buttons below to control playback",
            inline=False
        )
        
        embed.set_footer(text="Quran Audio Player • Use /quran play to start playback")
        
        return embed

    @app_commands.command(name="quran", description="Play Quran audio with the specified reciter")
    @app_commands.describe(
        speaker="The reciter to use",
        surah="The surah number to play (1-114, optional)"
    )
    @app_commands.choices(speaker=[
        app_commands.Choice(name="Abdul Basit", value="abdulbasit"),
        app_commands.Choice(name="Hudhaify", value="hudhaify"), 
        app_commands.Choice(name="Mishary", value="mishary"),
        app_commands.Choice(name="Soudais", value="soudais")
    ])
    async def play_quran(
        self,
        interaction: discord.Interaction,
        speaker: str,
        surah: Optional[int] = None
    ) -> None:
        """Play Quran audio with interactive controls.
        
        Args:
            interaction: The interaction that triggered the command
            speaker: The reciter to use
            surah: The surah number to play (optional)
        """
        try:
            # Check if user is in a voice channel
            if not interaction.user.voice or not interaction.user.voice.channel:
                await interaction.response.send_message(
                    "You need to be in a voice channel to use this command.",
                    ephemeral=True
                )
                return

            # If surah is not provided, get a random available surah
            if surah is None:
                available_surahs = await self.get_available_surahs(speaker)
                if not available_surahs:
                    await interaction.response.send_message(
                        f"No surahs available for {speaker.title()}.",
                        ephemeral=True
                    )
                    return
                surah = random.choice(available_surahs)
                self.logger.info(f"Selected random surah {surah} for {speaker}")

            # Validate surah number
            if surah < 1 or surah > 114:
                await interaction.response.send_message(
                    "Surah number must be between 1 and 114.",
                    ephemeral=True
                )
                return

            # Check if audio exists for this speaker and surah
            available_surahs = await self.get_available_surahs(speaker)
            if surah not in available_surahs:
                await interaction.response.send_message(
                    f"Surah {surah} is not available for {speaker.title()}. "
                    f"Available surahs: {', '.join(map(str, available_surahs[:10]))}{'...' if len(available_surahs) > 10 else ''}",
                    ephemeral=True
                )
                return

            # Defer response since this might take a moment
            await interaction.response.defer()

            # Get voice channel
            voice_channel = interaction.user.voice.channel
            
            # Connect to voice channel if not already connected
            voice_client = interaction.guild.voice_client
            if not voice_client or not voice_client.is_connected():
                try:
                    voice_client = await voice_channel.connect(timeout=30.0, reconnect=True)
                except Exception as e:
                    self.logger.error(f"Failed to connect to voice channel: {e}")
                    await interaction.followup.send(
                        "Failed to connect to the voice channel. Please try again.",
                        ephemeral=True
                    )
                    return
            elif voice_client.channel != voice_channel:
                try:
                    await voice_client.move_to(voice_channel)
                except Exception as e:
                    self.logger.error(f"Failed to move to voice channel: {e}")
                    await interaction.followup.send(
                        "Failed to move to the voice channel. Please try again.",
                        ephemeral=True
                    )
                    return

            # Create control panel
            embed = self.create_control_panel(speaker, surah)
            
            # Create buttons
            view = discord.ui.View(timeout=None)
            
            # Previous button
            previous_button = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                emoji="⏮️",
                custom_id=f"quran_prev_{interaction.guild.id}"
            )
            previous_button.callback = self.previous_callback
            view.add_item(previous_button)
            
            # Stop button
            stop_button = discord.ui.Button(
                style=discord.ButtonStyle.danger,
                emoji="⏹️",
                custom_id=f"quran_stop_{interaction.guild.id}"
            )
            stop_button.callback = self.stop_callback
            view.add_item(stop_button)
            
            # Next button
            next_button = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                emoji="⏭️",
                custom_id=f"quran_next_{interaction.guild.id}"
            )
            next_button.callback = self.next_callback
            view.add_item(next_button)
            
            # Speaker selection dropdown
            speaker_select = discord.ui.Select(
                placeholder="Change Reciter...",
                custom_id=f"quran_speaker_{interaction.guild.id}",
                options=[
                    discord.SelectOption(label="Abdul Basit", value="abdulbasit", emoji="🎵"),
                    discord.SelectOption(label="Hudhaify", value="hudhaify", emoji="🎵"),
                    discord.SelectOption(label="Mishary", value="mishary", emoji="🎵"),
                    discord.SelectOption(label="Soudais", value="soudais", emoji="🎵"),
                ]
            )
            speaker_select.callback = self.speaker_callback
            view.add_item(speaker_select)

            # Send the control panel
            message = await interaction.followup.send(embed=embed, view=view)
            
            # Store message in session
            if interaction.guild.id not in self.active_sessions:
                self.active_sessions[interaction.guild.id] = {}
            
            self.active_sessions[interaction.guild.id].update({
                'speaker': speaker,
                'surah': surah,
                'message': message,
                'voice_channel': voice_channel.id
            })

            # Start playing the audio
            await self.play_audio(interaction, speaker, surah)

        except Exception as e:
            self.logger.error(f"Error in play command: {e}")
            await interaction.followup.send(
                "An error occurred while trying to play the audio.",
                ephemeral=True
            )

    async def previous_callback(self, interaction: discord.Interaction):
        """Callback for previous button."""
        try:
            session = self.active_sessions.get(interaction.guild.id)
            if not session:
                await interaction.response.send_message(
                    "No active playback session.", 
                    ephemeral=True
                )
                return

            current_surah = session['surah']
            available_surahs = await self.get_available_surahs(session['speaker'])
            
            # Find the previous available surah
            current_index = available_surahs.index(current_surah) if current_surah in available_surahs else -1
            if current_index > 0:
                new_surah = available_surahs[current_index - 1]
                session['surah'] = new_surah
                
                # Update control panel
                embed = self.create_control_panel(session['speaker'], new_surah)
                await session['message'].edit(embed=embed)
                
                # Play the audio
                await self.play_audio(interaction, session['speaker'], new_surah)
                
                await interaction.response.defer()
            else:
                await interaction.response.send_message(
                    "This is the first available surah.", 
                    ephemeral=True
                )

        except Exception as e:
            self.logger.error(f"Error in previous callback: {e}")
            await interaction.response.send_message(
                "An error occurred.", 
                ephemeral=True
            )

    async def next_callback(self, interaction: discord.Interaction):
        """Callback for next button."""
        try:
            session = self.active_sessions.get(interaction.guild.id)
            if not session:
                await interaction.response.send_message(
                    "No active playback session.", 
                    ephemeral=True
                )
                return

            current_surah = session['surah']
            available_surahs = await self.get_available_surahs(session['speaker'])
            
            # Find the next available surah
            current_index = available_surahs.index(current_surah) if current_surah in available_surahs else -1
            if current_index < len(available_surahs) - 1:
                new_surah = available_surahs[current_index + 1]
                session['surah'] = new_surah
                
                # Update control panel
                embed = self.create_control_panel(session['speaker'], new_surah)
                await session['message'].edit(embed=embed)
                
                # Play the audio
                await self.play_audio(interaction, session['speaker'], new_surah)
                
                await interaction.response.defer()
            else:
                await interaction.response.send_message(
                    "This is the last available surah.", 
                    ephemeral=True
                )

        except Exception as e:
            self.logger.error(f"Error in next callback: {e}")
            await interaction.response.send_message(
                "An error occurred.", 
                ephemeral=True
            )

    async def stop_callback(self, interaction: discord.Interaction):
        """Callback for stop button."""
        try:
            session = self.active_sessions.get(interaction.guild.id)
            if not session:
                await interaction.response.send_message(
                    "No active playback session.", 
                    ephemeral=True
                )
                return

            # Stop playback and disconnect
            voice_client = interaction.guild.voice_client
            if voice_client:
                if voice_client.is_playing():
                    voice_client.stop()
                await voice_client.disconnect()

            # Remove session
            if interaction.guild.id in self.active_sessions:
                del self.active_sessions[interaction.guild.id]

            # Update message if it exists
            if session.get('message'):
                try:
                    embed = discord.Embed(
                        title="🎵 Quran Player",
                        description="Playback stopped.",
                        color=0x2b2d31
                    )
                    await session['message'].edit(embed=embed, view=None)
                except Exception as e:
                    self.logger.warning(f"Could not update message in stop callback: {e}")
            
            await interaction.response.defer()

        except Exception as e:
            self.logger.error(f"Error in stop callback: {e}")
            await interaction.response.send_message(
                "An error occurred while stopping playback.", 
                ephemeral=True
            )

    async def speaker_callback(self, interaction: discord.Interaction):
        """Callback for speaker selection."""
        try:
            session = self.active_sessions.get(interaction.guild.id)
            if not session:
                await interaction.response.send_message(
                    "No active playback session.", 
                    ephemeral=True
                )
                return

            new_speaker = interaction.data['values'][0]
            current_surah = session['surah']
            
            # Check if surah is available for new speaker
            available_surahs = await self.get_available_surahs(new_speaker)
            if current_surah not in available_surahs:
                # Find the closest available surah
                if available_surahs:
                    new_surah = min(available_surahs, key=lambda x: abs(x - current_surah))
                    session['surah'] = new_surah
                else:
                    await interaction.response.send_message(
                        f"No surahs available for {new_speaker.title()}.",
                        ephemeral=True
                    )
                    return

            # Update session
            session['speaker'] = new_speaker
            
            # Update control panel
            embed = self.create_control_panel(new_speaker, session['surah'])
            await session['message'].edit(embed=embed)
            
            # Play the audio with new speaker
            await self.play_audio(interaction, new_speaker, session['surah'])
            
            await interaction.response.defer()

        except Exception as e:
            self.logger.error(f"Error in speaker callback: {e}")
            await interaction.response.send_message(
                "An error occurred while changing speaker.", 
                ephemeral=True
            )


async def setup(bot: commands.Bot) -> None:
    """Set up the Quran cog.
    
    Args:
        bot: The bot instance
    """
    await bot.add_cog(QuranCog(bot))