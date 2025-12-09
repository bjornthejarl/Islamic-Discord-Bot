import asyncpg
import logging
import os
import re
import itertools
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    """Database manager for the bot using PostgreSQL."""
    
    def __init__(self, db_path: str = None):
        # db_path is ignored in favor of env var for Postgres, but kept for signature compatibility
        self.db_url = os.getenv("DATABASE_URL")
        self._pool = None

    async def connect(self):
        """Establish connection pool to the database."""
        if not self.db_url:
            logger.error("DATABASE_URL not found in environment variables")
            raise ValueError("DATABASE_URL not set")
            
        try:
            self._pool = await asyncpg.create_pool(self.db_url)
            await self._init_tables()
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def close(self):
        """Close the database connection."""
        if self._pool:
            await self._pool.close()
            logger.info("Database connection closed")

    async def _init_tables(self):
        """Initialize database tables."""
        async with self._pool.acquire() as conn:
            # Users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT,
                    guild_id BIGINT,
                    ilm_coins INTEGER DEFAULT 100,
                    good_deed_points INTEGER DEFAULT 0,
                    total_earned INTEGER DEFAULT 100,
                    total_spent INTEGER DEFAULT 0,
                    total_donated INTEGER DEFAULT 0,
                    daily_streak INTEGER DEFAULT 0,
                    last_daily TIMESTAMP,
                    games_played INTEGER DEFAULT 0,
                    quizzes_completed INTEGER DEFAULT 0,
                    total_learning_time INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, guild_id)
                )
            """)
            
            # Transactions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    guild_id BIGINT,
                    type TEXT,
                    amount INTEGER,
                    source TEXT,
                    description TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id, guild_id) REFERENCES users (user_id, guild_id)
                )
            """)
            
            # Inventory/Items table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    user_id BIGINT,
                    guild_id BIGINT,
                    item_id TEXT,
                    quantity INTEGER DEFAULT 1,
                    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, guild_id, item_id),
                    FOREIGN KEY (user_id, guild_id) REFERENCES users (user_id, guild_id)
                )
            """)
            
            # Achievements table (New)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_achievements (
                    user_id BIGINT,
                    guild_id BIGINT,
                    achievement_id TEXT,
                    achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, guild_id, achievement_id),
                    FOREIGN KEY (user_id, guild_id) REFERENCES users (user_id, guild_id)
                )
            """)

            # Guild Settings table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id BIGINT PRIMARY KEY,
                    daily_content_channel_id BIGINT,
                    prayer_times_city TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def _convert_query(self, query: str) -> str:
        """Convert SQLite ? placeholders to PostgreSQL $n placeholders."""
        # Simple regex to replace ? with $1, $2, etc.
        # This assumes ? are used as placeholders and not in string literals.
        # Given the codebase, this is a safe assumption.
        counter = itertools.count(1)
        return re.sub(r'\?', lambda m: f"${next(counter)}", query)

    async def execute(self, query: str, parameters: tuple = ()) -> str:
        """Execute a query."""
        if not self._pool:
            await self.connect()
        
        pg_query = self._convert_query(query)
        async with self._pool.acquire() as conn:
            return await conn.execute(pg_query, *parameters)

    async def fetchone(self, query: str, parameters: tuple = ()) -> Optional[asyncpg.Record]:
        """Fetch a single row."""
        if not self._pool:
            await self.connect()
            
        pg_query = self._convert_query(query)
        async with self._pool.acquire() as conn:
            return await conn.fetchrow(pg_query, *parameters)

    async def fetchall(self, query: str, parameters: tuple = ()) -> List[asyncpg.Record]:
        """Fetch all rows."""
        if not self._pool:
            await self.connect()
            
        pg_query = self._convert_query(query)
        async with self._pool.acquire() as conn:
            return await conn.fetch(pg_query, *parameters)

    async def commit(self):
        """Commit changes. No-op for asyncpg with autocommit."""
        # asyncpg executes in autocommit mode by default outside of transaction blocks
        pass
