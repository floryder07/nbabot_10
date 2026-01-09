"""
NBABot v11 — Discord Embed Formatting
STRICTLY v11. DO NOT IMPORT FROM LEGACY.
"""

import discord
from typing import List, Optional
from config import BOT_COLOR

# ============================================
# CONSTANTS (v11)
# ============================================

EMBED_SEPARATOR = "━━━━━━━━━━━━━━━━━━━━━━"
CONFIDENCE_MAX = 95

TIER_EMOJIS = {
    "safe": "🛡️",
    "normal": "⚖️",
    "moonshot": "🚀",
    "high_risk": "⚠️",
}

LEG_TYPE_EMOJIS_V11 = {
    "player_prop": "👤",
    "moneyline": "🏆",
    "spread": "📈",
    "game_total": "📊",
    "team_total": "📊",
}

# ============================================
# VERSION GUARD (HARD FAIL IF MISUSED)
# ============================================

V11_SIGNATURE = "NBABOT_V11_EMBEDS"

def _assert_v11():
    return V11_SIGNATURE

# ============================================
# HELPERS
# ============================================

def calculate_implied_probability(american_odds: int) -> float:
    if american_odds > 0:
        return 100 / (american_odds + 100) * 100
    return abs(american_odds) / (abs(american_odds) + 100) * 100


def get_tier_from_score(score: int) -> tuple:
    if score >= 80:
        return ("safe", "🛡️", "Safe")
    elif score >= 60:
        return ("normal", "⚖️", "Normal")
    elif score >= 40:
        return ("moonshot", "🚀", "Moonshot")
    return ("high_risk", "⚠️", "High Risk")

# ============================================
# CONFIDENCE FORMATTING
# ============================================

def format_confidence_line(score: int, tier: str, tier_label: str) -> str:
    emoji = TIER_EMOJIS.get(tier, "⚠️")
    return f"💯 CONFIDENCE: {score} / {CONFIDENCE_MAX} ({emoji} {tier_label})"

# ============================================
# CAUTION FORMATTING
# ============================================

def format_caution_section(messages: list, icon: str = "⚠️") -> str:
    if not messages:
        return ""
    lines = [f"{icon} CAUTION:"]
    lines.extend(f"• {msg}" for msg in messages)
    return "\n".join(lines)

def format_caution_flags(messages: list) -> str:
    if not messages:
        return ""
    return "⚠️ CAUTION FLAGS:\n" + "\n".join(f"• {m}" for m in messages)

# ============================================
# EMBEDS (v11)
# ============================================

def build_insights_embed_v11(
    player_name: str,
    stat_type: str,
    line: float,
    direction: str,
    game_log: list,
    minutes_log: list,
    hits_l5: int,
    hits_l10: int,
    hits_l15: int,
    avg_stat: float,
    median_stat: float,
    avg_minutes: float,
    low_minute_games: int,
    h2h_avg: float = None,
    h2h_opponent: str = None,
    caution_messages: list = None
) -> discord.Embed:

    _assert_v11()

    embed = discord.Embed(
        title=f"📊 INSIGHTS — {player_name} {direction.title()} {line} {stat_type.title()}",
        color=BOT_COLOR
    )

    embed.add_field(
        name="🎯 Hit Rate",
        value=f"Last 5: {hits_l5}/5\nLast 10: {hits_l10}/10\nLast 15: {hits_l15}/15",
        inline=True
    )

    embed.add_field(
        name="📊 Stats",
        value=f"Avg: {avg_stat:.1f}\nMedian: {median_stat:.1f}",
        inline=True
    )

    embed.add_field(
        name="⏱️ Minutes",
        value=f"Avg: {avg_minutes:.1f}\nLow-Min Games: {low_minute_games}",
        inline=True
    )

    if caution_messages:
        embed.add_field(
            name="",
            value=format_caution_flags(caution_messages),
            inline=False
        )

    embed.set_footer(text="⚠️ DATA ONLY — NO OPINIONS")

    return embed
