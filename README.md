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

### Spiritual Commands

#### `/prayertimes`
- **Description**: Get prayer times for a specific city
- **Options**: City, Country (optional)

#### `/qibla`
- **Description**: Get Qibla direction for a city
- **Options**: City

#### `/zakat`
- **Description**: Calculate Zakat (2.5%) on your assets
- **Options**: Cash, Gold, Silver, Other savings

#### `/set_daily_channel`
- **Description**: Set the channel for daily Islamic content (Verse/Hadith of the Day)
- **Permissions**: Administrator only
- **Options**: Channel

#### `/trigger_daily`
- **Description**: Manually trigger the daily content delivery (Admin only)

### Economy Commands

#### `/balance`
- **Description**: Check your Ilm Coins and Good Deed Points balance
- **Options**: User (moderators can check other users)

#### `/daily`
- **Description**: Claim your daily Ilm Coins reward with streak bonuses

#### `/work`
- **Description**: Earn Ilm Coins by performing Halal jobs (Calligrapher, Scholar, etc.)
- **Cooldown**: 1 hour

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

#### `/guess_reciter`
- **Description**: Listen to a clip and guess the Quran reciter
- **Rewards**: Earn Ilm Coins for correct guesses

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
├── Dockerfile            # Docker container configuration
├── docker-compose.yml    # Docker Compose for easy deployment
├── .dockerignore         # Docker ignore patterns
└── src/
    ├── __init__.py
    ├── config.py         # Configuration and environment variables
    ├── database.py       # PostgreSQL database connection and management
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
    │   ├── spiritual.py  # Spiritual utilities Cog
    │   └── help.py       # Help system Cog
    └── utils/
        ├── __init__.py
        ├── checks.py     # Permission checks and validations
        ├── economy_utils.py # Economy system utilities
        └── game_utils.py    # Game system utilities
```

## Economy System

### Currency Types
- **Ilm Coins (IC)**: Main currency earned through games, jobs, daily rewards, and activities
- **Good Deed Points (GDP)**: Prestige currency earned through donations and charitable acts

### Features
- Daily rewards with streak bonuses
- **Halal Jobs**: Earn coins through roleplay jobs like Scholar or Merchant
- Coin transfers between users
- Charitable donations with GDP rewards
- Server leaderboards
- Halal-compliant mechanics only

## Spiritual Utilities
- **Prayer Times**: Accurate timings for any city via Aladhan API
- **Qibla Finder**: Direction calculation for prayer
- **Zakat Calculator**: Easy asset-based calculation
- **Daily Content**: Automatic postings of Verses and Hadiths

## Game System

### Available Games
1. **Guess the Reciter**: Audio-based challenge to identify Quran reciters
2. **Islamic Knowledge Quiz**: Multiple-choice questions on various Islamic topics
3. **Quran Verse Match**: Match Quran verses to correct surah names
4. **Hadith Trivia**: Interactive Hadith learning games

## Shop System

### Item Categories
- **Knowledge**: Educational items like books and courses
- **Cosmetic**: Visual items for profile customization
- **Practical**: Useful items like prayer mats
- **Prestige**: Achievement and recognition items
- **Utility**: Boosts and temporary benefits

### Shop Features
- Halal-compliant items only
- Inventory management (Database backed)
- Item effects and benefits
- Category filtering

## Profile System

### Features
- User statistics tracking (Games played, Quizzes completed)
- Achievement system with database tracking
- Progress tracking
- Level system based on total earnings
- Server leaderboards
- Achievement rewards

## Setup Instructions

### 1. Prerequisites

- Python 3.10 or higher
- PostgreSQL Database
- Discord Bot Token

### 2. Discord Developer Portal Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a New Application
3. Go to the "Bot" section
4. Create a bot and copy the token
5. Enable these privileged gateway intents:
   - **SERVER MEMBERS INTENT** (required for role management)
   - **MESSAGE CONTENT INTENT** (recommended)

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
   DISCORD_TOKEN=your_token_here
   DATABASE_URL=postgresql://user:password@host:port/dbname
   ```

### 5. Role Setup

**Critical**: In each server where you want to use the bot, ensure the bot's role is ABOVE all roles it needs to manage.

### 6. Running the Bot

```bash
python bot.py
```

On first run, the bot will:
- Connect to Discord
- Connect to the PostgreSQL database (creating tables if they don't exist)
- Sync slash commands globally across all servers
- Be ready to receive commands in all servers

## Database
The bot now uses **PostgreSQL** for all data storage (Users, Economy, Inventory, Achievements).
Ensure you have a running PostgreSQL instance and provide the connection string in `DATABASE_URL`.

## Troubleshooting

### Database Connection Fails
- Check `DATABASE_URL` in `.env`
- Ensure the database server is running and accessible
- Check for firewall or network issues

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