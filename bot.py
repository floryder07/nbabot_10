"""
NBABot v10.0 — Main Discord Bot

NBA Analytics Discord Bot — Rule-Based Parlay Generator
"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import logging
from typing import Optional

from config import (
    DISCORD_TOKEN, GUILD_ID, BOT_NAME, BOT_VERSION,
    MIN_LEGS, MAX_LEGS, MIN_WAGER, MAX_WAGER,
    DEFAULT_LADDER, VALID_LADDERS
)
from parlay_engine import parlay_engine
from embeds import (
    build_parlay_embed, build_help_embed, build_rules_embed,
    build_error_embed, build_no_games_embed, build_not_enough_legs_embed
)
from buttons import ParlayView
from api_client import api_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(BOT_NAME)


class NBABot(commands.Bot):
    """
    Main Discord bot class.
    """
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            description=f"{BOT_NAME} v{BOT_VERSION} — NBA Analytics Bot"
        )
    
    async def setup_hook(self):
        """Called when the bot is ready to set up commands."""
        # Add cog with commands
        await self.add_cog(ParlayCog(self))
        
        # Sync commands
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info(f"Synced commands to guild {GUILD_ID}")
        else:
            await self.tree.sync()
            logger.info("Synced commands globally")
    
    async def on_ready(self):
        """Called when the bot is fully connected."""
        logger.info(f"{BOT_NAME} v{BOT_VERSION} is online!")
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")
        
        # Set presence
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="NBA games 🏀"
            )
        )
    
    async def close(self):
        """Clean up when bot shuts down."""
        await api_client.close()
        await super().close()


class ParlayCog(commands.Cog):
    """
    Cog containing all parlay-related commands.
    """
    
    def __init__(self, bot: NBABot):
        self.bot = bot
    
    # ==================== MAIN PARLAY COMMAND ====================
    
    @app_commands.command(
        name="parlay",
        description="Generate a rule-based NBA parlay using historical hit-rate data"
    )
    @app_commands.describe(
        legs="Number of legs for the parlay (2-10)",
        wager="Wager amount in USD",
        ladder="Historical game window for hit-rate calculation (default: 5)"
    )
    @app_commands.choices(ladder=[
        app_commands.Choice(name="5 games", value=5),
        app_commands.Choice(name="10 games", value=10),
        app_commands.Choice(name="15 games", value=15),
    ])
    async def parlay_command(
        self,
        interaction: discord.Interaction,
        legs: app_commands.Range[int, MIN_LEGS, MAX_LEGS],
        wager: app_commands.Range[float, MIN_WAGER, MAX_WAGER],
        ladder: Optional[int] = DEFAULT_LADDER
    ):
        """
        Main parlay generation command.
        
        Usage: /parlay legs:4 wager:10 ladder:5
        """
        await interaction.response.defer()
        
        try:
            # Generate parlay
            parlay = await parlay_engine.generate_parlay(
                legs_count=legs,
                wager=wager,
                ladder=ladder,
                user_id=str(interaction.user.id),
                guild_id=str(interaction.guild_id) if interaction.guild_id else None,
                channel_id=str(interaction.channel_id) if interaction.channel_id else None
            )
            
            if not parlay:
                # Check if no games
                games = await api_client.get_games_today()
                if not games:
                    embed = build_no_games_embed()
                else:
                    embed = build_not_enough_legs_embed(legs, 0)
                
                await interaction.followup.send(embed=embed)
                return
            
            # Build embed and view
            embed = build_parlay_embed(parlay)
            view = ParlayView(parlay)
            
            await interaction.followup.send(embed=embed, view=view)
            
            logger.info(
                f"Generated parlay {parlay.id} for user {interaction.user.id} "
                f"({legs} legs, ${wager}, ladder {ladder})"
            )
        
        except Exception as e:
            logger.error(f"Error generating parlay: {e}", exc_info=True)
            embed = build_error_embed(
                "Generation Failed",
                "An error occurred while generating the parlay. Please try again."
            )
            await interaction.followup.send(embed=embed)
    
    # ==================== HELP COMMAND ====================
    
    @app_commands.command(
        name="parlay-help",
        description="Show help information for NBABot commands"
    )
    async def help_command(self, interaction: discord.Interaction):
        """Show help embed."""
        embed = build_help_embed()
        await interaction.response.send_message(embed=embed)
    
    # ==================== RULES COMMAND ====================
    
    @app_commands.command(
        name="parlay-rules",
        description="Display eligibility rules for parlay legs"
    )
    async def rules_command(self, interaction: discord.Interaction):
        """Show eligibility rules embed."""
        embed = build_rules_embed()
        await interaction.response.send_message(embed=embed)
    
    # ==================== STATS COMMAND ====================
    
    @app_commands.command(
        name="parlay-stats",
        description="Show bot statistics and status"
    )
    async def stats_command(self, interaction: discord.Interaction):
        """Show bot statistics."""
        embed = discord.Embed(
            title=f"📊 {BOT_NAME} v{BOT_VERSION} Statistics",
            color=0x1D428A
        )
        
        # Bot stats
        embed.add_field(
            name="🤖 Bot Info",
            value=(
                f"**Version:** {BOT_VERSION}\n"
                f"**Guilds:** {len(self.bot.guilds)}\n"
                f"**Latency:** {round(self.bot.latency * 1000)}ms"
            ),
            inline=True
        )
        
        # Cache stats
        embed.add_field(
            name="📦 Cache",
            value=(
                f"**Parlays:** {len(parlay_engine._parlay_cache)}\n"
                f"**Legs:** {len(parlay_engine._leg_cache)}"
            ),
            inline=True
        )
        
        # Check today's games
        try:
            games = await api_client.get_games_today()
            games_count = len(games) if games else 0
        except:
            games_count = "Error"
        
        embed.add_field(
            name="🏀 Today's Games",
            value=f"**Available:** {games_count}",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
    
    # ==================== ERROR HANDLERS ====================
    
    @parlay_command.error
    async def parlay_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle parlay command errors."""
        if isinstance(error, app_commands.CommandOnCooldown):
            embed = build_error_embed(
                "Cooldown",
                f"Please wait {error.retry_after:.1f} seconds before using this command again."
            )
        elif isinstance(error, app_commands.MissingPermissions):
            embed = build_error_embed(
                "Missing Permissions",
                "You don't have permission to use this command."
            )
        else:
            logger.error(f"Command error: {error}", exc_info=True)
            embed = build_error_embed(
                "Error",
                "An unexpected error occurred. Please try again."
            )
        
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def main():
    """Main entry point."""
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN not found in environment variables!")
        return
    
    bot = NBABot()
    
    try:
        await bot.start(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot shutting down...")
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
