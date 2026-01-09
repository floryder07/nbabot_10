# file: config.py

"""
NBABot v11.0.0 Configuration
Unified + Locked v11 Systems
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# BOT METADATA (SINGLE SOURCE OF TRUTH)
# ============================================

BOT_NAME = "NBABot"
BOT_VERSION = "11.0.0"
BOT_COLOR = 0x1D428A  # NBA Blue

# ============================================
# DISCORD CONFIGURATION
# ============================================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("DISCORD_GUILD_ID")
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
BOT_USER_ID = os.getenv("DISCORD_BOT_USER_ID")

# ============================================
# CONFIDENCE SYSTEM (v11 — LOCKED)
# ============================================

CONFIDENCE_MAX = 95
CONFIDENCE_MIN = 0

CONFIDENCE_TIERS = {
    "safe": {"min": 80, "max": 95, "emoji": "🛡️", "label": "Safe"},
    "normal": {"min": 60, "max": 79, "emoji": "⚖️", "label": "Normal"},
    "moonshot": {"min": 40, "max": 59, "emoji": "🚀", "label": "Moonshot"},
    "high_risk": {"min": 0, "max": 39, "emoji": "⚠️", "label": "High Risk"},
}

CONFIDENCE_BASE_SCORES = {
    (5, 5): 70,
    (4, 5): 62,
    (8, 10): 65,
    (7, 10): 58,
    (13, 15): 68,
    (12, 15): 60,
    (11, 15): 56,
    (10, 15): 52,
}

CONFIDENCE_POSITIVE_MODIFIERS = {
    "alt_line_consistency": 5,
    "minutes_stable": 5,
    "role_clarity": 4,
    "favorable_matchup": 4,
    "h2h_alignment": 3,
    "home_advantage": 2,
}

CONFIDENCE_NEGATIVE_MODIFIERS = {
    "questionable_doubtful": -6,
    "one_low_minute_game": -7,
    "two_low_minute_games": -12,
    "role_shift_conflict": -6,
    "key_teammate_missing": -5,
    "road_disadvantage": -2,
}

# ============================================
# PLAYER PROP SYSTEM (v11 — LOCKED)
# ============================================

PLAYER_PROP_MARKETS = [
    "points",
    "rebounds",
    "assists",
    "pra",
    "points_rebounds",
    "points_assists",
    "rebounds_assists",
    "steals",
    "blocks",
    "threes",
    "double_double",
    "triple_double",
    "first_quarter_points",
    "first_half_points",
]

PLAYER_PROP_THRESHOLDS = {
    5: {"min_hits": 4, "min_pct": 0.80},
    10: {"min_hits": 7, "min_pct": 0.70},
    15: {"min_hits": 10, "min_pct": 0.67},
}

ALT_LINE_THRESHOLDS = {
    "l5_min": 0.60,
    "l10_min": 0.65,
    "l15_min": 0.65,
}

ODDS_CONSTRAINT_MIN = -250
ODDS_CONSTRAINT_MAX = 180

# ============================================
# MINUTES & STATUS SYSTEM (v11 — LOCKED)
# ============================================

LOW_MINUTES_THRESHOLD = 0.75
EXCLUDE_LOW_MINUTE_STREAK = 3

STATUS_ELIGIBILITY = {
    "active": True,
    "probable": True,
    "questionable": True,
    "doubtful": False,
    "out": False,
    "suspended": False,
}

# ============================================
# CAUTION SYSTEM (v11 — LOCKED)
# ============================================

CAUTION_ICONS = {
    "none": "",
    "mild": "⚠️",
    "high": "⚠️⚠️",
    "excluded": "❌",
}

CAUTION_TRIGGERS = {
    "questionable": {"level": 1, "message": "Listed as Questionable"},
    "doubtful": {"level": 2, "message": "Listed as Doubtful"},
    "minutes_drop": {"level": 1, "message": "Minutes dropped in last game"},
    "minutes_volatility": {"level": 2, "message": "Minutes volatility detected"},
    "role_shift": {"level": 1, "message": "Role shift detected"},
    "teammate_out": {"level": 1, "message": "Key teammate missing"},
    "star_out": {"level": 2, "message": "Star player ruled OUT"},
    "back_to_back": {"level": 1, "message": "Back-to-back game"},
    "blowout_risk": {"level": 1, "message": "Blowout risk"},
    "large_spread": {"level": 1, "message": "Large spread"},
    "road_game": {"level": 1, "message": "Road disadvantage"},
}

# ============================================
# DISPLAY SETTINGS (v11)
# ============================================

LEG_TYPE_EMOJIS = {
    "player_prop": "👤",
    "moneyline": "🏆",
    "spread": "📈",
    "game_total": "📊",
    "team_total": "📊",
}

CONFIDENCE_DISPLAY_FORMAT = "{score} / {max} ({emoji} {label})"
EMBED_SEPARATOR = "━━━━━━━━━━━━━━━━━━━━━━"
EMBED_FOOTER = f"{BOT_NAME} v{BOT_VERSION} | Educational Analytics Only"
DISCLAIMER = "⚠️ Educational analytics only. No betting advice."

# ============================================
# COMMAND SETTINGS (v11)
# ============================================

POTD_MAX_PICKS = 5
POTD_MIN_CONFIDENCE = 70

EDGE_FINDER_MIN_ODDS = 100
EDGE_FINDER_MIN_CONFIDENCE = 60

# ============================================
# DATA SOURCES
# ============================================

API_BASKETBALL_KEY = os.getenv("API_BASKETBALL_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

STATMUSE_ENABLED = os.getenv("STATMUSE_ENABLED", "false").lower() == "true"
NBA_API_ENABLED = os.getenv("NBA_API_ENABLED", "true").lower() == "true"

# ============================================
# RUNTIME
# ============================================

MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ============================================
# VALIDATION
# ============================================

def validate_config() -> dict:
    status = {"valid": True, "errors": [], "warnings": []}

    if not DISCORD_TOKEN:
        status["valid"] = False
        status["errors"].append("DISCORD_TOKEN is missing")

    if not API_BASKETBALL_KEY and not MOCK_MODE:
        status["warnings"].append("API_BASKETBALL_KEY missing (enable MOCK_MODE)")

    if not ODDS_API_KEY:
        status["warnings"].append("ODDS_API_KEY missing (odds limited)")

    return status
