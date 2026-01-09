"""
NBABot v11 — Caution Engine

ADDED FOR: Universal Caution System
DOES NOT MODIFY EXISTING LOGIC

Core Rules (LOCKED):
- Cautions must visibly appear across picks, Insights, and Explain
- ⚠️ = Mild volatility (1 trigger)
- ⚠️⚠️ = High volatility (stacked triggers)
- ❌ = Excluded (never shown as a pick)
- Cautions appear BEFORE buttons in Discord output
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


# ============================================
# CONSTANTS (LOCKED — DO NOT MODIFY)
# ============================================

class CautionLevel(Enum):
    """Caution severity levels."""
    NONE = 0
    MILD = 1        # ⚠️
    HIGH = 2        # ⚠️⚠️
    EXCLUDED = 3    # ❌ (never render)


# Caution triggers and their severity
CAUTION_TRIGGERS = {
    # Player Status
    "questionable": {"level": 1, "message": "Listed as Questionable"},
    "doubtful": {"level": 2, "message": "Listed as Doubtful"},
    "game_time_decision": {"level": 1, "message": "Game-time decision"},
    
    # Minutes Volatility
    "minutes_drop_single": {"level": 1, "message": "Minutes dropped in last game"},
    "minutes_drop_multiple": {"level": 2, "message": "Minutes volatility detected (2+ games below average)"},
    "low_minutes_recent": {"level": 1, "message": "Recent low-minute game"},
    
    # Role Changes
    "role_shift_minor": {"level": 1, "message": "Minor role shift detected"},
    "role_shift_major": {"level": 2, "message": "Significant role change detected"},
    "facilitator_increase": {"level": 1, "message": "Assist rate trending upward, may cap scoring"},
    
    # Team Context
    "teammate_out": {"level": 1, "message": "Key teammate missing"},
    "star_player_out": {"level": 2, "message": "Star player ruled OUT"},
    "back_to_back": {"level": 1, "message": "Back-to-back game"},
    
    # Matchup Risk
    "blowout_risk": {"level": 1, "message": "Blowout risk may reduce late-game effort"},
    "pace_down": {"level": 1, "message": "Pace-down matchup"},
    "strong_defender": {"level": 1, "message": "Elite defender assigned"},
    
    # Line Risk
    "large_spread": {"level": 1, "message": "Large spread increases variance"},
    "alt_line_volatility": {"level": 2, "message": "Alt line volatility"},
    "thin_margin": {"level": 1, "message": "Thin margin on historical covers"},
    
    # Scoring Pattern
    "scoring_concentrated": {"level": 1, "message": "Scoring concentrated in specific quarters"},
    "inconsistent_scoring": {"level": 1, "message": "Inconsistent scoring nights"},
    
    # General
    "road_game": {"level": 1, "message": "Road disadvantage"},
}

# Display icons
CAUTION_ICONS = {
    CautionLevel.NONE: "",
    CautionLevel.MILD: "⚠️",
    CautionLevel.HIGH: "⚠️⚠️",
    CautionLevel.EXCLUDED: "❌",
}


# ============================================
# DATA STRUCTURES
# ============================================

@dataclass
class Caution:
    """Single caution trigger."""
    key: str
    level: int
    message: str


@dataclass
class CautionResult:
    """Result of caution detection."""
    level: CautionLevel
    icon: str
    triggers: List[Caution]
    messages: List[str]
    should_exclude: bool
    total_severity: int


@dataclass
class PlayerCautionData:
    """Input data for player caution detection."""
    # Status
    injury_status: Optional[str] = None  # 'questionable', 'doubtful', 'out', None
    is_game_time_decision: bool = False
    
    # Minutes
    minutes_last_game: Optional[float] = None
    minutes_avg: Optional[float] = None
    low_minute_game_count: int = 0
    
    # Role
    assist_rate_trending_up: bool = False
    role_shift_detected: bool = False
    role_shift_severity: str = "none"  # 'none', 'minor', 'major'
    
    # Team
    key_teammate_out: bool = False
    star_player_out: bool = False
    is_back_to_back: bool = False
    
    # Matchup
    blowout_risk: bool = False
    pace_down_matchup: bool = False
    elite_defender_matchup: bool = False
    
    # Location
    is_road: bool = False


@dataclass
class TeamCautionData:
    """Input data for team caution detection."""
    # Roster
    star_player_out: bool = False
    key_player_out: bool = False
    multiple_players_out: bool = False
    
    # Schedule
    is_back_to_back: bool = False
    is_road: bool = False
    
    # Line
    spread_size: float = 0.0
    is_large_spread: bool = False
    
    # Matchup
    blowout_risk: bool = False
    pace_mismatch: bool = False


# ============================================
# CORE FUNCTIONS
# ============================================

def detect_player_cautions(data: PlayerCautionData) -> CautionResult:
    """
    Detect cautions for a player prop.
    
    RULE: Cautions must always appear when triggered.
    """
    triggers = []
    
    # Check injury status
    if data.injury_status == "doubtful":
        triggers.append(_get_caution("doubtful"))
    elif data.injury_status == "questionable":
        triggers.append(_get_caution("questionable"))
    
    if data.is_game_time_decision:
        triggers.append(_get_caution("game_time_decision"))
    
    # Check minutes volatility
    if data.low_minute_game_count >= 2:
        triggers.append(_get_caution("minutes_drop_multiple"))
    elif data.low_minute_game_count == 1:
        triggers.append(_get_caution("minutes_drop_single"))
    
    if data.minutes_last_game and data.minutes_avg:
        if data.minutes_last_game < data.minutes_avg * 0.75:
            triggers.append(_get_caution("low_minutes_recent"))
    
    # Check role changes
    if data.role_shift_severity == "major":
        triggers.append(_get_caution("role_shift_major"))
    elif data.role_shift_severity == "minor" or data.role_shift_detected:
        triggers.append(_get_caution("role_shift_minor"))
    
    if data.assist_rate_trending_up:
        triggers.append(_get_caution("facilitator_increase"))
    
    # Check team context
    if data.star_player_out:
        triggers.append(_get_caution("star_player_out"))
    elif data.key_teammate_out:
        triggers.append(_get_caution("teammate_out"))
    
    if data.is_back_to_back:
        triggers.append(_get_caution("back_to_back"))
    
    # Check matchup
    if data.blowout_risk:
        triggers.append(_get_caution("blowout_risk"))
    
    if data.pace_down_matchup:
        triggers.append(_get_caution("pace_down"))
    
    if data.elite_defender_matchup:
        triggers.append(_get_caution("strong_defender"))
    
    # Check location
    if data.is_road:
        triggers.append(_get_caution("road_game"))
    
    return _build_caution_result(triggers)


def detect_team_cautions(data: TeamCautionData) -> CautionResult:
    """
    Detect cautions for team bets (ML, spread, total).
    
    RULE: Cautions must always appear when triggered.
    """
    triggers = []
    
    # Check roster
    if data.star_player_out:
        triggers.append(_get_caution("star_player_out"))
    elif data.key_player_out:
        triggers.append(_get_caution("teammate_out"))
    
    # Check schedule
    if data.is_back_to_back:
        triggers.append(_get_caution("back_to_back"))
    
    if data.is_road:
        triggers.append(_get_caution("road_game"))
    
    # Check line
    if data.is_large_spread or data.spread_size >= 10:
        triggers.append(_get_caution("large_spread"))
    
    # Check matchup
    if data.blowout_risk:
        triggers.append(_get_caution("blowout_risk"))
    
    return _build_caution_result(triggers)


def detect_spread_cautions(
    spread_size: float,
    cover_margin: float,
    is_road: bool = False,
    back_to_back: bool = False
) -> CautionResult:
    """
    Detect cautions specific to spread bets.
    """
    triggers = []
    
    if abs(spread_size) >= 10:
        triggers.append(_get_caution("large_spread"))
    
    if abs(cover_margin) < 2:
        triggers.append(_get_caution("thin_margin"))
    
    if is_road:
        triggers.append(_get_caution("road_game"))
    
    if back_to_back:
        triggers.append(_get_caution("back_to_back"))
    
    return _build_caution_result(triggers)


def detect_alt_line_cautions(
    is_alt_line: bool,
    hit_rate_variance: float = 0.0
) -> CautionResult:
    """
    Detect cautions for alt line picks.
    """
    triggers = []
    
    if is_alt_line and hit_rate_variance > 0.15:
        triggers.append(_get_caution("alt_line_volatility"))
    
    return _build_caution_result(triggers)


# ============================================
# HELPER FUNCTIONS
# ============================================

def _get_caution(key: str) -> Caution:
    """Get caution object from key."""
    if key not in CAUTION_TRIGGERS:
        return Caution(key=key, level=1, message=f"Unknown caution: {key}")
    
    trigger = CAUTION_TRIGGERS[key]
    return Caution(
        key=key,
        level=trigger["level"],
        message=trigger["message"]
    )


def _build_caution_result(triggers: List[Caution]) -> CautionResult:
    """
    Build caution result from triggers.
    
    RULE: 
    - 0 triggers = NONE
    - 1 trigger of level 1 = MILD
    - 2+ triggers OR any level 2 = HIGH
    - Level 3 = EXCLUDED
    """
    if not triggers:
        return CautionResult(
            level=CautionLevel.NONE,
            icon="",
            triggers=[],
            messages=[],
            should_exclude=False,
            total_severity=0
        )
    
    # Calculate total severity
    total_severity = sum(t.level for t in triggers)
    
    # Check for exclusion
    if any(t.level >= 3 for t in triggers):
        return CautionResult(
            level=CautionLevel.EXCLUDED,
            icon=CAUTION_ICONS[CautionLevel.EXCLUDED],
            triggers=triggers,
            messages=[t.message for t in triggers],
            should_exclude=True,
            total_severity=total_severity
        )
    
    # Determine level
    if total_severity >= 3 or any(t.level >= 2 for t in triggers):
        level = CautionLevel.HIGH
    elif total_severity >= 1:
        level = CautionLevel.MILD
    else:
        level = CautionLevel.NONE
    
    return CautionResult(
        level=level,
        icon=CAUTION_ICONS[level],
        triggers=triggers,
        messages=[t.message for t in triggers],
        should_exclude=False,
        total_severity=total_severity
    )


# ============================================
# FORMATTING FUNCTIONS
# ============================================

def format_caution_block(result: CautionResult) -> str:
    """
    Format caution block for Discord display.
    
    Output:
    ⚠️ CAUTION:
    • Listed as Questionable
    • Minutes dropped in last game
    """
    if result.level == CautionLevel.NONE or not result.messages:
        return ""
    
    lines = [f"{result.icon} CAUTION:"]
    for msg in result.messages:
        lines.append(f"• {msg}")
    
    return "\n".join(lines)


def format_caution_inline(result: CautionResult) -> str:
    """
    Format caution for inline display.
    
    Output: "⚠️⚠️ Questionable, Minutes volatility"
    """
    if result.level == CautionLevel.NONE or not result.messages:
        return ""
    
    short_messages = result.messages[:3]  # Max 3 for inline
    return f"{result.icon} {', '.join(short_messages)}"


def format_caution_flags(result: CautionResult) -> str:
    """
    Format caution flags section for Insights.
    
    Output:
    ⚠️ CAUTION FLAGS:
    • Questionable
    • Minutes drop detected
    """
    if result.level == CautionLevel.NONE or not result.messages:
        return ""
    
    lines = [f"{result.icon} CAUTION FLAGS:"]
    for msg in result.messages:
        lines.append(f"• {msg}")
    
    return "\n".join(lines)


def get_caution_header(result: CautionResult) -> str:
    """
    Get caution header for risk section.
    
    Returns: "⚠️ WHY THERE IS CAUTION:" or empty string
    """
    if result.level == CautionLevel.NONE:
        return ""
    
    return f"{result.icon} WHY THERE IS CAUTION:"


def has_cautions(result: CautionResult) -> bool:
    """Check if any cautions exist."""
    return result.level != CautionLevel.NONE


def get_caution_count(result: CautionResult) -> int:
    """Get number of caution triggers."""
    return len(result.triggers)


# ============================================
# QUICK DETECTION (SIMPLIFIED)
# ============================================

def quick_player_caution(
    is_questionable: bool = False,
    minutes_below_avg: bool = False,
    teammate_out: bool = False,
    is_road: bool = False
) -> CautionResult:
    """
    Quick caution detection with minimal inputs.
    """
    data = PlayerCautionData(
        injury_status="questionable" if is_questionable else None,
        low_minute_game_count=1 if minutes_below_avg else 0,
        key_teammate_out=teammate_out,
        is_road=is_road
    )
    return detect_player_cautions(data)


def quick_team_caution(
    star_out: bool = False,
    large_spread: bool = False,
    is_road: bool = False
) -> CautionResult:
    """
    Quick caution detection for team bets.
    """
    data = TeamCautionData(
        star_player_out=star_out,
        is_large_spread=large_spread,
        is_road=is_road
    )
    return detect_team_cautions(data)
