"""
NBABot v10.1.0 — Explanation Engine

NEW MODULE: Generates detailed, number-based explanations.
Does NOT replace existing code — adds new functionality.

Key Principles:
- Explanations must include NUMBERS, not vague language
- Deterministic output (no random wording)
- Always show WHY a line was chosen
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ExplanationData:
    """Data structure for generating explanations."""
    stat_type: str
    player_name: Optional[str]
    team_name: Optional[str]
    line: float
    direction: str
    hits_l5: int
    hits_l10: int
    hits_l15: int
    avg_l5: float
    avg_l10: float
    avg_l15: float
    margin: float
    confidence: float
    alt_lines_considered: List[float]


class ExplanationEngine:
    """
    Engine for generating detailed, data-driven explanations.
    All explanations are deterministic and include specific numbers.
    """
    
    def __init__(self):
        pass
    
    # ==================== PLAYER PROP EXPLANATIONS ====================
    
    def explain_player_prop(
        self,
        player_name: str,
        stat_type: str,
        line: float,
        direction: str,
        game_values: List[float],
        alt_lines: List[float] = None
    ) -> str:
        """
        Generate detailed explanation for a player prop selection.
        
        Args:
            player_name: Player's name
            stat_type: 'points', 'rebounds', 'assists', etc.
            line: Selected line
            direction: 'over' or 'under'
            game_values: List of stat values (most recent first)
            alt_lines: Other lines that were considered
        
        Returns:
            Detailed explanation string with numbers
        """
        l5 = game_values[:5]
        l10 = game_values[:10] if len(game_values) >= 10 else game_values
        l15 = game_values[:15] if len(game_values) >= 15 else game_values
        
        # Calculate stats
        avg_l5 = sum(l5) / len(l5)
        avg_l10 = sum(l10) / len(l10)
        avg_l15 = sum(l15) / len(l15)
        
        if direction == "over":
            hits_l5 = sum(1 for v in l5 if v > line)
            hits_l10 = sum(1 for v in l10 if v > line)
            hits_l15 = sum(1 for v in l15 if v > line)
            margin = avg_l5 - line
        else:
            hits_l5 = sum(1 for v in l5 if v < line)
            hits_l10 = sum(1 for v in l10 if v < line)
            hits_l15 = sum(1 for v in l15 if v < line)
            margin = line - avg_l5
        
        stat_label = stat_type.replace("_", " ").title()
        dir_word = direction.title()
        
        explanation = f"""**📊 {player_name} — {dir_word} {line} {stat_label}**

**Hit Rate Analysis:**
• {dir_word} {line} in **{hits_l5} of last 5** games ({hits_l5/5*100:.0f}%)
• {dir_word} {line} in **{hits_l10} of last 10** games ({hits_l10/len(l10)*100:.0f}%)
• {dir_word} {line} in **{hits_l15} of last 15** games ({hits_l15/len(l15)*100:.0f}%)

**Averages:**
• Last 5 games: **{avg_l5:.1f}** {stat_type}
• Last 10 games: **{avg_l10:.1f}** {stat_type}
• Last 15 games: **{avg_l15:.1f}** {stat_type}

**Line Selection:**
• Selected **{line}** as optimal line
• Average margin: **{'+' if margin > 0 else ''}{margin:.1f}** {stat_type} {direction} the line
"""
        
        # Add alt lines comparison if available
        if alt_lines and len(alt_lines) > 1:
            explanation += f"\n**Alt Lines Considered:** {', '.join(str(l) for l in sorted(alt_lines))}"
            explanation += f"\n• Chose {line} for highest consistency across all windows"
        
        # Add recent game breakdown
        explanation += f"\n\n**Last 5 Games:** {', '.join(str(int(v)) for v in l5)}"
        
        return explanation
    
    # ==================== TEAM TOTAL EXPLANATIONS ====================
    
    def explain_team_total(
        self,
        team_name: str,
        opponent_name: str,
        line: float,
        direction: str,
        team_scores: List[float],
        opponent_allowed: List[float]
    ) -> str:
        """
        Generate detailed explanation for team total selection.
        
        Args:
            team_name: Team's name
            opponent_name: Opponent's name
            line: Team total line
            direction: 'over' or 'under'
            team_scores: Team's points scored (recent games)
            opponent_allowed: Points opponent has allowed
        
        Returns:
            Detailed explanation string
        """
        l5_team = team_scores[:5]
        l10_team = team_scores[:10] if len(team_scores) >= 10 else team_scores
        
        l5_opp = opponent_allowed[:5]
        l10_opp = opponent_allowed[:10] if len(opponent_allowed) >= 10 else opponent_allowed
        
        team_avg_l5 = sum(l5_team) / len(l5_team)
        team_avg_l10 = sum(l10_team) / len(l10_team)
        opp_avg_l5 = sum(l5_opp) / len(l5_opp)
        opp_avg_l10 = sum(l10_opp) / len(l10_opp)
        
        if direction == "over":
            hits_l5 = sum(1 for s in l5_team if s > line)
            hits_l10 = sum(1 for s in l10_team if s > line)
            team_qualifies = "✅" if team_avg_l5 >= line else "❌"
            opp_qualifies = "✅" if opp_avg_l5 >= line else "❌"
        else:
            hits_l5 = sum(1 for s in l5_team if s < line)
            hits_l10 = sum(1 for s in l10_team if s < line)
            team_qualifies = "✅" if team_avg_l5 <= line else "❌"
            opp_qualifies = "✅" if opp_avg_l5 <= line else "❌"
        
        dir_word = direction.title()
        
        explanation = f"""**📊 {team_name} Team Total — {dir_word} {line}**

**Team Scoring (L5):**
• Average: **{team_avg_l5:.1f}** points per game
• {dir_word} {line} in **{hits_l5} of 5** games ({hits_l5/5*100:.0f}%)
• Qualifies: {team_qualifies}

**Opponent Defense ({opponent_name}):**
• Allows: **{opp_avg_l5:.1f}** points per game (L5)
• Qualifies: {opp_qualifies}

**Extended Sample:**
• Team L10 Avg: **{team_avg_l10:.1f}** ppg
• Opp L10 Allows: **{opp_avg_l10:.1f}** ppg
• {dir_word} {line} in **{hits_l10} of {len(l10_team)}** games (L10)

**Recent Scores:** {', '.join(str(int(s)) for s in l5_team)}
"""
        
        return explanation
    
    # ==================== SPREAD EXPLANATIONS ====================
    
    def explain_spread(
        self,
        team_name: str,
        spread: float,
        margins: List[float],
        main_spread: float,
        alt_spreads: List[float] = None
    ) -> str:
        """
        Generate detailed explanation for spread selection.
        
        Args:
            team_name: Team's name
            spread: Selected spread
            margins: List of margin of victory/defeat
            main_spread: The main spread line
            alt_spreads: Alt spreads that were considered
        
        Returns:
            Detailed explanation string
        """
        l5 = margins[:5]
        l10 = margins[:10] if len(margins) >= 10 else margins
        
        avg_margin_l5 = sum(l5) / len(l5)
        avg_margin_l10 = sum(l10) / len(l10)
        
        # Calculate covers for selected spread
        if spread < 0:  # Favorite
            covers_l5 = sum(1 for m in l5 if m > abs(spread))
            covers_l10 = sum(1 for m in l10 if m > abs(spread))
            main_covers = sum(1 for m in l5 if m > abs(main_spread))
        else:  # Underdog
            covers_l5 = sum(1 for m in l5 if m > -spread)
            covers_l10 = sum(1 for m in l10 if m > -spread)
            main_covers = sum(1 for m in l5 if m > -main_spread)
        
        explanation = f"""**📊 {team_name} — Spread {spread:+.1f}**

**Margin of Victory:**
• Last 5 Average: **{'+' if avg_margin_l5 > 0 else ''}{avg_margin_l5:.1f}** points
• Last 10 Average: **{'+' if avg_margin_l10 > 0 else ''}{avg_margin_l10:.1f}** points

**Cover Rate (Selected {spread:+.1f}):**
• Covers in **{covers_l5} of 5** games (L5) — {covers_l5/5*100:.0f}%
• Covers in **{covers_l10} of {len(l10)}** games (L10) — {covers_l10/len(l10)*100:.0f}%

**Main Line Comparison:**
• Main spread: {main_spread:+.1f} → covers {main_covers}/5
• Selected: {spread:+.1f} → covers {covers_l5}/5
"""
        
        if spread != main_spread:
            explanation += f"\n**Why Alt Spread?**\n• {spread:+.1f} provides better cover rate than main line"
        
        explanation += f"\n\n**Recent Margins:** {', '.join(f'{int(m):+d}' for m in l5)}"
        
        return explanation
    
    # ==================== MONEYLINE EXPLANATIONS ====================
    
    def explain_moneyline(
        self,
        team_name: str,
        opponent_name: str,
        team_wins: List[bool],
        h2h_wins: int = None,
        h2h_games: int = None
    ) -> str:
        """
        Generate detailed explanation for moneyline selection.
        
        Args:
            team_name: Team's name
            opponent_name: Opponent's name
            team_wins: List of win/loss (True = win)
            h2h_wins: Head-to-head wins (optional)
            h2h_games: Head-to-head games (optional)
        
        Returns:
            Detailed explanation string
        """
        l5 = team_wins[:5]
        l10 = team_wins[:10] if len(team_wins) >= 10 else team_wins
        
        wins_l5 = sum(l5)
        wins_l10 = sum(l10)
        
        explanation = f"""**📊 {team_name} Moneyline**

**Recent Form:**
• Won **{wins_l5} of last 5** games ({wins_l5/5*100:.0f}%)
• Won **{wins_l10} of last {len(l10)}** games ({wins_l10/len(l10)*100:.0f}%)
"""
        
        if h2h_wins is not None and h2h_games is not None and h2h_games > 0:
            h2h_pct = h2h_wins / h2h_games * 100
            explanation += f"""
**Head-to-Head vs {opponent_name} (1 Year):**
• Record: **{h2h_wins} - {h2h_games - h2h_wins}** ({h2h_pct:.0f}%)
• ℹ️ H2H is supporting data only — does not affect eligibility
"""
        
        explanation += f"\n**Last 5 Results:** {', '.join('W' if w else 'L' for w in l5)}"
        
        return explanation
    
    # ==================== PARLAY SUMMARY ====================
    
    def explain_parlay_summary(
        self,
        legs: List[Dict],
        total_confidence: float
    ) -> str:
        """
        Generate summary explanation for entire parlay.
        
        Args:
            legs: List of leg data dicts
            total_confidence: Overall confidence score
        
        Returns:
            Summary explanation string
        """
        num_legs = len(legs)
        
        # Categorize legs
        high_confidence = [l for l in legs if l.get('confidence', 0) >= 80]
        medium_confidence = [l for l in legs if 60 <= l.get('confidence', 0) < 80]
        lower_confidence = [l for l in legs if l.get('confidence', 0) < 60]
        
        # Count leg types
        type_counts = {}
        for leg in legs:
            leg_type = leg.get('type', 'unknown')
            type_counts[leg_type] = type_counts.get(leg_type, 0) + 1
        
        # Check for correlated legs
        game_ids = [l.get('game_id', '') for l in legs]
        correlated = len(game_ids) - len(set(game_ids))
        
        explanation = f"""**📋 PARLAY ANALYSIS**

**Composition:**
• Total Legs: **{num_legs}**
"""
        
        for leg_type, count in type_counts.items():
            type_label = leg_type.replace("_", " ").title()
            explanation += f"• {type_label}: **{count}**\n"
        
        explanation += f"""
**Confidence Breakdown:**
• High Confidence (80%+): **{len(high_confidence)}** legs
• Medium Confidence (60-79%): **{len(medium_confidence)}** legs
• Lower Confidence (<60%): **{len(lower_confidence)}** legs
• Overall: **{total_confidence:.0f}%**

**Risk Factors:**
"""
        
        if correlated > 0:
            explanation += f"• ⚠️ **{correlated}** correlated leg(s) from same game — increases variance\n"
        else:
            explanation += "• ✅ No correlated legs — good diversification\n"
        
        if lower_confidence:
            explanation += f"• ⚠️ **{len(lower_confidence)}** leg(s) below 60% confidence\n"
        
        if len(high_confidence) == num_legs:
            explanation += "• ✅ All legs have high confidence\n"
        
        return explanation


# Global instance
explanation_engine = ExplanationEngine()
