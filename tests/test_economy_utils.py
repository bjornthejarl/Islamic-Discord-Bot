import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from src.utils.economy_utils import EconomyUtils

# Convert row to dict helper since the actual code relies on row object behaving like a dict or having keys
class MockRow(dict):
    def __init__(self, data):
        super().__init__(data)

@pytest.mark.asyncio
async def test_get_user_data_new_user():
    """Test that get_user_data creates a user if not found."""
    with patch('src.utils.economy_utils.Database') as MockDB:
        mock_db = MockDB.return_value
        
        full_user_data = {
            "user_id": 123, 
            "guild_id": 456, 
            "ilm_coins": 100, 
            "good_deed_points": 0, 
            "total_earned": 100,
            "total_spent": 0,
            "total_donated": 0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "daily_streak": 0,
            "last_daily": None,
            "games_played": 0,
            "quizzes_completed": 0,
            "total_learning_time": 0
        }
        
        # First call returns None (not found), Second call returns the new user
        mock_db.fetchone = AsyncMock(side_effect=[
            None, 
            MockRow(full_user_data)
        ])
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()

        utils = EconomyUtils()
        
        data = await utils.get_user_data(123, 456)
        
        # Verify result structure (it returns nested dict)
        assert data["economy"]["ilm_coins"] == 100
        
        # Verify Insert was called
        mock_db.execute.assert_called()
        args = mock_db.execute.call_args[0]
        assert "INSERT INTO users" in args[0]

@pytest.mark.asyncio
async def test_add_coins():
    """Test adding coins updates user and logs transaction."""
    with patch('src.utils.economy_utils.Database') as MockDB:
        mock_db = MockDB.return_value
        
        full_user_data = {
            "user_id": 123, 
            "guild_id": 456, 
            "ilm_coins": 100, 
            "good_deed_points": 0, 
            "total_earned": 100,
            "total_spent": 0,
            "total_donated": 0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "daily_streak": 0,
            "last_daily": None,
            "games_played": 0,
            "quizzes_completed": 0,
            "total_learning_time": 0
        }

        # Mock get_user_data internal call
        mock_db.fetchone = AsyncMock(return_value=MockRow(full_user_data))
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()

        utils = EconomyUtils()
        
        # Add 50 coins
        success = await utils.add_coins(123, 456, 50, "test_source")
        
        assert success is True
        
        # update query + log transaction query
        assert mock_db.execute.call_count >= 2
        
        # Verify update query
        update_call = mock_db.execute.call_args_list[0]
        assert "UPDATE users" in update_call[0][0]
        
@pytest.mark.asyncio
async def test_transfer_coins_success():
    """Test successful coin transfer."""
    with patch('src.utils.economy_utils.Database') as MockDB:
        mock_db = MockDB.return_value
        
        # We need mock returns for sender and receiver
        base_data = {
            "total_spent": 0, "total_donated": 0,
            "created_at": datetime.now(), "updated_at": datetime.now(),
            "daily_streak": 0, "last_daily": None,
            "games_played": 0, "quizzes_completed": 0, "total_learning_time": 0
        }
        
        sender_data = MockRow({**base_data, "user_id": 1, "guild_id": 1, "ilm_coins": 500, "good_deed_points": 0, "total_earned": 500})
        receiver_data = MockRow({**base_data, "user_id": 2, "guild_id": 1, "ilm_coins": 100, "good_deed_points": 0, "total_earned": 100})
        
        # Side effect for fetchone when checking users
        mock_db.fetchone = AsyncMock(side_effect=[sender_data, receiver_data])

        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()
        
        utils = EconomyUtils()
        
        # Also mock remove_coins and add_coins inside transfer_coins to avoid complex nesting recursion issues or failure
        # Actually transfer_coins calls remove_coins and add_coins. 
        # Since we are testing transfer_coins logic (checks bounds, balance), and the calls to remove/add.
        # But remove_coins/add_coins call DB execute.
        # It's better to just let them run or mock them.
        # If we let them run, they call get_user_data again, which calls fetchone.
        # Our side_effect has 2 items. remove_coins calls get_user_data (3rd call), add_coins calls get_user_data (4th call).
        # We need more items in side_effect.
        
        mock_db.fetchone = AsyncMock(side_effect=[
            sender_data,   # transfer check
            sender_data,   # remove_coins check
            receiver_data  # add_coins check
        ])

        success = await utils.transfer_coins(1, 2, 1, 200)
        
        assert success is True
        # Verify calls occurred
        # We expect DB executes for remove (update), log, add (update), log.
        assert mock_db.execute.call_count >= 4
