# file: bot.py

"""
NBABot v11 — Main Discord Bot
NBA Analytics Discord Bot — Rule-Based Parlay Generator
"""

import asyncio
import os
import logging

os.environ["NBABOT_VERSION"] = "11"

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from confidence_engine import (
    calculate_confidence,
    HitRateData,
    ContextData,
    CONFIDENCE_MAX,
)

from embeds import (
    build_potd_embed_v11,
    build_edge_finder_embed_v11,
    build_parlay_embed,
)

from buttons import ParlayView
from parlay_engine import parlay_engine, Parlay, generate_parlay_id
from startup_checks import verify_v11
from startup_checks_player_status import verify_player_status_engine

# ----------------- SETUP -----------------

logging.basicConfig(level=logging.INFO)

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing")

POTD_CONFIDENCE_MIN = 70
DEFAULT_MIN_CONFIDENCE = 60

# ================= COG ==================

class ParlayCog(commands.Cog):
    """All parlay-related commands (v11)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------- PICK OF THE DAY ----------

    @app_commands.command(
        name="pickoftheday",
        description="Get today's highest confidence picks ranked",
    )
    async def pickoftheday(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            games = await parlay_engine.api.get_games_today()
            if not games:
                await interaction.followup.send("❌ No NBA games today.", ephemeral=True)
                return

            all_picks = []

            for game in games:
                legs = await parlay_engine._generate_legs_for_game(game, ladder=5)
                for leg in legs:
                    if not leg.eligible:
                        continue

                    hit_rate = HitRateData(
                        hits_l5=leg.hit_rate.hits_l5,
                        games_l5=leg.hit_rate.games_l5,
                        hits_l10=leg.hit_rate.hits_l10,
                        games_l10=leg.hit_rate.games_l10,
                        hits_l15=leg.hit_rate.hits_l15,
                        games_l15=leg.hit_rate.games_l15,
                    )

                    context = ContextData(
                        minutes_stable=leg.minutes_projection.stable,
                        is_home=leg.is_home,
                    )

                    confidence = calculate_confidence(hit_rate, context)

                    if confidence.score >= POTD_CONFIDENCE_MIN:
                        all_picks.append(
                            {"leg": leg, "confidence": confidence.score}
                        )

            if not all_picks:
                await interaction.followup.send("❌ No eligible picks today.", ephemeral=True)
                return

            all_picks.sort(key=lambda x: x["confidence"], reverse=True)
            embed = build_potd_embed_v11(all_picks[:5])
            await interaction.followup.send(embed=embed)

        except Exception:
            logging.exception("Pick of the Day failed")
            await interaction.followup.send(
                "❌ Unexpected error. Please try again later.",
                ephemeral=True,
            )

    # ---------- PARLAY CONFIDENCE ----------

    @app_commands.command(
        name="parlay-confidence",
        description="Generate parlay with v11 confidence scoring",
    )
    async def parlay_confidence(
        self,
        interaction: discord.Interaction,
        legs: int = 4,
        wager: float = 10.0,
        ladder: int = 5,
        min_confidence: int = DEFAULT_MIN_CONFIDENCE,
    ):
        await interaction.response.defer()
        try:
            games = await parlay_engine.api.get_games_today()
            if not games:
                await interaction.followup.send("❌ No NBA games today.", ephemeral=True)
                return

            eligible_legs = []

            for game in games:
                game_legs = await parlay_engine._generate_legs_for_game(game, ladder)
                for leg in game_legs:
                    if not leg.eligible:
                        continue

                    hit_rate = HitRateData(
                        hits_l5=leg.hit_rate.hits_l5,
                        games_l5=leg.hit_rate.games_l5,
                        hits_l10=leg.hit_rate.hits_l10,
                        games_l10=leg.hit_rate.games_l10,
                        hits_l15=leg.hit_rate.hits_l15,
                        games_l15=leg.hit_rate.games_l15,
                    )

                    context = ContextData(
                        minutes_stable=leg.minutes_projection.stable,
                        is_home=leg.is_home,
                    )

                    confidence = calculate_confidence(hit_rate, context)

                    if confidence.score >= min_confidence:
                        leg.confidence = confidence
                        eligible_legs.append(leg)

            if len(eligible_legs) < legs:
                await interaction.followup.send(
                    f"❌ Only {len(eligible_legs)} legs meet criteria.",
                    ephemeral=True,
                )
                return

            eligible_legs.sort(
                key=lambda l: l.confidence.score, reverse=True
            )
            selected = parlay_engine._select_varied_legs(
                eligible_legs, legs
            )

            total_decimal = 1.0
            for leg in selected:
                total_decimal *= leg.odds.decimal

            parlay = Parlay(
                id=generate_parlay_id(),
                legs=selected,
                leg_count=len(selected),
                wager=wager,
                ladder=ladder,
                total_odds=parlay_engine._decimal_to_american(total_decimal),
                total_odds_decimal=round(total_decimal, 2),
                potential_win=round(wager * total_decimal, 2),
                created_at=None,
                user_id=str(interaction.user.id),
                guild_id=str(interaction.guild_id),
                channel_id=str(interaction.channel_id),
            )

            parlay_engine._parlay_cache[parlay.id] = parlay
            for leg in selected:
                parlay_engine._leg_cache[leg.id] = leg

            embed = build_parlay_embed(parlay)
            avg_conf = sum(l.confidence.score for l in selected) / len(selected)
            embed.set_footer(
                text=f"Avg Confidence: {avg_conf:.0f}/{CONFIDENCE_MAX} | ⚠️ Educational Only"
            )

            await interaction.followup.send(
                embed=embed,
                view=ParlayView(parlay),
            )

        except Exception:
            logging.exception("Parlay confidence failed")
            await interaction.followup.send(
                "❌ Unexpected error. Please try again later.",
                ephemeral=True,
            )

    # ---------- EDGE FINDER ----------

    @app_commands.command(
        name="edge-finder",
        description="Find best +odds value plays",
    )
    async def edge_finder(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            games = await parlay_engine.api.get_games_today()
            picks = []

            for game in games:
                legs = await parlay_engine._generate_legs_for_game(game, ladder=5)
                for leg in legs:
                    if leg.odds.american <= 0:
                        continue

                    hit_rate = HitRateData(
                        hits_l5=leg.hit_rate.hits_l5,
                        games_l5=leg.hit_rate.games_l5,
                        hits_l10=leg.hit_rate.hits_l10,
                        games_l10=leg.hit_rate.games_l10,
                        hits_l15=leg.hit_rate.hits_l15,
                        games_l15=leg.hit_rate.games_l15,
                    )

                    context = ContextData(
                        minutes_stable=leg.minutes_projection.stable,
                        is_home=leg.is_home,
                    )

                    confidence = calculate_confidence(hit_rate, context)

                    if confidence.score >= DEFAULT_MIN_CONFIDENCE:
                        picks.append(
                            {"leg": leg, "confidence": confidence.score}
                        )

            if not picks:
                await interaction.followup.send("❌ No +odds edges today.", ephemeral=True)
                return

            picks.sort(key=lambda x: x["confidence"], reverse=True)
            embed = build_edge_finder_embed_v11(picks[:5])
            await interaction.followup.send(embed=embed)

        except Exception:
            logging.exception("Edge finder failed")
            await interaction.followup.send(
                "❌ Unexpected error. Please try again later.",
                ephemeral=True,
            )


# ================= BOT ==================

class NBABot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.default(),
        )

    async def setup_hook(self):
        await self.add_cog(ParlayCog(self))
        await self.tree.sync()


# ================= ENTRY ==================

async def main():
    verify_v11()
    verify_player_status_engine()
    bot = NBABot()
    await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
