# Discord Verify Bot

A production-ready Discord bot that uses slash commands to verify users with gender-specific roles. The bot automatically registers and syncs slash commands globally on startup.

## Features

- **Slash Commands**: Modern Discord slash commands for better user experience
- **Global Auto-Sync**: Commands are automatically synced globally across all guilds on every startup
- **Role-Based Permissions**: Only users with specific roles can use verification commands
- **Role Management**: Assigns verification roles and removes unverified roles automatically
- **Safety Checks**: Prevents verifying bots, handles missing roles, and manages permissions gracefully
- **Structured Logging**: Clear, structured console logging for monitoring and debugging
- **Complete Economy System**: Halal-compliant currency and rewards system
- **Educational Games**: Interactive Islamic knowledge games with rewards
- **Shop System**: Halal-compliant items and purchases
- **Profile System**: User progression, achievements, and leaderboards
- **Help System**: Comprehensive DM-based help system

## Commands

### Verification Commands

#### `/verify_female`
- **Description**: Verify a user as female
- **Required Role**: Female Verifier Role (ID: 1438678339786244096)
- **Action**:
  - Assigns Female Role (ID: 1438734916929196054) to target user
  - Removes Female Unverified Role (ID: 1438758944322355200) if present
- **Permissions**: Guild-only, requires bot to have Manage Roles permission

#### `/verify_male`
- **Description**: Verify a user as male
- **Required Role**: Male Verifier Role (ID: 1438678549358706781)
- **Action**:
  - Assigns Male Role (ID: 1438734872670769323) to target user
  - Removes Male Unverified Role (ID: 1438734829192740955) if present
- **Permissions**: Guild-only, requires bot to have Manage Roles permission

### Moderation Commands

#### `/purge`
- **Description**: Delete multiple messages at once (respects 1-day age limit)
- **Permissions**: Requires Manage Messages permission
- **Options**: Number of messages to delete (1-100)

### Economy Commands

#### `/balance`
- **Description**: Check your Ilm Coins and Good Deed Points balance
- **Options**: User (moderators can check other users)

#### `/daily`
- **Description**: Claim your daily Ilm Coins reward with streak bonuses

#### `/transfer`
- **Description**: Transfer Ilm Coins to another user
- **Options**: Recipient, amount (10-1000), optional message

#### `/donate`
- **Description**: Donate Ilm Coins to community funds
- **Options**: Amount, cause (General, Education, Charity, Community)

#### `/leaderboard`
- **Description**: View server leaderboards for various metrics
- **Options**: Type (Coins, GDP, Total Earned), scope, limit

### Game Commands

#### `/quiz`
- **Description**: Test your Islamic knowledge with multiple-choice questions
- **Options**: Category (Quran, Hadith, Prophets, Prayer, Calendar, Random), difficulty

#### `/verse_match`
- **Description**: Match Quran verses to their correct surah names
- **Options**: Difficulty (Easy, Medium, Hard)

#### `/hadith_game`
- **Description**: Learn about Hadith through interactive trivia
- **Options**: Mode (Completion, Knowledge, Narrator, Random)

### Shop Commands

#### `/shop`
- **Description**: Browse the Halal shop for items
- **Options**: Category (All, Knowledge, Cosmetic, Practical, Prestige, Utility)

#### `/buy`
- **Description**: Purchase an item from the shop
- **Options**: Item ID

#### `/inventory`
- **Description**: View your purchased items and inventory

### Profile Commands

#### `/profile`
- **Description**: View your profile and achievements
- **Options**: User (view another user's profile)

#### `/achievements`
- **Description**: View all available achievements and your progress

### Help Commands

#### `/help`
- **Description**: Get comprehensive help about bot commands via DMs

## Project Structure

```
discord_verify_bot/
├── bot.py                 # Main bot entry point
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .env.example          # Environment variables template
└── src/
    ├── __init__.py
    ├── config.py         # Configuration and environment variables
    ├── logging_setup.py  # Structured logging setup
    ├── cogs/
    │   ├── __init__.py
    │   ├── verify.py     # Verify commands Cog
    │   ├── moderation.py # Moderation commands Cog
    │   ├── purge.py      # Message purging Cog
    │   ├── economy.py    # Economy system Cog
    │   ├── games.py      # Educational games Cog
    │   ├── shop.py       # Shop system Cog
    │   ├── profile.py    # Profile and achievements Cog
    │   └── help.py       # Help system Cog
    ├── utils/
    │   ├── __init__.py
    │   ├── checks.py     # Permission checks and validations
    │   ├── economy_utils.py # Economy system utilities
    │   └── game_utils.py    # Game system utilities
    └── data/
        ├── economy/
        │   ├── settings.json
        │   ├── users/     # User economy data
        │   └── transactions/ # Transaction logs
        ├── games/         # Game content data
        ├── profiles/      # User profiles and achievements
        └── shop/          # Shop items and inventories
```

## Economy System

### Currency Types
- **Ilm Coins (IC)**: Main currency earned through games, daily rewards, and activities
- **Good Deed Points (GDP)**: Prestige currency earned through donations and charitable acts

### Features
- Daily rewards with streak bonuses
- Coin transfers between users
- Charitable donations with GDP rewards
- Server leaderboards
- Halal-compliant mechanics only

## Game System

### Available Games
1. **Islamic Knowledge Quiz**: Multiple-choice questions on various Islamic topics
2. **Quran Verse Match**: Match Quran verses to correct surah names
3. **Hadith Trivia**: Interactive Hadith learning games
4. **Reaction-based gameplay**: Interactive reaction-based interfaces
5. **Educational rewards**: Earn while learning Islamic knowledge

### Game Features
- Multiple difficulty levels
- Category filtering
- Performance-based rewards
- Time-limited challenges
- Educational explanations

## Shop System

### Item Categories
- **Knowledge**: Educational items like books and courses
- **Cosmetic**: Visual items for profile customization
- **Practical**: Useful items like prayer mats
- **Prestige**: Achievement and recognition items
- **Utility**: Boosts and temporary benefits

### Shop Features
- Halal-compliant items only
- Inventory management
- Item effects and benefits
- Category filtering
- Purchase confirmation

## Profile System

### Features
- User statistics tracking
- Achievement system with 10+ achievements
- Progress tracking
- Level system based on total earnings
- Server leaderboards
- Achievement rewards

### Achievement Categories
- Learning and knowledge
- Charity and good deeds
- Consistency and dedication
- Economy and wealth
- Community participation

## Setup Instructions

### 1. Prerequisites

- Python 3.10 or higher
- Discord Bot Token

### 2. Discord Developer Portal Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a New Application
3. Go to the "Bot" section
4. Create a bot and copy the token
5. Enable these privileged gateway intents:
   - **SERVER MEMBERS INTENT** (required for role management)

### 3. Bot Installation

1. In the "OAuth2" → "URL Generator" section:
2. Select these scopes:
   - `bot`
   - `applications.commands`
3. Select these bot permissions:
   - `Manage Roles`
   - `Manage Messages` (for purge command)
   - `Read Message History` (for purge command)
4. Use the generated URL to invite the bot to your servers

### 4. Environment Setup

1. Clone or download this project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
4. Edit `.env` with your actual values:
   ```
   DISCORD_TOKEN=your_actual_bot_token_here
   ```

### 5. Role Setup

**Critical**: In each server where you want to use the bot, ensure the bot's role is ABOVE all roles it needs to manage:
- Female Role (1438734916929196054)
- Male Role (1438734872670769323)
- Female Unverified Role (1438758944322355200)
- Male Unverified Role (1438734829192740955)

The bot cannot manage roles that are higher than its own highest role.

### 6. Running the Bot

```bash
python bot.py
```

On first run, the bot will:
- Connect to Discord
- Sync slash commands globally across all servers
- Log the commands that were synced
- Be ready to receive commands in all servers

## Configuration

### Role IDs

The role IDs are hardcoded in `src/config.py` and can be modified there:

```python
# Role IDs for verifiers (users who can run the commands)
FEMALE_VERIFIER_ROLE_ID: int = 1438678339786244096
MALE_VERIFIER_ROLE_ID: int = 1438678549358706781

# Role IDs to assign to verified users
FEMALE_ROLE_ID: int = 1438734916929196054
MALE_ROLE_ID: int = 1438734872670769323

# Role IDs to remove when verified
FEMALE_REMOVE_ROLE_ID: int = 1438758944322355200
MALE_REMOVE_ROLE_ID: int = 1438734829192740955
```

### Economy Settings

Economy settings are configured in `src/data/economy/settings.json`:
- Daily base reward and streak bonuses
- Transfer limits
- Game reward multipliers
- Weekly bonus amounts

### Environment Variables

- `DISCORD_TOKEN`: Your bot token from Discord Developer Portal

## Troubleshooting

### Commands Not Appearing
- Ensure the bot has the `applications.commands` scope when invited
- Global command sync can take up to 1 hour to propagate across all servers
- Restart the bot to force command sync

### Permission Errors
- Verify the bot has "Manage Roles" permission in the server
- Ensure the bot's role is above all roles it needs to manage in each server
- Check that the role IDs in config.py match actual roles in your server

### Role Assignment Fails
- The bot's highest role must be above the target roles in each server
- Target user must not be a bot
- Target user must not already have the role

### Data Issues
- User data is stored in JSON files in the `src/data/` directory
- Ensure the bot has write permissions to these directories
- Data is organized by user ID and guild ID for multi-server support

## Development

The bot uses a modular Cog-based architecture:
- `bot.py`: Main entry point, handles startup and global command syncing
- `src/cogs/`: Contains all command modules organized by functionality
- `src/utils/`: Reusable utility functions and classes
- `src/data/`: JSON-based data storage with organized directory structure
- `src/config.py`: Centralized configuration management
- `src/logging_setup.py`: Structured logging configuration

### Adding New Features
1. Create a new Cog in `src/cogs/`
2. Add utility functions in `src/utils/` if needed
3. Update data structure in `src/data/` if required
4. Load the Cog in `bot.py` setup_hook method
5. Update README.md with new commands and features

## License

This project is provided as-is for educational and production use.