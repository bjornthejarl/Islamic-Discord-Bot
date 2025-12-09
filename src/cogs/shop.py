"""
Shop Cog for Discord Bot
Handles Halal-compliant shop system with items, purchases, and inventory.
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging
import json
import os
from typing import Optional

from src.utils.economy_utils import EconomyUtils

logger = logging.getLogger(__name__)


class ShopCog(commands.Cog):
    """Shop system with Halal-compliant items and purchases."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.economy_utils = EconomyUtils()
        self.shop_items = self.load_shop_items()
    
    def load_shop_items(self):
        """Load shop items from JSON file."""
        try:
            shop_path = os.path.join("src", "data", "shop", "items.json")
            if os.path.exists(shop_path):
                with open(shop_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Create default shop items if file doesn't exist
                default_items = {
                    "items": [
                        {
                            "id": "dua_book",
                            "name": "📖 Dua Collection Book",
                            "description": "A comprehensive collection of Islamic prayers and supplications",
                            "price": 150,
                            "type": "consumable",
                            "category": "knowledge",
                            "effects": {"good_deed_points": 5}
                        },
                        {
                            "id": "quran_audio",
                            "name": "🎧 Quran Audio Recitation",
                            "description": "Beautiful recitation of the Holy Quran by renowned Qaris",
                            "price": 200,
                            "type": "consumable", 
                            "category": "knowledge",
                            "effects": {"good_deed_points": 8}
                        },
                        {
                            "id": "islamic_art",
                            "name": "🖼️ Islamic Art Frame",
                            "description": "Beautiful Islamic calligraphy and geometric patterns",
                            "price": 300,
                            "type": "decorative",
                            "category": "cosmetic",
                            "effects": {"prestige": 10}
                        },
                        {
                            "id": "prayer_mat",
                            "name": "🧎 Premium Prayer Mat",
                            "description": "High-quality prayer mat with comfortable padding",
                            "price": 400,
                            "type": "utility",
                            "category": "practical",
                            "effects": {"good_deed_points": 15}
                        },
                        {
                            "id": "charity_certificate",
                            "name": "🏆 Charity Certificate",
                            "description": "Official certificate recognizing your charitable contributions",
                            "price": 500,
                            "type": "achievement",
                            "category": "prestige",
                            "effects": {"prestige": 25, "good_deed_points": 20}
                        },
                        {
                            "id": "knowledge_boost",
                            "name": "🧠 Knowledge Boost",
                            "description": "Temporary 2x bonus to quiz and game rewards (24 hours)",
                            "price": 350,
                            "type": "boost",
                            "category": "utility",
                            "effects": {"xp_multiplier": 2.0, "duration_hours": 24}
                        },
                        {
                            "id": "hijri_calendar",
                            "name": "📅 Hijri Calendar",
                            "description": "Beautiful Islamic calendar with important dates and events",
                            "price": 250,
                            "type": "decorative",
                            "category": "knowledge",
                            "effects": {"good_deed_points": 10}
                        },
                        {
                            "id": "arabic_lessons",
                            "name": "📚 Arabic Language Course",
                            "description": "Basic Arabic language lessons for Quranic understanding",
                            "price": 600,
                            "type": "consumable",
                            "category": "knowledge",
                            "effects": {"good_deed_points": 30, "prestige": 15}
                        }
                    ]
                }
                os.makedirs(os.path.dirname(shop_path), exist_ok=True)
                with open(shop_path, 'w', encoding='utf-8') as f:
                    json.dump(default_items, f, indent=2, ensure_ascii=False)
                return default_items
        except Exception as e:
            logger.error(f"Error loading shop items: {e}")
            return {"items": []}
    
    @app_commands.command(name="shop", description="Browse the Halal shop for items")
    @app_commands.describe(category="Filter items by category")
    @app_commands.choices(category=[
        app_commands.Choice(name="All Items", value="all"),
        app_commands.Choice(name="Knowledge", value="knowledge"),
        app_commands.Choice(name="Cosmetic", value="cosmetic"),
        app_commands.Choice(name="Practical", value="practical"),
        app_commands.Choice(name="Prestige", value="prestige"),
        app_commands.Choice(name="Utility", value="utility")
    ])
    async def shop(self, interaction: discord.Interaction, category: app_commands.Choice[str] = None):
        """Display the shop with available items."""
        await interaction.response.defer()
        
        try:
            category_value = category.value if category else "all"
            items = self.shop_items["items"]
            
            # Filter items by category if specified
            if category_value != "all":
                items = [item for item in items if item["category"] == category_value]
            
            if not items:
                await interaction.followup.send(
                    f"❌ No items available in the {category_value} category.",
                    ephemeral=True
                )
                return
            
            # Create shop embed
            embed = discord.Embed(
                title="🕌 Ilm Garden Shop",
                color=discord.Color.gold(),
                description="Browse Halal-compliant items to enhance your Islamic journey"
            )
            
            # Add items to embed
            for i, item in enumerate(items):
                item_text = f"**Price:** {item['price']} IC\n"
                item_text += f"**Type:** {item['type'].title()}\n"
                item_text += f"**Category:** {item['category'].title()}\n"
                
                # Add effects
                if "effects" in item:
                    effects = []
                    for effect, value in item["effects"].items():
                        if effect == "good_deed_points":
                            effects.append(f"+{value} GDP")
                        elif effect == "prestige":
                            effects.append(f"+{value} Prestige")
                        elif effect == "xp_multiplier":
                            effects.append(f"{value}x XP Boost")
                    
                    if effects:
                        item_text += f"**Effects:** {', '.join(effects)}\n"
                
                embed.add_field(
                    name=f"{item['name']} (ID: `{item['id']}`)",
                    value=f"{item['description']}\n{item_text}",
                    inline=False
                )
            
            embed.set_footer(text=f"Use /buy <item_id> to purchase an item | {len(items)} items found")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in shop command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while accessing the shop. Please try again.",
                ephemeral=True
            )
    
    @app_commands.command(name="buy", description="Purchase an item from the shop")
    @app_commands.describe(item_id="ID of the item to purchase")
    async def buy(self, interaction: discord.Interaction, item_id: str):
        """Purchase an item from the shop."""
        await interaction.response.defer()
        
        try:
            # Find the item
            item = None
            for shop_item in self.shop_items["items"]:
                if shop_item["id"] == item_id:
                    item = shop_item
                    break
            
            if not item:
                await interaction.followup.send(
                    f"❌ Item with ID `{item_id}` not found in the shop.",
                    ephemeral=True
                )
                return
            
            # Check if user has enough coins
            user_data = await self.economy_utils.get_user_data(interaction.user.id, interaction.guild.id)
            current_coins = user_data["economy"]["ilm_coins"]
            
            if current_coins < item["price"]:
                await interaction.followup.send(
                    f"❌ You don't have enough Ilm Coins to purchase {item['name']}.\n"
                    f"**Price:** {item['price']} IC | **Your Balance:** {current_coins} IC",
                    ephemeral=True
                )
                return
            
            # Process purchase
            success = await self.economy_utils.remove_coins(
                interaction.user.id,
                interaction.guild.id,
                item["price"],
                f"purchase_{item_id}"
            )
            
            if not success:
                await interaction.followup.send(
                    "❌ Failed to process purchase. Please try again.",
                    ephemeral=True
                )
                return
            
            # Add item to user's inventory in DB
            await self.economy_utils.db.execute(
                """
                INSERT INTO inventory (user_id, guild_id, item_id, quantity)
                VALUES (?, ?, ?, 1)
                ON CONFLICT (user_id, guild_id, item_id) 
                DO UPDATE SET quantity = inventory.quantity + 1
                """,
                (interaction.user.id, interaction.guild.id, item_id)
            )
            
            await self.economy_utils.db.commit()
            
            # Apply item effects
            effects_applied = []
            if "effects" in item:
                if "good_deed_points" in item["effects"]:
                    gdp_amount = item["effects"]["good_deed_points"]
                    user_data["economy"]["good_deed_points"] += gdp_amount
                    
                    # Update user GDP directly in DB
                    await self.economy_utils.db.execute(
                        "UPDATE users SET good_deed_points = good_deed_points + ? WHERE user_id = ? AND guild_id = ?",
                        (gdp_amount, interaction.user.id, interaction.guild.id)
                    )
                    effects_applied.append(f"+{gdp_amount} Good Deed Points")
                
                # Check for other effects handling if needed
            
            # Create success embed
            embed = discord.Embed(
                title="🛒 Purchase Successful!",
                color=discord.Color.green(),
                description=f"You purchased **{item['name']}**"
            )
            
            embed.add_field(
                name="💰 Price",
                value=f"{item['price']} Ilm Coins",
                inline=True
            )
            
            embed.add_field(
                name="📦 New Balance",
                value=f"{current_coins - item['price']} IC",
                inline=True
            )
            
            if effects_applied:
                embed.add_field(
                    name="✨ Effects Applied",
                    value="\n".join(effects_applied),
                    inline=False
                )
            
            embed.set_footer(text="Use /inventory to view your purchased items")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in buy command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while processing your purchase. Please try again.",
                ephemeral=True
            )
    
    @app_commands.command(name="inventory", description="View your purchased items and inventory")
    async def inventory(self, interaction: discord.Interaction):
        """Display user's inventory."""
        await interaction.response.defer()
        
        try:
            # Fetch inventory from DB
            rows = await self.economy_utils.db.fetchall(
                "SELECT item_id, quantity FROM inventory WHERE user_id = ? AND guild_id = ?",
                (interaction.user.id, interaction.guild.id)
            )
            
            if not rows:
                await interaction.followup.send(
                    "📦 Your inventory is empty. Visit the shop with `/shop` to purchase items!",
                    ephemeral=True
                )
                return
            
            # Create inventory embed
            embed = discord.Embed(
                title=f"📦 {interaction.user.display_name}'s Inventory",
                color=discord.Color.blue()
            )
            
            item_count = 0
            for row in rows:
                item_id = row['item_id']
                quantity = row['quantity']
                
                # Find item details
                item_details = next((i for i in self.shop_items["items"] if i["id"] == item_id), None)
                
                if item_details:
                    item_text = f"**Type:** {item_details['type'].title()}\n"
                    item_text += f"**Quantity:** {quantity}\n"
                    
                    embed.add_field(
                        name=item_details["name"],
                        value=item_text,
                        inline=True
                    )
                    item_count += 1
            
            embed.set_footer(text=f"Total items: {item_count}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in inventory command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while accessing your inventory. Please try again.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Add the shop cog to the bot."""
    await bot.add_cog(ShopCog(bot))
    logger.info("Shop cog loaded successfully")
