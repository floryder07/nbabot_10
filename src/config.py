"""
NBABot v10.1.0 Configuration

Updated with new data sources: Odds API, StatMuse, NBA API
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# DISCORD CONFIGURATION
# ============================================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("DISCORD_GUILD_ID")
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
BOT_USER_ID = os.getenv("DISCORD_BOT_USER_ID")

# ============================================
# BOT SETTINGS
# ============================================
BOT_NAME = "NBABot"
BOT_VERSION = "10.1.0"
BOT_COLOR = 0x1D428A  # NBA Blue

# ============================================
# PRIMARY DATA SOURCES
# ============================================

# API-Basketball (API-Sports)
API_BASKETBALL_KEY = os.getenv("API_BASKETBALL_KEY")
API_BASKETBALL_BASE_URL = "https://v1.basketball.api-sports.io"

# The Odds API
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4"
ODDS_API_SPORT = "basketball_nba"
ODDS_API_REGIONS = "us"  # us, uk, eu, au
ODDS_API_MARKETS = "h2h,spreads,totals,player_points,player_rebounds,player_assists"

# ============================================
# SECONDARY DATA SOURCES
# ============================================

# StatMuse (web-based, no official API)
STATMUSE_ENABLED = os.getenv("STATMUSE_ENABLED", "false").lower() == "true"
STATMUSE_BASE_URL = "https://www.statmuse.com/nba"

# NBA Official API
NBA_API_ENABLED = os.getenv("NBA_API_ENABLED", "true").lower() == "true"
NBA_API_BASE_URL = "https://stats.nba.com/stats"

# ============================================
# DATA SOURCE PRIORITY (Fallback Order)
# ============================================
# 1 = highest priority, used first
DATA_SOURCE_PRIORITY = {
    "odds_api": 1,        # Best for lines/odds
    "api_basketball": 2,  # Best for stats/games
    "nba_api": 3,         # Reference data
    "statmuse": 4,        # Validation
    "derived": 5          # Fallback calculations
}

# ============================================
# ELIGIBILITY THRESHOLDS
# ============================================
ELIGIBILITY_THRESHOLDS = {
    5: 3,   # Need 3+ out of 5
    10: 7,  # Need 7+ out of 10
    15: 10  # Need 10+ out of 15
}

VALID_LADDERS = [5, 10, 15]
DEFAULT_LADDER = 5

# ============================================
# PARLAY SETTINGS
# ============================================
MIN_LEGS = 2
MAX_LEGS = 10
MIN_WAGER = 1
MAX_WAGER = 10000

# ============================================
# PROJECTION SETTINGS (v10.1.0)
# ============================================
# Minimum hit rates for recommendation
MIN_HIT_RATE_L5 = 0.80   # 4/5 (80%)
MIN_HIT_RATE_L10 = 0.70  # 7/10 (70%)
MIN_HIT_RATE_L15 = 0.67  # 10/15 (67%)

# Confidence thresholds
HIGH_CONFIDENCE = 80
MEDIUM_CONFIDENCE = 60
LOW_CONFIDENCE = 40

# ============================================
# PROP TYPES
# ============================================
PROP_TYPES = [
    "points",
    "rebounds", 
    "assists",
    "threes",
    "steals",
    "blocks",
    "pts_reb_ast"
]

# ============================================
# LEG TYPES
# ============================================
LEG_TYPES = [
    "player_prop",
    "moneyline",
    "spread",
    "game_total",
    "team_total"
]

# ============================================
# H2H SETTINGS
# ============================================
H2H_WINDOW_YEARS = 1

# ============================================
# DISPLAY SETTINGS
# ============================================
EMBED_FOOTER = f"{BOT_NAME} v{BOT_VERSION} | Educational Analytics Only"
DISCLAIMER = "⚠️ Educational analytics only. No betting advice."

# ============================================
# RATE LIMITING
# ============================================
API_BASKETBALL_RATE_LIMIT = int(os.getenv("API_BASKETBALL_RATE_LIMIT", "10"))
ODDS_API_RATE_LIMIT = int(os.getenv("ODDS_API_RATE_LIMIT", "500"))
API_CACHE_TTL_SECONDS = 300  # 5 minutes

# ============================================
# RUNTIME
# ============================================
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


# ============================================
# HELPER FUNCTIONS
# ============================================

def is_production() -> bool:
    """Check if running in production."""
    return ENVIRONMENT == "production"


def get_active_data_sources() -> list:
    """Get list of active/configured data sources."""
    sources = []
    
    if API_BASKETBALL_KEY:
        sources.append("api_basketball")
    
    if ODDS_API_KEY:
        sources.append("odds_api")
    
    if NBA_API_ENABLED:
        sources.append("nba_api")
    
    if STATMUSE_ENABLED:
        sources.append("statmuse")
    
    if MOCK_MODE:
        sources.append("mock")
    
    return sources


def validate_config() -> dict:
    """Validate configuration and return status."""
    status = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Required
    if not DISCORD_TOKEN:
        status["valid"] = False
        status["errors"].append("DISCORD_TOKEN is missing")
    
    # Recommended
    if not API_BASKETBALL_KEY and not MOCK_MODE:
        status["warnings"].append("API_BASKETBALL_KEY missing - enable MOCK_MODE for testing")
    
    if not ODDS_API_KEY:
        status["warnings"].append("ODDS_API_KEY missing - alt lines won't be available")
    
    return status
