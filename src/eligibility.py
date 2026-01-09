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
