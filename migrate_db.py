import asyncio
import json
import os
import logging
from src.database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Migration")

async def migrate_data():
    """Migrate data from JSON files to SQLite database."""
    db = Database()
    await db.connect()
    
    data_path = "src/data/economy/users"
    if not os.path.exists(data_path):
        logger.warning(f"Data directory {data_path} not found. Skipping migration.")
        await db.close()
        return

    files = [f for f in os.listdir(data_path) if f.endswith('.json')]
    logger.info(f"Found {len(files)} user files to migrate.")
    
    count = 0
    for filename in files:
        try:
            file_path = os.path.join(data_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
            
            user_id = user_data.get("user_id")
            guild_id = user_data.get("guild_id")
            
            if not user_id or not guild_id:
                logger.warning(f"Skipping {filename}: Missing user_id or guild_id")
                continue
                
            economy = user_data.get("economy", {})
            activities = user_data.get("activities", {})
            
            # Check if user already exists
            existing = await db.fetchone(
                "SELECT 1 FROM users WHERE user_id = ? AND guild_id = ?",
                (user_id, guild_id)
            )
            
            if existing:
                logger.info(f"User {user_id} already exists in DB. Skipping.")
                continue
            
            # Insert into database
            await db.execute("""
                INSERT INTO users (
                    user_id, guild_id, ilm_coins, good_deed_points, 
                    total_earned, total_spent, total_donated,
                    daily_streak, last_daily, games_played, 
                    quizzes_completed, total_learning_time,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                guild_id,
                economy.get("ilm_coins", 0),
                economy.get("good_deed_points", 0),
                economy.get("total_earned", 0),
                economy.get("total_spent", 0),
                economy.get("total_donated", 0),
                activities.get("daily_streak", 0),
                activities.get("last_daily"),
                activities.get("games_played", 0),
                activities.get("quizzes_completed", 0),
                activities.get("total_learning_time", 0),
                economy.get("created_at"),
                economy.get("updated_at")
            ))
            
            count += 1
            if count % 10 == 0:
                logger.info(f"Migrated {count} users...")
                
        except Exception as e:
            logger.error(f"Error migrating {filename}: {e}")
            
    await db.commit()
    await db.close()
    logger.info(f"Migration completed. Successfully migrated {count} users.")

if __name__ == "__main__":
    asyncio.run(migrate_data())
