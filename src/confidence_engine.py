"""
NBABot v11 — Confidence Engine

ADDED FOR: Confidence Scoring System (NEVER 100%)
DOES NOT MODIFY EXISTING LOGIC

Core Rules (LOCKED):
- Maximum confidence: 95 (NEVER 100%)
- Base scores from hit rate consistency
- Positive modifiers capped by ceiling
- Negative modifiers always apply
- Final score: clamp(score, min=0, max=95)
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


# ============================================
# CONSTANTS (LOCKED — DO NOT MODIFY)
# ============================================

CONFIDENCE_MAX = 95  # NEVER 100%
CONFIDENCE_MIN = 0

# Base scores by hit quality (consistency-driven)
BASE_SCORES = {
    # (hits, games): base_score
    (5, 5): 70,    # 5/5 hits
    (4, 5): 62,    # 4/5 hits
    (8, 10): 65,   # 8/10 hits
    (7, 10): 58,   # 7/10 hits
    (13, 15): 68,  # 13/15 hits
    (12, 15): 60,  # 12/15 hits
    (11, 15): 56,  # 11/15 hits
    (10, 15): 52,  # 10/15 hits
}

# Positive modifiers (context-only, capped)
POSITIVE_MODIFIERS = {
    "alt_line_consistency": 5,      # Strong alt line consistency
    "minutes_stable": 5,            # Minutes stable (no flags)
    "role_clarity": 4,              # Role clarity (no stat conflict)
    "favorable_matchup": 4,         # Favorable matchup (position/opponent)
    "h2h_alignment": 3,             # Head-to-head alignment
    "home_advantage": 2,            # Home advantage
}

# Negative modifiers (MANDATORY — always apply)
NEGATIVE_MODIFIERS = {
    "questionable_doubtful": -6,    # Questionable or Doubtful status
    "one_low_minute_game": -7,      # 1 low-minute game
    "two_low_minute_games": -12,    # 2 low-minute games
    "role_shift_conflict": -6,      # Recent role shift conflict
    "key_teammate_missing": -5,     # Key teammate missing
    "road_disadvantage": -2,        # Road disadvantage
}

# Confidence tiers (display only — do not affect math)
CONFIDENCE_TIERS = {
    "safe": {"min": 80, "max": 95, "emoji": "🛡️", "label": "Safe"},
    "normal": {"min": 60, "max": 79, "emoji": "⚖️", "label": "Normal"},
    "moonshot": {"min": 40, "max": 59, "emoji": "🚀", "label": "Moonshot"},
    "high_risk": {"min": 0, "max": 39, "emoji": "⚠️", "label": "High Risk"},
}


# ============================================
# DATA STRUCTURES
# ============================================

@dataclass
class ConfidenceResult:
    """Result of confidence calculation."""
    score: int                      # Final score (0-95)
    tier: str                       # 'safe', 'normal', 'moonshot', 'high_risk'
    tier_emoji: str                 # 🛡️, ⚖️, 🚀, ⚠️
    tier_label: str                 # 'Safe', 'Normal', etc.
    base_score: int                 # Base score before modifiers
    positive_applied: Dict[str, int]  # Positive modifiers applied
    negative_applied: Dict[str, int]  # Negative modifiers applied
    why_not_higher: List[str]       # Reasons confidence is not 95


@dataclass
class HitRateData:
    """Hit rate data for confidence calculation."""
    hits_l5: int
    games_l5: int
    hits_l10: int
    games_l10: int
    hits_l15: int
    games_l15: int


@dataclass
class ContextData:
    """Context data for modifiers."""
    # Positive context
    alt_line_consistent: bool = False
    minutes_stable: bool = False
    role_clear: bool = False
    favorable_matchup: bool = False
    h2h_favorable: bool = False
    is_home: bool = False
    
    # Negative context
    is_questionable: bool = False
    is_doubtful: bool = False
    low_minute_games: int = 0       # 0, 1, or 2+
    role_shift_detected: bool = False
    teammate_missing: bool = False
    is_road: bool = False


# ============================================
# CORE FUNCTIONS
# ============================================

def clamp(value: int, min_val: int = CONFIDENCE_MIN, max_val: int = CONFIDENCE_MAX) -> int:
    """
    Clamp confidence score to valid range.
    
    LOCKED RULE: Max is always 95, never 100.
    """
    return max(min_val, min(max_val, value))


def get_base_score(hit_rate: HitRateData) -> Tuple[int, str]:
    """
    Calculate base confidence score from hit rates.
    
    RULE: If multiple windows qualify, use the strongest applicable base.
    RULE: Bases do not stack.
    
    Returns:
        Tuple of (base_score, window_used)
    """
    candidates = []
    
    # Check L5
    if hit_rate.games_l5 >= 5:
        key = (hit_rate.hits_l5, hit_rate.games_l5)
        if key in BASE_SCORES:
            candidates.append((BASE_SCORES[key], f"{hit_rate.hits_l5}/{hit_rate.games_l5}"))
    
    # Check L10
    if hit_rate.games_l10 >= 10:
        key = (hit_rate.hits_l10, hit_rate.games_l10)
        if key in BASE_SCORES:
            candidates.append((BASE_SCORES[key], f"{hit_rate.hits_l10}/{hit_rate.games_l10}"))
    
    # Check L15
    if hit_rate.games_l15 >= 15:
        key = (hit_rate.hits_l15, hit_rate.games_l15)
        if key in BASE_SCORES:
            candidates.append((BASE_SCORES[key], f"{hit_rate.hits_l15}/{hit_rate.games_l15}"))
    
    # If no exact match, calculate based on percentage
    if not candidates:
        # Use weighted formula: (L15 × 40) + (L10 × 35) + (L5 × 25) / 100
        pct_l5 = (hit_rate.hits_l5 / hit_rate.games_l5 * 100) if hit_rate.games_l5 > 0 else 0
        pct_l10 = (hit_rate.hits_l10 / hit_rate.games_l10 * 100) if hit_rate.games_l10 > 0 else 0
        pct_l15 = (hit_rate.hits_l15 / hit_rate.games_l15 * 100) if hit_rate.games_l15 > 0 else 0
        
        weighted = (pct_l15 * 0.40) + (pct_l10 * 0.35) + (pct_l5 * 0.25)
        base = int(weighted * 0.95)  # Scale to 0-95 range
        return (clamp(base), "weighted")
    
    # Return highest base score (strongest window)
    best = max(candidates, key=lambda x: x[0])
    return best


def apply_positive_modifiers(base: int, context: ContextData) -> Tuple[int, Dict[str, int]]:
    """
    Apply positive modifiers to base score.
    
    RULE: Positive modifiers reward context and stability, not raw stats.
    RULE: They are capped by global confidence ceiling.
    """
    applied = {}
    score = base
    
    if context.alt_line_consistent:
        mod = POSITIVE_MODIFIERS["alt_line_consistency"]
        score += mod
        applied["alt_line_consistency"] = mod
    
    if context.minutes_stable:
        mod = POSITIVE_MODIFIERS["minutes_stable"]
        score += mod
        applied["minutes_stable"] = mod
    
    if context.role_clear:
        mod = POSITIVE_MODIFIERS["role_clarity"]
        score += mod
        applied["role_clarity"] = mod
    
    if context.favorable_matchup:
        mod = POSITIVE_MODIFIERS["favorable_matchup"]
        score += mod
        applied["favorable_matchup"] = mod
    
    if context.h2h_favorable:
        mod = POSITIVE_MODIFIERS["h2h_alignment"]
        score += mod
        applied["h2h_alignment"] = mod
    
    if context.is_home:
        mod = POSITIVE_MODIFIERS["home_advantage"]
        score += mod
        applied["home_advantage"] = mod
    
    return (score, applied)


def apply_negative_modifiers(score: int, context: ContextData) -> Tuple[int, Dict[str, int], List[str]]:
    """
    Apply negative modifiers to score.
    
    RULE: Negative modifiers ALWAYS apply when triggered.
    RULE: They can outweigh positives.
    
    Returns:
        Tuple of (score, applied_mods, reasons)
    """
    applied = {}
    reasons = []
    
    if context.is_questionable or context.is_doubtful:
        mod = NEGATIVE_MODIFIERS["questionable_doubtful"]
        score += mod
        applied["questionable_doubtful"] = mod
        status = "Doubtful" if context.is_doubtful else "Questionable"
        reasons.append(f"Player listed as {status}")
    
    if context.low_minute_games >= 2:
        mod = NEGATIVE_MODIFIERS["two_low_minute_games"]
        score += mod
        applied["two_low_minute_games"] = mod
        reasons.append("2+ low-minute games detected")
    elif context.low_minute_games == 1:
        mod = NEGATIVE_MODIFIERS["one_low_minute_game"]
        score += mod
        applied["one_low_minute_game"] = mod
        reasons.append("1 low-minute game detected")
    
    if context.role_shift_detected:
        mod = NEGATIVE_MODIFIERS["role_shift_conflict"]
        score += mod
        applied["role_shift_conflict"] = mod
        reasons.append("Recent role shift detected")
    
    if context.teammate_missing:
        mod = NEGATIVE_MODIFIERS["key_teammate_missing"]
        score += mod
        applied["key_teammate_missing"] = mod
        reasons.append("Key teammate missing")
    
    if context.is_road:
        mod = NEGATIVE_MODIFIERS["road_disadvantage"]
        score += mod
        applied["road_disadvantage"] = mod
        reasons.append("Road disadvantage")
    
    return (score, applied, reasons)


def get_confidence_tier(score: int) -> Tuple[str, str, str]:
    """
    Get confidence tier from score.
    
    RULE: Tiers are display only — they do not affect math.
    
    Returns:
        Tuple of (tier_key, emoji, label)
    """
    for tier_key, tier_data in CONFIDENCE_TIERS.items():
        if tier_data["min"] <= score <= tier_data["max"]:
            return (tier_key, tier_data["emoji"], tier_data["label"])
    
    # Default fallback
    return ("high_risk", "⚠️", "High Risk")


def build_why_not_higher(
    score: int,
    negative_reasons: List[str],
    context: ContextData
) -> List[str]:
    """
    Build list of reasons why confidence is not 95.
    
    RULE: Every pick MUST explain why confidence is not higher.
    """
    reasons = []
    
    # Add negative modifier reasons
    reasons.extend(negative_reasons)
    
    # Add inherent uncertainty if score is high but not max
    if score >= 85 and score < CONFIDENCE_MAX:
        if not reasons:
            reasons.append("Inherent game-to-game variance")
    
    # Add context-specific reasons
    if not context.minutes_stable and "minute" not in " ".join(reasons).lower():
        reasons.append("Minutes not fully stable")
    
    if not context.alt_line_consistent:
        reasons.append("Alt line variance exists")
    
    # Ensure at least one reason
    if not reasons:
        reasons.append("Standard uncertainty in sports outcomes")
    
    return reasons[:4]  # Cap at 4 reasons


# ============================================
# MAIN CALCULATION FUNCTION
# ============================================

def calculate_confidence(
    hit_rate: HitRateData,
    context: ContextData
) -> ConfidenceResult:
    """
    Calculate confidence score for a pick.
    
    LOCKED RULES:
    - Max confidence: 95 (NEVER 100%)
    - Base from consistency
    - Positive modifiers capped
    - Negative modifiers always apply
    - Final: clamp(score, 0, 95)
    """
    # Step 1: Get base score
    base_score, window_used = get_base_score(hit_rate)
    
    # Step 2: Apply positive modifiers
    score_after_positive, positive_applied = apply_positive_modifiers(base_score, context)
    
    # Step 3: Apply negative modifiers (MANDATORY)
    score_after_negative, negative_applied, negative_reasons = apply_negative_modifiers(
        score_after_positive, context
    )
    
    # Step 4: Clamp to valid range (0-95, NEVER 100)
    final_score = clamp(score_after_negative)
    
    # Step 5: Get tier
    tier_key, tier_emoji, tier_label = get_confidence_tier(final_score)
    
    # Step 6: Build "why not higher" explanation
    why_not_higher = build_why_not_higher(final_score, negative_reasons, context)
    
    return ConfidenceResult(
        score=final_score,
        tier=tier_key,
        tier_emoji=tier_emoji,
        tier_label=tier_label,
        base_score=base_score,
        positive_applied=positive_applied,
        negative_applied=negative_applied,
        why_not_higher=why_not_higher
    )


# ============================================
# HELPER FUNCTIONS
# ============================================

def format_confidence_display(result: ConfidenceResult) -> str:
    """
    Format confidence for Discord display.
    
    Output: "84 / 95 (🛡️ Safe)"
    """
    return f"{result.score} / {CONFIDENCE_MAX} ({result.tier_emoji} {result.tier_label})"


def format_why_not_higher(result: ConfidenceResult) -> str:
    """
    Format "why not higher" section for Discord.
    
    Output:
    ⚠️ Why not higher:
    • Player listed as Questionable
    • Recent role shift detected
    """
    if not result.why_not_higher:
        return ""
    
    lines = ["⚠️ Why not higher:"]
    for reason in result.why_not_higher:
        lines.append(f"• {reason}")
    
    return "\n".join(lines)


# ============================================
# QUICK CALCULATION (SIMPLIFIED)
# ============================================

def quick_confidence(
    hits_l5: int,
    hits_l10: int,
    hits_l15: int,
    games_l5: int = 5,
    games_l10: int = 10,
    games_l15: int = 15,
    is_questionable: bool = False,
    low_minute_games: int = 0,
    is_home: bool = False
) -> int:
    """
    Quick confidence calculation with minimal inputs.
    
    Returns: Confidence score (0-95)
    """
    hit_rate = HitRateData(
        hits_l5=hits_l5,
        games_l5=games_l5,
        hits_l10=hits_l10,
        games_l10=games_l10,
        hits_l15=hits_l15,
        games_l15=games_l15
    )
    
    context = ContextData(
        is_questionable=is_questionable,
        low_minute_games=low_minute_games,
        is_home=is_home,
        is_road=not is_home
    )
    
    result = calculate_confidence(hit_rate, context)
    return result.score
