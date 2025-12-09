import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
import aiohttp
import urllib.parse
from datetime import datetime
from typing import Optional
import random

from src.utils.economy_utils import EconomyUtils  # To access DB mainly, or we can pass DB instance

logger = logging.getLogger(__name__)

class SpiritualCog(commands.Cog):
    """Spiritual utilities and features."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        # We need access to the database. Accessing via bot instance or creating a new utils instance.
        # Ideally, bot should hold the db info. Since EconomyUtils has logic, we can use it or just the db.
        # But we don't have dependency injection clean here. I'll instantiate EconomyUtils to get DB access.
        self.economy_utils = EconomyUtils()
        self.daily_content_task.start()

    async def cog_unload(self):
        await self.session.close()
        self.daily_content_task.cancel()

    @tasks.loop(hours=24)
    async def daily_content_task(self):
        """Post daily Islamic content to configured channels."""
        try:
            # Fetch content
            content = await self.get_daily_content()
            if not content:
                logger.warning("Failed to fetch daily content")
                return

            # Fetch all guilds with configured channels
            # We access the DB through economy_utils.db
            rows = await self.economy_utils.db.fetchall("SELECT guild_id, daily_content_channel_id FROM guild_settings WHERE daily_content_channel_id IS NOT NULL")
            
            for row in rows:
                channel_id = row['daily_content_channel_id']
                try:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        await channel.send(embed=content)
                except Exception as e:
                    logger.error(f"Failed to send daily content to channel {channel_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in daily content task: {e}")

    @daily_content_task.before_loop
    async def before_daily_content(self):
        await self.bot.wait_until_ready()

    async def get_daily_content(self) -> Optional[discord.Embed]:
        """Fetch a random verse or hadith."""
        # Mix of verses and hadiths
        try:
            # 50/50 chance
            if random.random() > 0.5:
                # Get Verse
                # Using a random verse endpoint or our internal logic. 
                # Let's use a public API wrapper logic or simple fetch
                # For simplicity/reliability without external deps, I'll use a curated list or API if I can.
                # http://api.alquran.cloud/v1/ayah/{random}/en.asad
                
                random_ayah = random.randint(1, 6236)
                url = f"http://api.alquran.cloud/v1/ayah/{random_ayah}/en.asad"
                async with self.session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        verse = data['data']
                        embed = discord.Embed(
                            title="📖 Verse of the Day",
                            description=f"*{verse['text']}*",
                            color=discord.Color.green()
                        )
                        embed.set_footer(text=f"Surah {verse['surah']['englishName']} ({verse['surah']['number']}:{verse['numberInSurah']})")
                        return embed
            else:
                # Get Hadith (Mocking slightly as reliable free hadith APIs are rare/rate-limited without keys)
                # Using a small internal list for reliability if API fails
                hadiths = [
                    "The best among you is the one who learns the Quran and teaches it. (Bukhari)",
                    "Actions are judged by intentions. (Bukhari)",
                    "A good word is charity. (Bukhari)",
                    "None of you truly believes until he loves for his brother what he loves for himself. (Bukhari/Muslim)",
                    "Cleanliness is half of faith. (Muslim)"
                ]
                text = random.choice(hadiths)
                embed = discord.Embed(
                    title="📜 Hadith of the Day",
                    description=f"*{text}*",
                    color=discord.Color.gold()
                )
                return embed
                
        except Exception as e:
            logger.error(f"Error fetching daily content: {e}")
            return None

    @app_commands.command(name="set_daily_channel", description="Set the channel for daily Islamic content")
    @app_commands.describe(channel="Channel to post content in")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_daily_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Configure the daily content channel."""
        await interaction.response.defer()
        
        try:
            # Check if guild exists in settings, insert or update
            await self.economy_utils.db.execute(
                """
                INSERT INTO guild_settings (guild_id, daily_content_channel_id) 
                VALUES (?, ?)
                ON CONFLICT (guild_id) DO UPDATE SET 
                daily_content_channel_id = EXCLUDED.daily_content_channel_id,
                updated_at = CURRENT_TIMESTAMP
                """,
                (interaction.guild.id, channel.id)
            )
            await self.economy_utils.db.commit()
            
            await interaction.followup.send(f"✅ Daily content will now be posted in {channel.mention}.")
            
            # Send a test message immediately
            content = await self.get_daily_content()
            if content:
                await channel.send(content=f"🌟 **Daily Content setup successful!** Here is a sample:", embed=content)
            
        except Exception as e:
            logger.error(f"Error in set_daily_channel: {e}")
            await interaction.followup.send("❌ An error occurred.", ephemeral=True)

    @app_commands.command(name="trigger_daily", description="Manually trigger the daily content (Admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def trigger_daily(self, interaction: discord.Interaction):
        """Force trigger the daily content delivery."""
        await interaction.response.defer()
        await self.daily_content_task()
        await interaction.followup.send("✅ Daily content triggered.")
        
    @app_commands.command(name="prayertimes", description="Get prayer times for a specific city")
    @app_commands.describe(city="City to get prayer times for", country="Country (optional)")
    async def prayertimes(self, interaction: discord.Interaction, city: str, country: Optional[str] = None):
        """Get prayer times for a location."""
        await interaction.response.defer()
        
        try:
            # Construct API URL
            base_url = "http://api.aladhan.com/v1/timingsByCity"
            params = {
                "city": city,
                "country": country if country else "",
                "method": 2  # ISNA method, arguably standard-ish or customizable later
            }
            
            async with self.session.get(base_url, params=params) as response:
                if response.status != 200:
                    await interaction.followup.send("❌ Failed to fetch prayer times. Please check the city name.", ephemeral=True)
                    return
                
                data = await response.json()
                data = data.get("data", {})
                timings = data.get("timings", {})
                date_readable = data.get("date", {}).get("readable", "")
                
                if not timings:
                    await interaction.followup.send("❌ Could not find timings for this location.", ephemeral=True)
                    return

                embed = discord.Embed(
                    title=f"🕌 Prayer Times for {city.title()}",
                    description=f"**Date:** {date_readable}",
                    color=discord.Color.green()
                )
                
                # Order of prayers
                prayers = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
                
                for prayer in prayers:
                    time = timings.get(prayer)
                    embed.add_field(name=prayer, value=time, inline=False)
                    
                embed.set_footer(text="Powered by Aladhan API")
                await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in prayertimes: {e}")
            await interaction.followup.send("❌ An error occurred.", ephemeral=True)

    @app_commands.command(name="qibla", description="Get Qibla direction for a city")
    @app_commands.describe(city="City name")
    async def qibla(self, interaction: discord.Interaction, city: str):
        """Get Qibla direction."""
        await interaction.response.defer()
        
        try:
            # We first need coordinates for the city to use detailed methods, 
            # but usually Aladhan has a qibla endpoint or we can search lat/long.
            # Aladhan Qibla API requires lat/long. 
            # So first, geocode the city.
            # Using OpenStreetMap Nominatim (needs User-Agent)
            
            geocode_url = "https://nominatim.openstreetmap.org/search"
            headers = {'User-Agent': 'IlmGardenBot/1.0'}
            params = {'q': city, 'format': 'json', 'limit': 1}
            
            async with self.session.get(geocode_url, params=params, headers=headers) as resp:
                if resp.status != 200:
                    await interaction.followup.send("❌ Could not find location.", ephemeral=True)
                    return
                geo_data = await resp.json()
                
            if not geo_data:
                await interaction.followup.send(f"❌ Could not find coordinates for {city}.", ephemeral=True)
                return
                
            lat = geo_data[0]['lat']
            lon = geo_data[0]['lon']
            
            # Now get Qibla
            qibla_url = f"http://api.aladhan.com/v1/qibla/{lat}/{lon}"
            async with self.session.get(qibla_url) as resp:
                if resp.status != 200:
                    await interaction.followup.send("❌ Failed to calculate Qibla.", ephemeral=True)
                    return
                q_data = await resp.json()
                
            direction = q_data.get("data", {}).get("direction")
            
            embed = discord.Embed(
                title=f"🧭 Qibla Direction for {city.title()}",
                description=f"The Qibla is at **{direction:.2f}°** relative to North.",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url="https://i.imgur.com/2X8Xg7Y.png") # Placeholder compass image
            
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in qibla: {e}")
            await interaction.followup.send("❌ An error occurred.", ephemeral=True)

    @app_commands.command(name="zakat", description="Calculate Zakat (2.5%) on your assets")
    @app_commands.describe(cash="Cash amount", gold="Value of gold", silver="Value of silver", other="Other savings")
    async def zakat(self, interaction: discord.Interaction, cash: float = 0.0, gold: float = 0.0, silver: float = 0.0, other: float = 0.0):
        """Calculate Zakat."""
        total_assets = cash + gold + silver + other
        zakat_due = total_assets * 0.025
        
        embed = discord.Embed(
            title="💰 Zakat Calculator",
            color=discord.Color.green()
        )
        embed.add_field(name="Total Assets", value=f"{total_assets:,.2f}", inline=False)
        embed.add_field(name="Zakat Due (2.5%)", value=f"**{zakat_due:,.2f}**", inline=False)
        embed.set_footer(text="Nisab threshold should be checked locally.")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(SpiritualCog(bot))
    logger.info("Spiritual cog loaded")
