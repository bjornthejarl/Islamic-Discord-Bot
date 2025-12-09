"""
Economy utility functions for the Discord bot.
Handles user data management, transactions, and economy operations.
"""

import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging
from src.database import Database

logger = logging.getLogger(__name__)


class EconomyUtils:
    """Utility class for economy system operations."""
    
    def __init__(self, db_path: str = "ilm_garden.db"):
        self.db = Database(db_path)
        self.settings = self._load_settings()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load economy settings from JSON file."""
        # Settings can still be in JSON as they are config, not user data
        settings_path = "src/data/economy/settings.json"
        try:
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading economy settings: {e}")
            return {}
    
    async def get_user_data(self, user_id: int, guild_id: int) -> Dict[str, Any]:
        """Get user economy data, creating if it doesn't exist. Uses short TTL cache."""
        cache_key = f"{user_id}_{guild_id}"
        now = datetime.utcnow()
        
        # Check cache
        if hasattr(self, "_user_cache") and cache_key in self._user_cache:
            cache_entry = self._user_cache[cache_key]
            if (now - cache_entry["timestamp"]) < timedelta(seconds=10):
                return cache_entry["data"]
        
        # Fetch from DB
        row = await self.db.fetchone(
            "SELECT * FROM users WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id)
        )
        
        data = None
        if row:
            data = self._row_to_dict(row)
        else:
            # Create new user
            await self.db.execute(
                """
                INSERT INTO users (
                    user_id, guild_id, ilm_coins, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, guild_id, 100, now, now)
            )
            await self.db.commit()
            
            # Recursively get fresh data (this recursion is safe as it will hit the row block)
            # But let's just make it explicit to avoid recursion loops
            data = await self.get_user_data(user_id, guild_id)
            return data # Already cached by the recursive call if we implemented it, but wait..
            
            # Let's fix the recursion logic. calling get_user_data again will hit DB again.
            # We already inserted. Let's just return the default dict or fetch again.
            # Fetching again is safer.
        
        # Update cache
        if not hasattr(self, "_user_cache"):
            self._user_cache = {}
        
        self._user_cache[cache_key] = {
            "data": data,
            "timestamp": now
        }
        
        return data
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dictionary matching old structure."""
        return {
            "user_id": row["user_id"],
            "guild_id": row["guild_id"],
            "economy": {
                "ilm_coins": row["ilm_coins"],
                "good_deed_points": row["good_deed_points"],
                "total_earned": row["total_earned"],
                "total_spent": row["total_spent"],
                "total_donated": row["total_donated"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            },
            "activities": {
                "daily_streak": row["daily_streak"],
                "last_daily": row["last_daily"],
                "games_played": row["games_played"],
                "quizzes_completed": row["quizzes_completed"],
                "total_learning_time": row["total_learning_time"]
            }
        }
    
    async def save_user_data(self, user_id: int, guild_id: int, user_data: Dict[str, Any]) -> None:
        """
        Save user economy data.
        Note: In the new DB implementation, this is mostly for compatibility.
        Direct DB updates are preferred.
        """
        economy = user_data["economy"]
        activities = user_data["activities"]
        
        await self.db.execute(
            """
            UPDATE users SET
                ilm_coins = ?,
                good_deed_points = ?,
                total_earned = ?,
                total_spent = ?,
                total_donated = ?,
                daily_streak = ?,
                last_daily = ?,
                games_played = ?,
                quizzes_completed = ?,
                total_learning_time = ?,
                updated_at = ?
            WHERE user_id = ? AND guild_id = ?
            """,
            (
                economy["ilm_coins"],
                economy["good_deed_points"],
                economy["total_earned"],
                economy["total_spent"],
                economy["total_donated"],
                activities["daily_streak"],
                activities["last_daily"],
                activities["games_played"],
                activities["quizzes_completed"],
                activities["total_learning_time"],
                datetime.utcnow(),
                user_id,
                guild_id
            )
        )
        await self.db.commit()
    
    async def add_coins(self, user_id: int, guild_id: int, amount: int, source: str = "unknown") -> bool:
        """Add coins to user's balance and log transaction."""
        if amount <= 0:
            return False
            
        # Ensure user exists
        await self.get_user_data(user_id, guild_id)
        
        await self.db.execute(
            """
            UPDATE users SET 
                ilm_coins = ilm_coins + ?,
                total_earned = total_earned + ?,
                updated_at = ?
            WHERE user_id = ? AND guild_id = ?
            """,
            (amount, amount, datetime.utcnow(), user_id, guild_id)
        )
        
        await self.log_transaction(user_id, guild_id, "earn", amount, source)
        await self.db.commit()
        
        logger.info(f"Added {amount} coins to user {user_id} from {source}")
        return True
    
    async def remove_coins(self, user_id: int, guild_id: int, amount: int, source: str = "unknown") -> bool:
        """Remove coins from user's balance if they have enough."""
        user_data = await self.get_user_data(user_id, guild_id)
        
        if user_data["economy"]["ilm_coins"] < amount:
            return False
        
        await self.db.execute(
            """
            UPDATE users SET 
                ilm_coins = ilm_coins - ?,
                total_spent = total_spent + ?,
                updated_at = ?
            WHERE user_id = ? AND guild_id = ?
            """,
            (amount, amount, datetime.utcnow(), user_id, guild_id)
        )
        
        await self.log_transaction(user_id, guild_id, "spend", -amount, source)
        await self.db.commit()
        
        logger.info(f"Removed {amount} coins from user {user_id} for {source}")
        return True
    
    async def transfer_coins(self, from_user_id: int, to_user_id: int, guild_id: int, amount: int) -> bool:
        """Transfer coins between users."""
        if not self.settings.get("economy", {}).get("transfer_enabled", True):
            return False
        
        min_amount = self.settings.get("economy", {}).get("min_transfer_amount", 10)
        max_amount = self.settings.get("economy", {}).get("max_transfer_amount", 1000)
        
        if amount < min_amount or amount > max_amount:
            return False
        
        # Check balance
        sender_data = await self.get_user_data(from_user_id, guild_id)
        if sender_data["economy"]["ilm_coins"] < amount:
            return False
            
        # Perform transfer
        await self.remove_coins(from_user_id, guild_id, amount, "transfer_out")
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
            if isinstance(last_daily, str):
                last_daily_date = datetime.fromisoformat(last_daily)
            else:
                last_daily_date = last_daily
                
            if (now - last_daily_date) < timedelta(hours=20):
                return {"success": False, "message": "You've already claimed your daily reward today!"}
        
        # Calculate streak
        streak = activities["daily_streak"]
        if last_daily:
            if isinstance(last_daily, str):
                last_daily_date = datetime.fromisoformat(last_daily)
            else:
                last_daily_date = last_daily
                
            if (now - last_daily_date) < timedelta(hours=48):
                streak += 1
            else:
                streak = 1
        else:
            streak = 1
        
        # Calculate reward
        base_reward = economy_settings.get("daily_base_reward", 50)
        streak_bonus = min(
            streak * economy_settings.get("daily_streak_bonus", 10),
            economy_settings.get("max_streak", 7) * economy_settings.get("daily_streak_bonus", 10)
        )
        
        total_reward = base_reward + streak_bonus
        
        # Weekly bonus check
        weekly_bonus = 0
        if streak % 7 == 0:
            weekly_bonus = economy_settings.get("weekly_bonus", 100)
            total_reward += weekly_bonus
        
        # Update user data
        await self.db.execute(
            """
            UPDATE users SET 
                daily_streak = ?,
                last_daily = ?,
                ilm_coins = ilm_coins + ?,
                total_earned = total_earned + ?,
                updated_at = ?
            WHERE user_id = ? AND guild_id = ?
            """,
            (streak, now, total_reward, total_reward, now, user_id, guild_id)
        )
        
        await self.log_transaction(user_id, guild_id, "earn", total_reward, "daily_reward")
        await self.db.commit()
        
        result = {
            "success": True,
            "reward": total_reward,
            "base_reward": base_reward,
            "streak_bonus": streak_bonus,
            "streak": streak,
            "message": f"Daily reward claimed! You received {total_reward} Ilm Coins."
        }
        
        if weekly_bonus > 0:
            result["weekly_bonus"] = weekly_bonus
            result["message"] += f" (Weekly bonus: +{weekly_bonus} IC)"
        
        return result
    
    async def get_leaderboard(self, guild_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get server leaderboard by coin balance."""
        rows = await self.db.fetchall(
            """
            SELECT user_id, ilm_coins, good_deed_points, total_earned 
            FROM users 
            WHERE guild_id = ? 
            ORDER BY ilm_coins DESC 
            LIMIT ?
            """,
            (guild_id, limit)
        )
        
        return [dict(row) for row in rows]
    
    async def log_transaction(self, user_id: int, guild_id: int, 
                            transaction_type: str, amount: int, source: str) -> None:
        """Log a transaction for auditing purposes."""
        await self.db.execute(
            """
            INSERT INTO transactions (
                user_id, guild_id, type, amount, source, description
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id, 
                guild_id, 
                transaction_type, 
                amount, 
                source, 
                f"{transaction_type.title()} from {source}"
            )
        )
    
    async def increment_stat(self, user_id: int, guild_id: int, stat_name: str, amount: int = 1) -> None:
        """Increment a specific user statistic."""
        valid_stats = [
            "games_played", "quizzes_completed", "total_learning_time",
            "daily_streak", "good_deed_points"
        ]
        
        if stat_name not in valid_stats:
            logger.warning(f"Attempted to increment invalid stat: {stat_name}")
            return

        await self.get_user_data(user_id, guild_id)  # Ensure user exists

        query = f"UPDATE users SET {stat_name} = {stat_name} + ?, updated_at = ? WHERE user_id = ? AND guild_id = ?"
        await self.db.execute(query, (amount, datetime.utcnow(), user_id, guild_id))
        await self.db.commit()