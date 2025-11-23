"""
Economy utility functions for the Discord bot.
Handles user data management, transactions, and economy operations.
"""

import json
import os
import asyncio
import aiofiles
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class EconomyUtils:
    """Utility class for economy system operations."""
    
    def __init__(self, data_path: str = "src/data/economy"):
        self.data_path = data_path
        self.settings = self._load_settings()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load economy settings from JSON file."""
        settings_path = os.path.join(self.data_path, "settings.json")
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Economy settings file not found at {settings_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing economy settings: {e}")
            return {}
    
    async def get_user_data(self, user_id: int, guild_id: int) -> Dict[str, Any]:
        """Get user economy data, creating if it doesn't exist."""
        user_file = os.path.join(self.data_path, "users", f"{user_id}_{guild_id}.json")
        
        try:
            async with aiofiles.open(user_file, 'r', encoding='utf-8') as f:
                return json.loads(await f.read())
        except FileNotFoundError:
            # Create new user data
            user_data = {
                "user_id": user_id,
                "guild_id": guild_id,
                "economy": {
                    "ilm_coins": 100,  # Starting coins
                    "good_deed_points": 0,
                    "total_earned": 100,
                    "total_spent": 0,
                    "total_donated": 0,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                },
                "activities": {
                    "daily_streak": 0,
                    "last_daily": None,
                    "last_quiz": None,
                    "games_played": 0,
                    "quizzes_completed": 0,
                    "total_learning_time": 0
                },
                "inventory": {},
                "achievements": {},
                "equipped_items": {},
                "settings": {
                    "notifications": True,
                    "public_profile": True,
                    "auto_equip": False
                }
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(user_file), exist_ok=True)
            
            # Save new user data
            async with aiofiles.open(user_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(user_data, indent=2, ensure_ascii=False))
            
            logger.info(f"Created new economy profile for user {user_id} in guild {guild_id}")
            return user_data
    
    async def save_user_data(self, user_id: int, guild_id: int, user_data: Dict[str, Any]) -> None:
        """Save user economy data."""
        user_file = os.path.join(self.data_path, "users", f"{user_id}_{guild_id}.json")
        
        # Update timestamp
        user_data["economy"]["updated_at"] = datetime.utcnow().isoformat()
        
        try:
            async with aiofiles.open(user_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(user_data, indent=2, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Error saving user data for {user_id}: {e}")
    
    async def add_coins(self, user_id: int, guild_id: int, amount: int, source: str = "unknown") -> bool:
        """Add coins to user's balance and log transaction."""
        user_data = await self.get_user_data(user_id, guild_id)
        
        if amount <= 0:
            return False
        
        user_data["economy"]["ilm_coins"] += amount
        user_data["economy"]["total_earned"] += amount
        
        await self.save_user_data(user_id, guild_id, user_data)
        await self.log_transaction(user_id, guild_id, "earn", amount, source)
        
        logger.info(f"Added {amount} coins to user {user_id} from {source}")
        return True
    
    async def remove_coins(self, user_id: int, guild_id: int, amount: int, source: str = "unknown") -> bool:
        """Remove coins from user's balance if they have enough."""
        user_data = await self.get_user_data(user_id, guild_id)
        
        if user_data["economy"]["ilm_coins"] < amount:
            return False
        
        user_data["economy"]["ilm_coins"] -= amount
        user_data["economy"]["total_spent"] += amount
        
        await self.save_user_data(user_id, guild_id, user_data)
        await self.log_transaction(user_id, guild_id, "spend", -amount, source)
        
        logger.info(f"Removed {amount} coins from user {user_id} for {source}")
        return True
    
    async def transfer_coins(self, from_user_id: int, to_user_id: int, guild_id: int, amount: int) -> bool:
        """Transfer coins between users."""
        # Check if transfer is enabled
        if not self.settings.get("economy", {}).get("transfer_enabled", True):
            return False
        
        min_amount = self.settings.get("economy", {}).get("min_transfer_amount", 10)
        max_amount = self.settings.get("economy", {}).get("max_transfer_amount", 1000)
        
        if amount < min_amount or amount > max_amount:
            return False
        
        # Remove coins from sender
        if not await self.remove_coins(from_user_id, guild_id, amount, "transfer_out"):
            return False
        
        # Add coins to receiver
        await self.add_coins(to_user_id, guild_id, amount, "transfer_in")
        
        logger.info(f"Transferred {amount} coins from {from_user_id} to {to_user_id}")
        return True
    
    async def claim_daily_reward(self, user_id: int, guild_id: int) -> Dict[str, Any]:
        """Claim daily reward with streak bonuses."""
        user_data = await self.get_user_data(user_id, guild_id)
        activities = user_data["activities"]
        economy_settings = self.settings.get("economy", {})
        
        now = datetime.utcnow()
        last_daily = activities.get("last_daily")
        
        # Check if user can claim daily
        if last_daily:
            last_daily_date = datetime.fromisoformat(last_daily)
            if (now - last_daily_date) < timedelta(hours=20):
                return {"success": False, "message": "You've already claimed your daily reward today!"}
        
        # Calculate streak
        if last_daily:
            last_daily_date = datetime.fromisoformat(last_daily)
            if (now - last_daily_date) < timedelta(hours=48):
                activities["daily_streak"] += 1
            else:
                activities["daily_streak"] = 1
        else:
            activities["daily_streak"] = 1
        
        # Calculate reward
        base_reward = economy_settings.get("daily_base_reward", 50)
        streak_bonus = min(
            activities["daily_streak"] * economy_settings.get("daily_streak_bonus", 10),
            economy_settings.get("max_streak", 7) * economy_settings.get("daily_streak_bonus", 10)
        )
        
        total_reward = base_reward + streak_bonus
        
        # Weekly bonus check
        if activities["daily_streak"] % 7 == 0:
            weekly_bonus = economy_settings.get("weekly_bonus", 100)
            total_reward += weekly_bonus
        
        # Update user data
        activities["last_daily"] = now.isoformat()
        await self.add_coins(user_id, guild_id, total_reward, "daily_reward")
        
        result = {
            "success": True,
            "reward": total_reward,
            "base_reward": base_reward,
            "streak_bonus": streak_bonus,
            "streak": activities["daily_streak"],
            "message": f"Daily reward claimed! You received {total_reward} Ilm Coins."
        }
        
        if activities["daily_streak"] % 7 == 0:
            result["weekly_bonus"] = weekly_bonus
            result["message"] += f" (Weekly bonus: +{weekly_bonus} IC)"
        
        return result
    
    async def get_leaderboard(self, guild_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get server leaderboard by coin balance."""
        leaderboard = []
        users_dir = os.path.join(self.data_path, "users")
        
        if not os.path.exists(users_dir):
            return leaderboard
        
        for filename in os.listdir(users_dir):
            if filename.endswith('.json'):
                try:
                    file_path = os.path.join(users_dir, filename)
                    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                        user_data = json.loads(await f.read())
                    
                    # Only include users from this guild
                    if user_data.get("guild_id") == guild_id:
                        leaderboard.append({
                            "user_id": user_data["user_id"],
                            "ilm_coins": user_data["economy"]["ilm_coins"],
                            "good_deed_points": user_data["economy"]["good_deed_points"],
                            "total_earned": user_data["economy"]["total_earned"]
                        })
                except Exception as e:
                    logger.error(f"Error reading user file {filename}: {e}")
        
        # Sort by coin balance (descending)
        leaderboard.sort(key=lambda x: x["ilm_coins"], reverse=True)
        return leaderboard[:limit]
    
    async def log_transaction(self, user_id: int, guild_id: int, 
                            transaction_type: str, amount: int, source: str) -> None:
        """Log a transaction for auditing purposes."""
        transaction_file = os.path.join(self.data_path, "transactions", f"{user_id}_{guild_id}.json")
        
        transaction = {
            "transaction_id": f"txn_{int(datetime.utcnow().timestamp())}_{user_id}",
            "user_id": user_id,
            "guild_id": guild_id,
            "type": transaction_type,
            "amount": amount,
            "currency": "ilm_coins",
            "source": source,
            "description": f"{transaction_type.title()} from {source}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(transaction_file), exist_ok=True)
        
        try:
            # Read existing transactions
            transactions = []
            if os.path.exists(transaction_file):
                async with aiofiles.open(transaction_file, 'r', encoding='utf-8') as f:
                    transactions = json.loads(await f.read())
            
            # Add new transaction
            transactions.append(transaction)
            
            # Keep only last 100 transactions
            if len(transactions) > 100:
                transactions = transactions[-100:]
            
            # Save updated transactions
            async with aiofiles.open(transaction_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(transactions, indent=2, ensure_ascii=False))
                
        except Exception as e:
            logger.error(f"Error logging transaction for user {user_id}: {e}")