import asyncio
import logging
import os
from src.database import Database
from src.utils.economy_utils import EconomyUtils

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestDB")

async def test_database():
    """Test database operations."""
    logger.info("Starting database test...")
    
    db_name = "test_ilm_garden_v2.db"
    
    # Cleanup existing test DB if any
    if os.path.exists(db_name):
        try:
            os.remove(db_name)
            logger.info("Cleaned up existing test DB")
        except Exception as e:
            logger.warning(f"Could not remove existing test DB: {e}")
            
    # Initialize DB
    db = Database(db_name)
    await db.connect()
    
    # Initialize EconomyUtils with test DB
    economy = EconomyUtils(db_name)
    
    # Test 1: Create User
    logger.info("Test 1: Create User")
    user_id = 123456789
    guild_id = 987654321
    
    user_data = await economy.get_user_data(user_id, guild_id)
    logger.info(f"User Data: {user_data}")
    coins = user_data["economy"]["ilm_coins"]
    logger.info(f"Coins: {coins} (Type: {type(coins)})")
    assert coins == 100
    logger.info("✅ User creation passed")
    
    # Test 2: Add Coins
    logger.info("Test 2: Add Coins")
    await economy.add_coins(user_id, guild_id, 50, "test_add")
    user_data = await economy.get_user_data(user_id, guild_id)
    assert user_data["economy"]["ilm_coins"] == 150
    logger.info("✅ Add coins passed")
    
    # Test 3: Remove Coins
    logger.info("Test 3: Remove Coins")
    await economy.remove_coins(user_id, guild_id, 30, "test_remove")
    user_data = await economy.get_user_data(user_id, guild_id)
    assert user_data["economy"]["ilm_coins"] == 120
    logger.info("✅ Remove coins passed")
    
    # Test 4: Transaction Log
    logger.info("Test 4: Transaction Log")
    rows = await db.fetchall("SELECT * FROM transactions WHERE user_id = ?", (user_id,))
    assert len(rows) == 2  # Add and Remove
    logger.info("✅ Transaction log passed")
    
    # Test 5: Daily Reward
    logger.info("Test 5: Daily Reward")
    result = await economy.claim_daily_reward(user_id, guild_id)
    assert result["success"] is True
    user_data = await economy.get_user_data(user_id, guild_id)
    assert user_data["activities"]["daily_streak"] == 1
    logger.info("✅ Daily reward passed")
    
    # Cleanup
    await db.close()
    await economy.db.close()
    
    # Give it a moment to release the file lock
    await asyncio.sleep(0.1)
    
    if os.path.exists(db_name):
        try:
            os.remove(db_name)
            logger.info("Test DB cleaned up")
        except Exception as e:
            logger.warning(f"Could not remove test DB: {e}")

if __name__ == "__main__":
    asyncio.run(test_database())
