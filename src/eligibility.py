from typing import Tuple, Optional, Dict, List
# ============================================
# PLAYER PROP THRESHOLDS (v11 — LOCKED)
# ============================================
# ADDED FOR: Player prop eligibility (stricter than team bets)
# DOES NOT MODIFY EXISTING LOGIC

PLAYER_PROP_ELIGIBILITY = {
    5: {"min_hits": 4, "min_pct": 0.80, "allowed": "4-5", "rejected": "0-3"},
    10: {"min_hits": 7, "min_pct": 0.70, "allowed": "7-10", "rejected": "0-6"},
    15: {"min_hits": 10, "min_pct": 0.67, "allowed": "10-15", "rejected": "0-9"},
}

# Alt line thresholds (must pass ALL windows)
ALT_LINE_ELIGIBILITY = {
    "l5_min_pct": 0.60,   # Last 5: 60% minimum (3/5)
    "l10_min_pct": 0.65,  # Last 10: 65% minimum (7/10 rounded)
    "l15_min_pct": 0.65,  # Last 15: 65% minimum (10/15)
}


# ============================================
# PLAYER PROP ELIGIBILITY CHECKER
# ============================================
# ADDED FOR: Player prop eligibility
# DOES NOT MODIFY EXISTING check_eligibility function

def check_player_prop_eligibility(
    hits_l5: int,
    hits_l10: int,
    hits_l15: int,
    games_l5: int = 5,
    games_l10: int = 10,
    games_l15: int = 15
) -> Tuple[bool, Optional[str], Dict[str, bool]]:
    """
    Check if a player prop line is eligible.
    
    RULES (LOCKED — v11):
    - Must pass ALL three windows
    - L5: 4/5 minimum (80%)
    - L10: 7/10 minimum (70%)
    - L15: 10/15 minimum (67%)
    - Fail ANY window → DISCARD immediately
    
    Args:
        hits_l5: Hits in last 5 games
        hits_l10: Hits in last 10 games
        hits_l15: Hits in last 15 games
        games_l5: Total games in L5 window (default 5)
        games_l10: Total games in L10 window (default 10)
        games_l15: Total games in L15 window (default 15)
    
    Returns:
        Tuple of (is_eligible, rejection_reason, window_results)
    """
    window_results = {
        "l5_passed": False,
        "l10_passed": False,
        "l15_passed": False,
    }
    
    # Check L5 window
    pct_l5 = hits_l5 / games_l5 if games_l5 > 0 else 0
    threshold_l5 = PLAYER_PROP_ELIGIBILITY[5]["min_pct"]
    if pct_l5 >= threshold_l5:
        window_results["l5_passed"] = True
    else:
        return (
            False,
            f"Failed L5 window: {hits_l5}/{games_l5} ({pct_l5*100:.0f}%) < {threshold_l5*100:.0f}%",
            window_results
        )
    
    # Check L10 window
    pct_l10 = hits_l10 / games_l10 if games_l10 > 0 else 0
    threshold_l10 = PLAYER_PROP_ELIGIBILITY[10]["min_pct"]
    if pct_l10 >= threshold_l10:
        window_results["l10_passed"] = True
    else:
        return (
            False,
            f"Failed L10 window: {hits_l10}/{games_l10} ({pct_l10*100:.0f}%) < {threshold_l10*100:.0f}%",
            window_results
        )
    
    # Check L15 window
    pct_l15 = hits_l15 / games_l15 if games_l15 > 0 else 0
    threshold_l15 = PLAYER_PROP_ELIGIBILITY[15]["min_pct"]
    if pct_l15 >= threshold_l15:
        window_results["l15_passed"] = True
    else:
        return (
            False,
            f"Failed L15 window: {hits_l15}/{games_l15} ({pct_l15*100:.0f}%) < {threshold_l15*100:.0f}%",
            window_results
        )
    
    # ALL windows passed
    return (True, None, window_results)


def check_alt_line_eligibility(
    hits_l5: int,
    hits_l10: int,
    hits_l15: int,
    games_l5: int = 5,
    games_l10: int = 10,
    games_l15: int = 15
) -> Tuple[bool, Optional[str]]:
    """
    Check if an alt line is eligible (uses different thresholds).
    
    RULES (LOCKED — v11):
    - L5: 60% minimum
    - L10: 65% minimum
    - L15: 65% minimum
    - Fail ANY → DISCARD
    
    Returns:
        Tuple of (is_eligible, rejection_reason)
    """
    # L5 check
    pct_l5 = hits_l5 / games_l5 if games_l5 > 0 else 0
    if pct_l5 < ALT_LINE_ELIGIBILITY["l5_min_pct"]:
        return (False, f"Alt line failed L5: {pct_l5*100:.0f}% < 60%")
    
    # L10 check
    pct_l10 = hits_l10 / games_l10 if games_l10 > 0 else 0
    if pct_l10 < ALT_LINE_ELIGIBILITY["l10_min_pct"]:
        return (False, f"Alt line failed L10: {pct_l10*100:.0f}% < 65%")
    
    # L15 check
    pct_l15 = hits_l15 / games_l15 if games_l15 > 0 else 0
    if pct_l15 < ALT_LINE_ELIGIBILITY["l15_min_pct"]:
        return (False, f"Alt line failed L15: {pct_l15*100:.0f}% < 65%")
    
    return (True, None)


def check_odds_constraint(american_odds: int) -> Tuple[bool, Optional[str]]:
    """
    Check if odds fall within acceptable range.
    
    RULE (LOCKED):
    - Only consider lines with -250 ≤ odds ≤ +180
    - If no eligible line fits → EXCLUDE player entirely
    
    Returns:
        Tuple of (is_valid, rejection_reason)
    """
    ODDS_MIN = -250
    ODDS_MAX = 180
    
    if american_odds < ODDS_MIN:
        return (False, f"Odds {american_odds} below minimum ({ODDS_MIN})")
    
    if american_odds > ODDS_MAX:
        return (False, f"Odds {american_odds} above maximum (+{ODDS_MAX})")
    
    return (True, None)


# ============================================
# HIT RATE CALCULATORS
# ============================================
# ADDED FOR: Player prop hit rate calculation
# DOES NOT MODIFY EXISTING LOGIC

def calculate_hit_rate(
    values: List[float],
    line: float,
    direction: str = "over"
) -> Dict[str, any]:
    """
    Calculate hit rate for a line across all windows.
    
    Args:
        values: List of stat values (most recent first), up to 15
        line: The betting line
        direction: 'over' or 'under'
    
    Returns:
        Dict with hits and percentages for each window
    """
    l5 = values[:5]
    l10 = values[:10]
    l15 = values[:15]
    
    if direction == "over":
        hits_l5 = sum(1 for v in l5 if v > line)
        hits_l10 = sum(1 for v in l10 if v > line)
        hits_l15 = sum(1 for v in l15 if v > line)
    else:  # under
        hits_l5 = sum(1 for v in l5 if v < line)
        hits_l10 = sum(1 for v in l10 if v < line)
        hits_l15 = sum(1 for v in l15 if v < line)
    
    return {
        "hits_l5": hits_l5,
        "hits_l10": hits_l10,
        "hits_l15": hits_l15,
        "games_l5": len(l5),
        "games_l10": len(l10),
        "games_l15": len(l15),
        "pct_l5": hits_l5 / len(l5) if l5 else 0,
        "pct_l10": hits_l10 / len(l10) if l10 else 0,
        "pct_l15": hits_l15 / len(l15) if l15 else 0,
    }


def find_optimal_line(
    values: List[float],
    direction: str = "over"
) -> Optional[Dict[str, any]]:
    """
    Find the optimal alt line based on player's actual outputs.
    
    RULES (LOCKED — v11):
    - Candidate lines generated from raw outputs only (NOT sportsbooks)
    - For OVERS: Select LOWEST eligible line
    - For UNDERS: Select HIGHEST eligible line
    - Must pass all three windows
    
    Args:
        values: List of stat values (most recent first)
        direction: 'over' or 'under'
    
    Returns:
        Dict with optimal line info, or None if no eligible line
    """
    if len(values) < 5:
        return None
    
    # Generate candidate lines from actual values
    unique_values = sorted(set(values))
    
    # For overs: start with lowest (most likely to hit)
    # For unders: start with highest (most likely to stay under)
    if direction == "over":
        candidates = unique_values  # Ascending
    else:
        candidates = unique_values[::-1]  # Descending
    
    # Find first eligible line
    for line in candidates:
        hit_data = calculate_hit_rate(values, line, direction)
        
        is_eligible, rejection = check_alt_line_eligibility(
            hit_data["hits_l5"],
            hit_data["hits_l10"],
            hit_data["hits_l15"],
            hit_data["games_l5"],
            hit_data["games_l10"],
            hit_data["games_l15"]
        )
        
        if is_eligible:
            return {
                "line": line,
                "direction": direction,
                "hits_l5": hit_data["hits_l5"],
                "hits_l10": hit_data["hits_l10"],
                "hits_l15": hit_data["hits_l15"],
                "pct_l5": hit_data["pct_l5"],
                "pct_l10": hit_data["pct_l10"],
                "pct_l15": hit_data["pct_l15"],
            }
    
    # No eligible line found
    return None


# ============================================
# ELIGIBILITY SUMMARY HELPERS
# ============================================
# ADDED FOR: Eligibility display
# DOES NOT MODIFY EXISTING LOGIC

def get_player_prop_rules_summary() -> str:
    """Get summary of player prop eligibility rules for display."""
    return """**Player Prop Eligibility (v11)**
| Window | Minimum | Requirement |
|--------|---------|-------------|
| Last 5 | 80% | 4/5 hits |
| Last 10 | 70% | 7/10 hits |
| Last 15 | 67% | 10/15 hits |

⚠️ Must pass ALL windows — fail any = excluded"""


def format_eligibility_result(
    is_eligible: bool,
    hits_l5: int,
    hits_l10: int,
    hits_l15: int
) -> str:
    """Format eligibility result for Discord display."""
    status = "✅ ELIGIBLE" if is_eligible else "❌ EXCLUDED"
    
    return f"""{status}
• L5: {hits_l5}/5 ({hits_l5/5*100:.0f}%)
• L10: {hits_l10}/10 ({hits_l10/10*100:.0f}%)
• L15: {hits_l15}/15 ({hits_l15/15*100:.0f}%)"""


# ============================================
# END OF v11 ELIGIBILITY ADDITIONS
# ============================================
"""
NBABot v10.0 Eligibility Module

Handles all eligibility rule checking for parlay legs.
"""

from typing import Tuple, Optional
from config import ELIGIBILITY_THRESHOLDS


def check_eligibility(hits: int, games: int, ladder: int) -> Tuple[bool, Optional[str]]:
    """
    Check if a leg meets the eligibility threshold.
    
    Args:
        hits: Number of successful hits in the sample
        games: Total games in the sample
        ladder: The ladder window (5, 10, or 15)
    
    Returns:
        Tuple of (is_eligible, rejection_reason)
        - If eligible: (True, None)
        - If rejected: (False, "reason string")
    
    Thresholds:
        - Ladder 5:  Need 3+ hits (reject 0-2)
        - Ladder 10: Need 7+ hits (reject 0-6)
        - Ladder 15: Need 10+ hits (reject 0-9)
    """
    
    if ladder not in ELIGIBILITY_THRESHOLDS:
        return False, f"Invalid ladder: {ladder}. Must be 5, 10, or 15."
    
    threshold = ELIGIBILITY_THRESHOLDS[ladder]
    
    if hits >= threshold:
        return True, None
    else:
        return False, f"Hit rate {hits}/{games} below threshold {threshold}/{ladder}"


def get_threshold(ladder: int) -> int:
    """
    Get the minimum hits required for a given ladder.
    
    Args:
        ladder: The ladder window (5, 10, or 15)
    
    Returns:
        Minimum hits required to pass eligibility
    """
    return ELIGIBILITY_THRESHOLDS.get(ladder, 0)


def calculate_hit_rate_percentage(hits: int, games: int) -> float:
    """
    Calculate hit rate as a percentage.
    
    Args:
        hits: Number of successful hits
        games: Total games in sample
    
    Returns:
        Hit rate as percentage (0-100)
    """
    if games == 0:
        return 0.0
    return round((hits / games) * 100, 1)


def format_hit_rate(hits: int, games: int) -> str:
    """
    Format hit rate for display.
    
    Args:
        hits: Number of successful hits
        games: Total games in sample
    
    Returns:
        Formatted string like "3 / 5 games"
    """
    return f"{hits} / {games} games"


def get_eligibility_status_emoji(is_eligible: bool) -> str:
    """
    Get emoji for eligibility status.
    
    Args:
        is_eligible: Whether the leg is eligible
    
    Returns:
        ✅ for eligible, ❌ for rejected
    """
    return "✅" if is_eligible else "❌"


# Eligibility rules summary for display
ELIGIBILITY_RULES = {
    5: {
        "allowed": "3-5 hits",
        "rejected": "0-2 hits",
        "threshold": 3,
        "description": "Need at least 3 out of 5 games"
    },
    10: {
        "allowed": "7-10 hits",
        "rejected": "0-6 hits",
        "threshold": 7,
        "description": "Need at least 7 out of 10 games"
    },
    15: {
        "allowed": "10-15 hits",
        "rejected": "0-9 hits",
        "threshold": 10,
        "description": "Need at least 10 out of 15 games"
    }
}


def get_rules_summary() -> str:
    """
    Get a formatted summary of eligibility rules.
    
    Returns:
        Multi-line string describing all eligibility rules
    """
    lines = ["**📊 Eligibility Rules**\n"]
    
    for ladder, rules in ELIGIBILITY_RULES.items():
        lines.append(f"**{ladder}-Game Ladder:**")
        lines.append(f"  ✅ Allowed: {rules['allowed']}")
        lines.append(f"  ❌ Rejected: {rules['rejected']}")
        lines.append(f"  → {rules['description']}\n")
    
    return "\n".join(lines)
