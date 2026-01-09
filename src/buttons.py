"""
NBABot v10.0 Button Handlers (FIXED)

Handles all Discord button interactions with proper defer/reply pattern.
"""

import discord
from discord.ui import View, Button, Select
from typing import Optional, List
from datetime import datetime

from embeds import build_insights_embed, build_explain_embed, build_parlay_embed
from parlay_engine import parlay_engine, Parlay, Leg


class LegSelectMenu(discord.ui.Select):
    """
    Dropdown menu to select a leg for insights/explain.
    """
    
    def __init__(self, parlay: Parlay, action: str):
        self.parlay = parlay
        self.action = action  # 'insights' or 'explain'
        
        options = []
        for i, leg in enumerate(parlay.legs, 1):
            # Truncate label if too long
            label = leg.selection.label[:45] + "..." if len(leg.selection.label) > 45 else leg.selection.label
            options.append(
                discord.SelectOption(
                    label=f"Leg {i}: {label}",
                    value=leg.id,
                    description=f"{leg.hit_rate.hits}/{leg.hit_rate.games} hit rate ({leg.hit_rate.percentage:.0f}%)"
                )
            )
        
        placeholder = "Select a leg for insights..." if action == "insights" else "Select a leg to explain..."
        
        super().__init__(
            placeholder=placeholder,
            options=options,
            min_values=1,
            max_values=1
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Handle leg selection with proper defer."""
        # IMPORTANT: Defer first to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        leg_id = self.values[0]
        leg = parlay_engine.get_leg(leg_id)
        
        if not leg:
            await interaction.followup.send(
                "❌ Leg data not found. Please generate a new parlay.",
                ephemeral=True
            )
            return
        
        if self.action == "insights":
            embed = build_insights_embed(leg)
        else:
            embed = build_explain_embed(leg)
        
        await interaction.followup.send(embed=embed, ephemeral=True)


class LegSelectView(View):
    """View containing the leg select menu."""
    
    def __init__(self, parlay: Parlay, action: str, timeout: float = 60.0):
        super().__init__(timeout=timeout)
        self.add_item(LegSelectMenu(parlay, action))


class ParlayView(View):
    """
    Main view with parlay interaction buttons.
    Fixed with proper interaction handling.
    """
    
    def __init__(self, parlay: Parlay, timeout: float = 300.0):
        super().__init__(timeout=timeout)
        self.parlay = parlay
        self.last_refresh = datetime.now()
    
    @discord.ui.button(label="📊 Insights", style=discord.ButtonStyle.primary)
    async def insights_button(self, interaction: discord.Interaction, button: Button):
        """
        Show statistical insights for the parlay.
        INSIGHTS = Numerical data summary, risk analysis.
        """
        # Defer immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        # Build insights summary for entire parlay
        insights_text = self._build_parlay_insights()
        
        embed = discord.Embed(
            title="📊 PARLAY INSIGHTS",
            description=insights_text,
            color=0x1D428A
        )
        embed.set_footer(text="NBABot v10.0 | Data Analysis")
        
        # Also show leg selector for individual leg insights
        view = LegSelectView(self.parlay, "insights")
        
        await interaction.followup.send(
            embed=embed,
            view=view,
            ephemeral=True
        )
    
    @discord.ui.button(label="📖 Explain", style=discord.ButtonStyle.secondary)
    async def explain_button(self, interaction: discord.Interaction, button: Button):
        """
        Explain why picks were included.
        EXPLAIN = Human-readable reasoning, educational.
        """
        # Defer immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        # Build explanation for entire parlay
        explain_text = self._build_parlay_explanation()
        
        embed = discord.Embed(
            title="📖 WHY THIS PARLAY WAS GENERATED",
            description=explain_text,
            color=0x1D428A
        )
        embed.set_footer(text="NBABot v10.0 | Educational Only")
        
        # Also show leg selector for individual explanations
        view = LegSelectView(self.parlay, "explain")
        
        await interaction.followup.send(
            embed=embed,
            view=view,
            ephemeral=True
        )
    
    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.success)
    async def refresh_button(self, interaction: discord.Interaction, button: Button):
        """
        Generate a new parlay with same settings.
        Uses deferUpdate() and edits existing message.
        """
        # Use deferUpdate for refresh (edits existing message)
        await interaction.response.defer()
        
        # Check cooldown (5 seconds)
        time_since_refresh = (datetime.now() - self.last_refresh).total_seconds()
        if time_since_refresh < 5:
            await interaction.followup.send(
                f"⏳ Please wait {5 - int(time_since_refresh)} seconds before refreshing.",
                ephemeral=True
            )
            return
        
        # Generate new parlay with same settings
        new_parlay = await parlay_engine.generate_parlay(
            legs_count=self.parlay.leg_count,
            wager=self.parlay.wager,
            ladder=self.parlay.ladder,
            user_id=str(interaction.user.id),
            guild_id=str(interaction.guild_id) if interaction.guild_id else None,
            channel_id=str(interaction.channel_id) if interaction.channel_id else None
        )
        
        if not new_parlay:
            await interaction.followup.send(
                "❌ Could not generate a new parlay. Please try again.",
                ephemeral=True
            )
            return
        
        # Update references
        self.parlay = new_parlay
        self.last_refresh = datetime.now()
        
        # Build new embed with refresh timestamp
        embed = build_parlay_embed(new_parlay)
        
        # Add refresh timestamp to footer
        refresh_time = self.last_refresh.strftime("%I:%M %p")
        embed.set_footer(text=f"🔄 Refreshed: {refresh_time} | NBABot v10.0 | Educational Only")
        
        # Edit the original message
        await interaction.message.edit(embed=embed, view=self)
    
    def _build_parlay_insights(self) -> str:
        """Build statistical insights for the parlay."""
        # Calculate average hit rate
        total_percentage = sum(leg.hit_rate.percentage for leg in self.parlay.legs)
        avg_hit_rate = total_percentage / len(self.parlay.legs)
        
        # Find highest risk leg (lowest hit rate)
        highest_risk = min(self.parlay.legs, key=lambda l: l.hit_rate.percentage)
        
        # Find lowest risk leg (highest hit rate)
        lowest_risk = max(self.parlay.legs, key=lambda l: l.hit_rate.percentage)
        
        # Count correlated legs (same game)
        game_ids = [leg.matchup.game_id for leg in self.parlay.legs]
        correlated = len(game_ids) - len(set(game_ids))
        
        # Count leg types
        type_counts = {}
        for leg in self.parlay.legs:
            type_counts[leg.type] = type_counts.get(leg.type, 0) + 1
        
        insights = f"""
**📈 Overall Statistics**
• Average Hit Rate: **{avg_hit_rate:.1f}%**
• Total Legs: **{len(self.parlay.legs)}**
• Sample Window: **Last {self.parlay.ladder} games**

**⚠️ Risk Analysis**
• Highest Risk: **{highest_risk.selection.label[:40]}** ({highest_risk.hit_rate.percentage:.0f}%)
• Lowest Risk: **{lowest_risk.selection.label[:40]}** ({lowest_risk.hit_rate.percentage:.0f}%)
• Correlated Legs: **{correlated}** (same game)

**🎯 Leg Breakdown**
"""
        for leg_type, count in type_counts.items():
            type_name = leg_type.replace("_", " ").title()
            insights += f"• {type_name}: **{count}**\n"
        
        return insights
    
    def _build_parlay_explanation(self) -> str:
        """Build human-readable explanation for the parlay."""
        threshold = {5: 3, 10: 7, 15: 10}[self.parlay.ladder]
        
        explanation = f"""
**🎯 Selection Criteria**
Each leg was selected because it has hit in at least **{threshold} of the last {self.parlay.ladder} games** ({(threshold/self.parlay.ladder)*100:.0f}%+ hit rate).

**📊 Methodology**
• Recent form was prioritized over season averages
• Only legs meeting the eligibility threshold were considered
• Variety in leg types was preferred when possible

**⚠️ Important Notes**
"""
        # Check for correlated legs
        game_ids = [leg.matchup.game_id for leg in self.parlay.legs]
        if len(game_ids) != len(set(game_ids)):
            explanation += "• ⚡ Some legs come from the same matchup, which increases variance\n"
        
        # Check for any player props
        player_props = [l for l in self.parlay.legs if l.type == "player_prop"]
        if player_props:
            explanation += f"• 👤 Contains {len(player_props)} player prop(s) — more volatile than team bets\n"
        
        # Check for totals
        totals = [l for l in self.parlay.legs if "total" in l.type]
        if totals:
            explanation += f"• 📊 Contains {len(totals)} total(s) — affected by pace and game script\n"
        
        explanation += """
**📚 Educational Purpose**
This parlay is generated for educational and entertainment purposes only. Past performance does not guarantee future results.
"""
        return explanation
    
    async def on_timeout(self):
        """Disable buttons after timeout."""
        for item in self.children:
            item.disabled = True
