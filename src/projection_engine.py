V11_SIGNATURE = "projection-engine-v10-legacy"

def _assert_v11():
    return V11_SIGNATURE
"""
NBABot v10.1.0 — Projection Engine

NEW MODULE: Alt line selection and projection logic.
Does NOT replace existing code — adds new functionality.

Core Principles:
- Uses averages + consistency, not single-game spikes
- Selects optimal alt lines, not default market lines
- Logic applies equally to Overs and Unders
- Prioritizes: highest probability, reasonable odds, consistency
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from statistics import mean, stdev


@dataclass
class AltLineAnalysis:
    """Analysis result for a single alt line."""
    line: float
    direction: str  # 'over' or 'under'
    hits_l5: int
    hits_l10: int
    hits_l15: int
    hit_rate_l5: float
    hit_rate_l10: float
    hit_rate_l15: float
    avg_margin: float  # Average margin above/below line
    consistency_score: float  # 0-100
    is_recommended: bool


@dataclass 
class ProjectionResult:
    """Final projection recommendation."""
    stat_type: str  # 'points', 'rebounds', etc.
    selected_line: float
    direction: str  # 'over' or 'under'
    confidence: float  # 0-100
    hit_rates: Dict[str, float]  # {'l5': 100, 'l10': 90, 'l15': 93}
    averages: Dict[str, float]  # {'l5': 24.8, 'l10': 24.6, 'l15': 23.9}
    reasoning: str
    all_lines_analyzed: List[AltLineAnalysis]


class ProjectionEngine:
    """
    Engine for analyzing stats and selecting optimal alt lines.
    """
    
    def __init__(self):
        # Minimum thresholds for recommendation
        self.min_hit_rate_l5 = 0.80   # 4/5
        self.min_hit_rate_l10 = 0.70  # 7/10
        self.min_hit_rate_l15 = 0.67  # 10/15
    
    # ==================== PLAYER PROPS ====================
    
    def analyze_player_prop(
        self,
        game_logs: List[float],
        alt_lines: List[float],
        direction: str = "over"
    ) -> ProjectionResult:
        """
        Analyze player prop and select optimal alt line.
        
        Args:
            game_logs: List of stat values (most recent first), up to 15 games
            alt_lines: Available alt lines (e.g., [20.5, 22.5, 24.5, 26.5])
            direction: 'over' or 'under'
        
        Returns:
            ProjectionResult with recommended line and analysis
        """
        if len(game_logs) < 5:
            raise ValueError("Need at least 5 games for analysis")
        
        # Split into windows
        l5 = game_logs[:5]
        l10 = game_logs[:10] if len(game_logs) >= 10 else game_logs
        l15 = game_logs[:15] if len(game_logs) >= 15 else game_logs
        
        # Calculate averages
        averages = {
            'l5': round(mean(l5), 1),
            'l10': round(mean(l10), 1),
            'l15': round(mean(l15), 1)
        }
        
        # Sort alt lines appropriately
        if direction == "over":
            # For overs, start with lowest line (most likely to hit)
            sorted_lines = sorted(alt_lines)
        else:
            # For unders, start with highest line (most likely to hit)
            sorted_lines = sorted(alt_lines, reverse=True)
        
        # Analyze each alt line
        all_analyses = []
        for line in sorted_lines:
            analysis = self._analyze_single_line(l5, l10, l15, line, direction)
            all_analyses.append(analysis)
        
        # Select best line
        best_line = self._select_best_line(all_analyses, direction)
        
        # Calculate confidence
        confidence = self._calculate_confidence(best_line) if best_line else 0
        
        # Build reasoning
        reasoning = self._build_player_reasoning(best_line, averages, direction)
        
        return ProjectionResult(
            stat_type="points",  # Will be set by caller
            selected_line=best_line.line if best_line else sorted_lines[0],
            direction=direction,
            confidence=confidence,
            hit_rates={
                'l5': best_line.hit_rate_l5 * 100 if best_line else 0,
                'l10': best_line.hit_rate_l10 * 100 if best_line else 0,
                'l15': best_line.hit_rate_l15 * 100 if best_line else 0
            },
            averages=averages,
            reasoning=reasoning,
            all_lines_analyzed=all_analyses
        )
    
    def _analyze_single_line(
        self,
        l5: List[float],
        l10: List[float],
        l15: List[float],
        line: float,
        direction: str
    ) -> AltLineAnalysis:
        """Analyze a single alt line across all windows."""
        
        if direction == "over":
            hits_l5 = sum(1 for v in l5 if v > line)
            hits_l10 = sum(1 for v in l10 if v > line)
            hits_l15 = sum(1 for v in l15 if v > line)
            margins = [v - line for v in l15]
        else:  # under
            hits_l5 = sum(1 for v in l5 if v < line)
            hits_l10 = sum(1 for v in l10 if v < line)
            hits_l15 = sum(1 for v in l15 if v < line)
            margins = [line - v for v in l15]
        
        hit_rate_l5 = hits_l5 / len(l5)
        hit_rate_l10 = hits_l10 / len(l10)
        hit_rate_l15 = hits_l15 / len(l15)
        
        avg_margin = mean(margins)
        
        # Consistency score based on hit rates across all windows
        consistency_score = self._calculate_consistency(
            hit_rate_l5, hit_rate_l10, hit_rate_l15
        )
        
        # Determine if recommended
        is_recommended = (
            hit_rate_l5 >= self.min_hit_rate_l5 and
            hit_rate_l10 >= self.min_hit_rate_l10 and
            hit_rate_l15 >= self.min_hit_rate_l15
        )
        
        return AltLineAnalysis(
            line=line,
            direction=direction,
            hits_l5=hits_l5,
            hits_l10=hits_l10,
            hits_l15=hits_l15,
            hit_rate_l5=hit_rate_l5,
            hit_rate_l10=hit_rate_l10,
            hit_rate_l15=hit_rate_l15,
            avg_margin=round(avg_margin, 1),
            consistency_score=consistency_score,
            is_recommended=is_recommended
        )
    
    def _select_best_line(
        self,
        analyses: List[AltLineAnalysis],
        direction: str
    ) -> Optional[AltLineAnalysis]:
        """
        Select the best alt line.
        
        For OVERS: Choose lowest line that clears consistently
        For UNDERS: Choose highest line player stays under consistently
        """
        # Filter to recommended lines only
        recommended = [a for a in analyses if a.is_recommended]
        
        if not recommended:
            # If none meet threshold, return highest consistency
            return max(analyses, key=lambda a: a.consistency_score)
        
        if direction == "over":
            # For overs, prefer lower lines (more likely to hit)
            # But also consider consistency
            return max(recommended, key=lambda a: (
                a.consistency_score,
                -a.line  # Lower line is better for overs
            ))
        else:
            # For unders, prefer higher lines (more likely to hit)
            return max(recommended, key=lambda a: (
                a.consistency_score,
                a.line  # Higher line is better for unders
            ))
    
    def _calculate_consistency(
        self,
        rate_l5: float,
        rate_l10: float,
        rate_l15: float
    ) -> float:
        """
        Calculate consistency score (0-100).
        Higher = more consistent across all windows.
        """
        rates = [rate_l5, rate_l10, rate_l15]
        avg_rate = mean(rates)
        
        # Penalize variance
        if len(set(rates)) > 1:
            variance_penalty = stdev(rates) * 20
        else:
            variance_penalty = 0
        
        score = (avg_rate * 100) - variance_penalty
        return max(0, min(100, round(score, 1)))
    
    def _calculate_confidence(self, analysis: AltLineAnalysis) -> float:
        """Calculate confidence score for the selection."""
        if not analysis:
            return 0
        
        # Base confidence on consistency and hit rates
        base = analysis.consistency_score
        
        # Bonus for high hit rates
        if analysis.hit_rate_l5 == 1.0:
            base += 5
        if analysis.hit_rate_l10 >= 0.9:
            base += 3
        
        # Bonus for positive margin
        if analysis.avg_margin > 3:
            base += 5
        elif analysis.avg_margin > 1:
            base += 2
        
        return min(100, round(base, 1))
    
    def _build_player_reasoning(
        self,
        analysis: Optional[AltLineAnalysis],
        averages: Dict[str, float],
        direction: str
    ) -> str:
        """Build explanation text for player prop selection."""
        if not analysis:
            return "Insufficient data for analysis."
        
        dir_word = "over" if direction == "over" else "under"
        
        reasoning = f"""• Player has gone {dir_word} {analysis.line} in:
  - {analysis.hits_l5} of last 5 games ({analysis.hit_rate_l5*100:.0f}%)
  - {analysis.hits_l10} of last 10 games ({analysis.hit_rate_l10*100:.0f}%)
  - {analysis.hits_l15} of last 15 games ({analysis.hit_rate_l15*100:.0f}%)

• Averages:
  - L5: {averages['l5']}
  - L10: {averages['l10']}
  - L15: {averages['l15']}

• Selected {analysis.line} as the safest alt line based on consistency
• Average margin: {'+' if analysis.avg_margin > 0 else ''}{analysis.avg_margin} points"""
        
        return reasoning
    
    # ==================== TEAM TOTALS ====================
    
    def analyze_team_total(
        self,
        team_scores: List[float],
        opponent_allowed: List[float],
        line: float,
        direction: str = "over"
    ) -> ProjectionResult:
        """
        Analyze team total.
        
        Args:
            team_scores: Team's points scored (last 5-15 games)
            opponent_allowed: Points opponent has allowed (last 5-15 games)
            line: The team total line
            direction: 'over' or 'under'
        
        Returns:
            ProjectionResult with analysis
        """
        # Calculate team averages
        l5_team = team_scores[:5]
        l10_team = team_scores[:10] if len(team_scores) >= 10 else team_scores
        
        team_avg_l5 = mean(l5_team)
        team_avg_l10 = mean(l10_team)
        
        # Calculate opponent defense averages
        l5_opp = opponent_allowed[:5]
        l10_opp = opponent_allowed[:10] if len(opponent_allowed) >= 10 else opponent_allowed
        
        opp_avg_l5 = mean(l5_opp)
        opp_avg_l10 = mean(l10_opp)
        
        # Check conditions
        if direction == "over":
            # Team avg >= line AND opponent allows >= line
            team_qualifies = team_avg_l5 >= line
            opp_qualifies = opp_avg_l5 >= line
            
            hits_l5 = sum(1 for s in l5_team if s > line)
            hits_l10 = sum(1 for s in l10_team if s > line)
        else:
            # Team avg <= line AND opponent allows <= line
            team_qualifies = team_avg_l5 <= line
            opp_qualifies = opp_avg_l5 <= line
            
            hits_l5 = sum(1 for s in l5_team if s < line)
            hits_l10 = sum(1 for s in l10_team if s < line)
        
        both_qualify = team_qualifies and opp_qualifies
        
        hit_rate_l5 = hits_l5 / len(l5_team)
        hit_rate_l10 = hits_l10 / len(l10_team)
        
        # Confidence based on both conditions
        if both_qualify and hit_rate_l5 >= 0.8:
            confidence = 85
        elif both_qualify and hit_rate_l5 >= 0.6:
            confidence = 70
        elif team_qualifies or opp_qualifies:
            confidence = 50
        else:
            confidence = 30
        
        reasoning = self._build_team_total_reasoning(
            team_avg_l5, team_avg_l10,
            opp_avg_l5, opp_avg_l10,
            line, direction,
            hits_l5, len(l5_team),
            hits_l10, len(l10_team)
        )
        
        return ProjectionResult(
            stat_type="team_total",
            selected_line=line,
            direction=direction,
            confidence=confidence,
            hit_rates={
                'l5': hit_rate_l5 * 100,
                'l10': hit_rate_l10 * 100,
                'l15': hit_rate_l10 * 100  # Use l10 if l15 not available
            },
            averages={
                'l5': round(team_avg_l5, 1),
                'l10': round(team_avg_l10, 1),
                'l15': round(team_avg_l10, 1)
            },
            reasoning=reasoning,
            all_lines_analyzed=[]
        )
    
    def _build_team_total_reasoning(
        self,
        team_avg_l5: float,
        team_avg_l10: float,
        opp_avg_l5: float,
        opp_avg_l10: float,
        line: float,
        direction: str,
        hits_l5: int,
        games_l5: int,
        hits_l10: int,
        games_l10: int
    ) -> str:
        """Build explanation for team total."""
        dir_word = "over" if direction == "over" else "under"
        
        return f"""• Team averages {team_avg_l5:.1f} points per game (L5)
• Opponent allows {opp_avg_l5:.1f} points per game (L5)
• Team total {dir_word} {line} has cleared in:
  - {hits_l5} of last {games_l5} games ({hits_l5/games_l5*100:.0f}%)
  - {hits_l10} of last {games_l10} games ({hits_l10/games_l10*100:.0f}%)

• L10 Averages:
  - Team: {team_avg_l10:.1f} ppg
  - Opp Allows: {opp_avg_l10:.1f} ppg"""
    
    # ==================== SPREADS ====================
    
    def analyze_spread(
        self,
        margins: List[float],
        main_spread: float,
        alt_spreads: List[float]
    ) -> ProjectionResult:
        """
        Analyze spread and select optimal alt spread.
        
        Args:
            margins: List of margin of victory/defeat (positive = win)
            main_spread: The main spread line
            alt_spreads: Available alt spreads
        
        Returns:
            ProjectionResult with recommended spread
        """
        l5 = margins[:5]
        l10 = margins[:10] if len(margins) >= 10 else margins
        l15 = margins[:15] if len(margins) >= 15 else margins
        
        # Analyze each spread
        best_spread = main_spread
        best_hit_rate = 0
        
        all_spreads = [main_spread] + alt_spreads
        spread_analyses = []
        
        for spread in sorted(all_spreads):
            # For favorite (negative spread): margin must be > abs(spread)
            # For underdog (positive spread): margin must be > -spread
            if spread < 0:
                hits_l5 = sum(1 for m in l5 if m > abs(spread))
                hits_l10 = sum(1 for m in l10 if m > abs(spread))
            else:
                hits_l5 = sum(1 for m in l5 if m > -spread)
                hits_l10 = sum(1 for m in l10 if m > -spread)
            
            hit_rate_l5 = hits_l5 / len(l5)
            hit_rate_l10 = hits_l10 / len(l10)
            
            spread_analyses.append({
                'spread': spread,
                'hits_l5': hits_l5,
                'hits_l10': hits_l10,
                'hit_rate_l5': hit_rate_l5,
                'hit_rate_l10': hit_rate_l10
            })
            
            # Prefer spreads with 100% L5 hit rate
            if hit_rate_l5 == 1.0 and hit_rate_l5 > best_hit_rate:
                best_spread = spread
                best_hit_rate = hit_rate_l5
            elif hit_rate_l5 >= 0.8 and hit_rate_l5 > best_hit_rate:
                best_spread = spread
                best_hit_rate = hit_rate_l5
        
        # Get best analysis
        best_analysis = next(
            (a for a in spread_analyses if a['spread'] == best_spread),
            spread_analyses[0]
        )
        
        avg_margin = mean(margins)
        
        reasoning = f"""• Team margin of victory (L5): {'+' if avg_margin > 0 else ''}{mean(l5):.1f} pts
• Main spread {main_spread:+.1f} hits {sum(1 for m in l5 if m > abs(main_spread) if main_spread < 0 else m > -main_spread)}/5
• Alt spread {best_spread:+.1f} hits {best_analysis['hits_l5']}/5 (selected)

• Spread cover rates:
  - L5: {best_analysis['hit_rate_l5']*100:.0f}%
  - L10: {best_analysis['hit_rate_l10']*100:.0f}%"""
        
        return ProjectionResult(
            stat_type="spread",
            selected_line=best_spread,
            direction="cover",
            confidence=best_hit_rate * 100,
            hit_rates={
                'l5': best_analysis['hit_rate_l5'] * 100,
                'l10': best_analysis['hit_rate_l10'] * 100,
                'l15': best_analysis['hit_rate_l10'] * 100
            },
            averages={
                'l5': round(mean(l5), 1),
                'l10': round(mean(l10), 1),
                'l15': round(mean(l15), 1)
            },
            reasoning=reasoning,
            all_lines_analyzed=[]
        )


# Global instance
projection_engine = ProjectionEngine()
