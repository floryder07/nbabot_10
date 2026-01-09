"""
NBABot v10.0 Configuration
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Discord Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

# API Configuration
API_BASKETBALL_KEY = os.getenv("API_BASKETBALL_KEY")
API_BASKETBALL_BASE_URL = "https://v1.basketball.api-sports.io"

# Bot Settings
BOT_NAME = "NBABot"
BOT_VERSION = "10.0"
BOT_COLOR = 0x1D428A  # NBA Blue

# Eligibility Thresholds
# Format: {ladder: minimum_hits_required}
ELIGIBILITY_THRESHOLDS = {
    5: 3,   # Need 3+ out of 5
    10: 7,  # Need 7+ out of 10
    15: 10  # Need 10+ out of 15
}

# Ladder Options
VALID_LADDERS = [5, 10, 15]
DEFAULT_LADDER = 5

# Parlay Limits
MIN_LEGS = 2
MAX_LEGS = 10
MIN_WAGER = 1
MAX_WAGER = 10000

# H2H Settings
H2H_WINDOW_YEARS = 1

# Prop Types Supported
PROP_TYPES = [
    "points",
    "rebounds", 
    "assists",
    "threes",
    "steals",
    "blocks",
    "pts_reb_ast"
]

# Leg Types
LEG_TYPES = [
    "player_prop",
    "moneyline",
    "spread",
    "game_total",
    "team_total"
]

# Display Settings
EMBED_FOOTER = f"{BOT_NAME} v{BOT_VERSION} | Educational Analytics Only"
DISCLAIMER = "⚠️ Educational analytics only. No betting advice."

# API Rate Limiting
API_RATE_LIMIT_PER_MINUTE = 30
API_CACHE_TTL_SECONDS = 300  # 5 minutes

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Mock Mode (for testing without API)
# Set to True to use mock data instead of real API calls
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"
