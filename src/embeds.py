"""
NBABot v10.0 Discord Embeds (FIXED)

Handles all Discord embed formatting with proper odds display.
"""

import discord
from typing import List, Optional
from config import BOT_COLOR, BOT_NAME, BOT_VERSION, EMBED_FOOTER, DISCLAIMER
from eligibility import get_rules_summary, ELIGIBILITY_RULES


def format_american_odds(odds: int) -> str:
    """Format American odds with + for positive."""
    if odds > 0:
        return f"+{odds}"
    return str(odds)


def calculate_implied_probability(american_odds: int) -> float:
    """Calculate implied probability from American odds."""
    if american_odds > 0:
        return 100 / (american_odds + 100) * 100
    else:
        return abs(american_odds) / (abs(american_odds) + 100) * 100


def build_parlay_embed(parlay) -> discord.Embed:
    """
    Build the main parlay embed with improved layout.
    """
    # Format total odds
    total_odds_str = format_american_odds(parlay.total_odds)
    
    # Header
    embed = discord.Embed(
        title=f"🏀 PARLAY — {parlay.leg_count} LEGS",
        color=BOT_COLOR
    )
    
    # Summary section
    embed.description = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 **TOTAL ODDS (American):** `{total_odds_str}`\n"
        f"💵 **WAGER:** ${parlay.wager:.2f} → **POTENTIAL WIN:** ${parlay.potential_win:.2f}\n"
        f"📊 **SAMPLE WINDOW:** Last {parlay.ladder} games\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    # Add each leg
    for i, leg in enumerate(parlay.legs, 1):
        leg_content = format_leg_field(leg, i)
        embed.add_field(
            name=leg_content["name"],
            value=leg_content["value"],
            inline=False
        )
    
    # Footer with disclaimer
    embed.set_footer(text=f"⚠️ EDUCATIONAL USE ONLY — NOT BETTING ADVICE | {BOT_NAME} v{BOT_VERSION}")
    
    return embed


def format_leg_field(leg, leg_number: int) -> dict:
    """
    Format a single leg for embed field with proper odds display.
    """
    # Type emoji mapping
    type_emojis = {
        "player_prop": "👤",
        "moneyline": "🏀",
        "spread": "📉",
        "game_total": "📊",
        "team_total": "📈"
    }
    
    emoji = type_emojis.get(leg.type, "🎯")
    type_name = leg.type.replace("_", " ").title()
    
    # Format odds properly
    odds_american = format_american_odds(leg.odds.american)
    implied_prob = calculate_implied_probability(leg.odds.american)
    
    # Build name
    name = f"{emoji} LEG {leg_number} — {type_name}"
    
    # Build value with proper formatting
    lines = [
        f"**MATCHUP:** {leg.matchup.away_team} @ {leg.matchup.home_team}",
        f"**PICK:** {leg.selection.label}",
        f"**HIT RATE:** {leg.hit_rate.hits} / {leg.hit_rate.games} games ({leg.hit_rate.percentage:.0f}%)",
    ]
    
    # Add H2H for moneyline
    if leg.type == "moneyline" and leg.h2h and leg.h2h.games > 0:
        lines.append(f"**H2H (1 Year):** {leg.h2h.wins} / {leg.h2h.games} wins")
    
    # Add spread data
    if leg.type == "spread" and leg.spread_data:
        lines.append(f"**AVG MARGIN:** {leg.spread_data.avg_margin:+.1f} pts")
    
    # Add odds with implied probability
    lines.append(f"**ODDS:** `{odds_american}` (Implied: {implied_prob:.1f}%)")
    
    return {
        "name": name,
        "value": "\n".join(lines)
    }


def build_insights_embed(leg) -> discord.Embed:
    """
    Build INSIGHTS embed for a specific leg.
    INSIGHTS = Numerical data, statistics, risk analysis.
    """
    odds_str = format_american_odds(leg.odds.american)
    implied_prob = calculate_implied_probability(leg.odds.american)
    
    embed = discord.Embed(
        title=f"📊 INSIGHTS — {leg.selection.label[:50]}",
        color=BOT_COLOR
    )
    
    # Statistical breakdown
    stats_lines = [
        "**📈 Performance Data**",
        f"• Hit Rate: **{leg.hit_rate.hits} / {leg.hit_rate.games}** ({leg.hit_rate.percentage:.1f}%)",
        f"• Sample Size: **{leg.hit_rate.games} games**",
        f"• Ladder Used: **{leg.hit_rate.ladder}-game window**",
        "",
        "**💰 Odds Analysis**",
        f"• American Odds: **{odds_str}**",
        f"• Decimal Odds: **{leg.odds.decimal:.2f}**",
        f"• Implied Probability: **{implied_prob:.1f}%**",
    ]
    
    # Type-specific insights
    if leg.type == "moneyline" and leg.h2h and leg.h2h.games > 0:
        h2h_pct = (leg.h2h.wins / leg.h2h.games * 100) if leg.h2h.games > 0 else 0
        stats_lines.extend([
            "",
            "**🤝 Head-to-Head (1 Year)**",
            f"• Record: **{leg.h2h.wins} / {leg.h2h.games}** ({h2h_pct:.0f}%)",
        ])
    
    elif leg.type == "spread" and leg.spread_data:
        stats_lines.extend([
            "",
            "**📉 Spread Data**",
            f"• Spread Line: **{leg.spread_data.spread_value:+.1f}**",
            f"• Avg Margin: **{leg.spread_data.avg_margin:+.1f} pts**",
            f"• Cover Rate: **{leg.spread_data.cover_rate['covers']} / {leg.spread_data.cover_rate['games']}**",
        ])
    
    elif leg.type == "player_prop":
        stats_lines.extend([
            "",
            "**👤 Player Prop Info**",
            f"• Prop Type: **{leg.selection.prop_type.title() if leg.selection.prop_type else 'N/A'}**",
            f"• Line: **{leg.selection.value}**",
        ])
    
    elif "total" in leg.type:
        stats_lines.extend([
            "",
            "**📊 Total Info**",
            f"• Direction: **{leg.selection.direction.title() if leg.selection.direction else 'N/A'}**",
            f"• Line: **{leg.selection.value}**",
        ])
    
    # Risk assessment
    if leg.hit_rate.percentage >= 80:
        risk_level = "🟢 LOW RISK"
    elif leg.hit_rate.percentage >= 60:
        risk_level = "🟡 MODERATE RISK"
    else:
        risk_level = "🔴 HIGHER RISK"
    
    stats_lines.extend([
        "",
        f"**⚠️ Risk Level:** {risk_level}",
    ])
    
    embed.description = "\n".join(stats_lines)
    embed.set_footer(text=f"{BOT_NAME} v{BOT_VERSION} | Data Analysis")
    
    return embed


def build_explain_embed(leg) -> discord.Embed:
    """
    Build EXPLAIN embed for why a leg was included.
    EXPLAIN = Human reasoning, educational content.
    """
    threshold = ELIGIBILITY_RULES[leg.hit_rate.ladder]["threshold"]
    
    embed = discord.Embed(
        title=f"📖 WHY THIS PICK — {leg.selection.label[:50]}",
        color=BOT_COLOR
    )
    
    # Main reasoning
    reasons = [
        "**✅ Eligibility Criteria Met**",
        f"• Hit rate of **{leg.hit_rate.hits}/{leg.hit_rate.games}** meets the minimum threshold of **{threshold}/{leg.hit_rate.ladder}**",
        f"• This means the pick has hit in **{leg.hit_rate.percentage:.0f}%** of recent games",
        "",
        "**📊 Selection Methodology**",
    ]
    
    # Type-specific reasoning
    if leg.type == "player_prop":
        reasons.extend([
            f"• Player props are based on individual performance over last **{leg.hit_rate.ladder}** games",
            "• Recent form is weighted more heavily than season averages",
            "• ⚠️ Player props can be volatile due to injury, matchups, and game script",
        ])
    
    elif leg.type == "moneyline":
        reasons.extend([
            f"• Team has won **{leg.hit_rate.hits}** of their last **{leg.hit_rate.games}** games",
        ])
        if leg.h2h and leg.h2h.games > 0:
            reasons.append(f"• H2H record (**{leg.h2h.wins}/{leg.h2h.games}**) used as supporting data only")
            reasons.append("• ℹ️ H2H does NOT affect eligibility — only recent form does")
    
    elif leg.type == "spread":
        reasons.extend([
            f"• Team has covered this spread in **{leg.hit_rate.hits}** of last **{leg.hit_rate.games}** games",
            f"• Average margin of victory: **{leg.spread_data.avg_margin:+.1f}** points" if leg.spread_data else "",
            "• Spread bets account for point differential, not just wins",
        ])
    
    elif "total" in leg.type:
        direction = leg.selection.direction or "over/under"
        reasons.extend([
            f"• The **{direction}** has hit in **{leg.hit_rate.hits}** of last **{leg.hit_rate.games}** games",
            "• Totals are affected by pace, defense, and game script",
            "• ⚠️ Weather and injuries can significantly impact totals",
        ])
    
    # What would cause exclusion
    reasons.extend([
        "",
        "**❌ Would Be Excluded If:**",
        f"• Hit rate below **{threshold}/{leg.hit_rate.ladder}** ({(threshold/leg.hit_rate.ladder)*100:.0f}%)",
        "• Missing or incomplete data",
        "• Game postponed or cancelled",
    ])
    
    embed.description = "\n".join(reasons)
    embed.set_footer(text=f"{BOT_NAME} v{BOT_VERSION} | Educational Only")
    
    return embed


def build_help_embed() -> discord.Embed:
    """Build help embed showing command usage."""
    embed = discord.Embed(
        title=f"🏀 {BOT_NAME} v{BOT_VERSION} — Help",
        description="Generate rule-based NBA parlays using historical hit-rate data.",
        color=BOT_COLOR
    )
    
    # Main command
    embed.add_field(
        name="📌 Main Command",
        value=(
            "```\n"
            "/parlay legs:<2-10> wager:<amount> ladder:<5|10|15>\n"
            "```\n"
            "**Parameters:**\n"
            "• `legs` — Number of legs (2-10)\n"
            "• `wager` — Wager amount in USD\n"
            "• `ladder` — Game window (5, 10, or 15 games)"
        ),
        inline=False
    )
    
    # Examples
    embed.add_field(
        name="💡 Examples",
        value=(
            "`/parlay legs:4 wager:10` — 4-leg parlay, $10, 5-game ladder\n"
            "`/parlay legs:3 wager:25 ladder:10` — 3-leg, $25, 10-game ladder"
        ),
        inline=False
    )
    
    # Buttons
    embed.add_field(
        name="🔘 Interactive Buttons",
        value=(
            "• **📊 Insights** — Statistical analysis & risk assessment\n"
            "• **📖 Explain** — Why each pick was included\n"
            "• **🔄 Refresh** — Generate new parlay (same settings)"
        ),
        inline=False
    )
    
    embed.set_footer(text=f"⚠️ {DISCLAIMER}")
    
    return embed


def build_rules_embed() -> discord.Embed:
    """Build embed showing eligibility rules."""
    embed = discord.Embed(
        title="📊 Eligibility Rules",
        description="Legs must meet these thresholds to be included.",
        color=BOT_COLOR
    )
    
    for ladder, rules in ELIGIBILITY_RULES.items():
        embed.add_field(
            name=f"🎯 {ladder}-Game Ladder",
            value=(
                f"✅ **Allowed:** {rules['allowed']}\n"
                f"❌ **Rejected:** {rules['rejected']}\n"
                f"→ {rules['description']}"
            ),
            inline=False
        )
    
    embed.add_field(
        name="⚠️ Important",
        value=(
            "• Rejected legs are **never shown**\n"
            "• H2H is **supporting data only**\n"
            "• Thresholds are **non-negotiable**"
        ),
        inline=False
    )
    
    embed.set_footer(text=EMBED_FOOTER)
    
    return embed


def build_error_embed(title: str, description: str) -> discord.Embed:
    """Build error embed."""
    embed = discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=discord.Color.red()
    )
    embed.set_footer(text=EMBED_FOOTER)
    return embed


def build_no_games_embed() -> discord.Embed:
    """Build embed for when no games are available."""
    return build_error_embed(
        "No Games Available",
        "There are no NBA games scheduled for today.\n\nTry again on a game day!"
    )


def build_not_enough_legs_embed(requested: int, available: int) -> discord.Embed:
    """Build embed for when not enough eligible legs are available."""
    return build_error_embed(
        "Not Enough Eligible Legs",
        f"You requested **{requested} legs**, but only **{available}** eligible legs available.\n\n"
        "**Try:**\n"
        "• Requesting fewer legs\n"
        "• Using a lower ladder\n"
        "• Waiting for more games"
    )
