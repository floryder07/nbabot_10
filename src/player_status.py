import os

if os.getenv("NBABOT_VERSION") not in (None, "11"):
    raise RuntimeError(
        "❌ player_status_engine_v11 imported outside v11 context"
    )
"""
NBABot v11 — Player Status Engine
LOCKED v11 MODULE — DO NOT USE IN LEGACY CONTEXT
"""

V11_PLAYER_STATUS_SIGNATURE = "NBABOT_V11_PLAYER_STATUS"

def _assert_v11():
    return V11_PLAYER_STATUS_SIGNATURE

"""
ADDED FOR: Player Status & Minutes Filter
DOES NOT MODIFY EXISTING LOGIC

Core Rules (LOCKED):
- Prevent picks when player is not fully active
- Minutes volatility increases risk
- Role uncertainty affects confidence
- <75% avg minutes = low minutes
- 3 straight low-minute games → EXCLUDE
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from statistics import mean, median


# ============================================
# CONSTANTS (LOCKED — DO NOT MODIFY)
# ============================================

# Minutes thresholds
LOW_MINUTES_THRESHOLD = 0.75  # <75% of avg = low minutes
EXCLUDE_LOW_MINUTE_STREAK = 3  # 3 straight low-minute games → exclude

# Status levels
class PlayerStatus(Enum):
    """Player availability status."""
    ACTIVE = "active"
    PROBABLE = "probable"
    QUESTIONABLE = "questionable"
    DOUBTFUL = "doubtful"
    OUT = "out"
    SUSPENDED = "suspended"
    UNKNOWN = "unknown"


# Status impact on eligibility
STATUS_ELIGIBILITY = {
    PlayerStatus.ACTIVE: True,
    PlayerStatus.PROBABLE: True,
    PlayerStatus.QUESTIONABLE: True,  # Include with caution
    PlayerStatus.DOUBTFUL: False,     # Exclude
    PlayerStatus.OUT: False,          # Exclude
    PlayerStatus.SUSPENDED: False,    # Exclude
    PlayerStatus.UNKNOWN: True,       # Include with caution
}

# Status impact on confidence
STATUS_CONFIDENCE_MODIFIER = {
    PlayerStatus.ACTIVE: 0,
    PlayerStatus.PROBABLE: -2,
    PlayerStatus.QUESTIONABLE: -6,
    PlayerStatus.DOUBTFUL: -15,
    PlayerStatus.OUT: -100,
    PlayerStatus.SUSPENDED: -100,
    PlayerStatus.UNKNOWN: -3,
}


# ============================================
# DATA STRUCTURES
# ============================================

@dataclass
class MinutesData:
    """Minutes data for a player."""
    minutes_last_15: List[float]  # Most recent first
    season_average: float
    last_game_minutes: float
    
    @property
    def minutes_last_5(self) -> List[float]:
        return self.minutes_last_15[:5]
    
    @property
    def minutes_last_10(self) -> List[float]:
        return self.minutes_last_15[:10]
    
    @property
    def avg_last_5(self) -> float:
        return mean(self.minutes_last_5) if self.minutes_last_5 else 0
    
    @property
    def avg_last_10(self) -> float:
        return mean(self.minutes_last_10) if self.minutes_last_10 else 0
    
    @property
    def avg_last_15(self) -> float:
        return mean(self.minutes_last_15) if self.minutes_last_15 else 0


@dataclass
class PlayerStatusData:
    """Complete player status data."""
    player_id: str
    player_name: str
    team: str
    
    # Availability
    injury_status: PlayerStatus
    injury_note: Optional[str] = None
    is_game_time_decision: bool = False
    
    # Minutes
    minutes_data: Optional[MinutesData] = None
    
    # Role
    role: str = "starter"  # 'starter', 'rotation', 'bench', 'unknown'
    usage_rate: Optional[float] = None
    usage_trending: str = "stable"  # 'up', 'down', 'stable'


@dataclass
class PlayerEligibilityResult:
    """Result of player eligibility check."""
    is_eligible: bool
    reason: Optional[str]
    confidence_modifier: int
    warnings: List[str]
    low_minute_games: int
    minutes_stable: bool
    role_clear: bool


@dataclass
class MinutesAnalysis:
    """Analysis of player minutes patterns."""
    avg_minutes: float
    median_minutes: float
    low_minute_game_count: int
    low_minute_streak: int
    is_minutes_stable: bool
    recent_trend: str  # 'up', 'down', 'stable'
    flags: List[str]


# ============================================
# CORE FUNCTIONS
# ============================================

def parse_injury_status(status_string: Optional[str]) -> PlayerStatus:
    """
    Parse injury status string to enum.
    
    Handles various formats from different APIs.
    """
    if not status_string:
        return PlayerStatus.ACTIVE
    
    status_lower = status_string.lower().strip()
    
    if status_lower in ["active", "available", "healthy", ""]:
        return PlayerStatus.ACTIVE
    elif status_lower in ["probable", "likely"]:
        return PlayerStatus.PROBABLE
    elif status_lower in ["questionable", "uncertain", "gtd", "game-time decision"]:
        return PlayerStatus.QUESTIONABLE
    elif status_lower in ["doubtful", "unlikely"]:
        return PlayerStatus.DOUBTFUL
    elif status_lower in ["out", "injured", "dnp", "did not play"]:
        return PlayerStatus.OUT
    elif status_lower in ["suspended", "suspension"]:
        return PlayerStatus.SUSPENDED
    else:
        return PlayerStatus.UNKNOWN


def check_player_eligibility(data: PlayerStatusData) -> PlayerEligibilityResult:
    """
    Check if player is eligible for picks.
    
    RULES:
    - OUT/DOUBTFUL/SUSPENDED → EXCLUDE
    - 3 straight low-minute games → EXCLUDE
    - QUESTIONABLE → Include with caution
    """
    warnings = []
    
    # Check injury status
    if not STATUS_ELIGIBILITY.get(data.injury_status, False):
        return PlayerEligibilityResult(
            is_eligible=False,
            reason=f"Player status: {data.injury_status.value}",
            confidence_modifier=STATUS_CONFIDENCE_MODIFIER.get(data.injury_status, 0),
            warnings=[],
            low_minute_games=0,
            minutes_stable=False,
            role_clear=False
        )
    
    # Check minutes data
    low_minute_games = 0
    minutes_stable = True
    low_minute_streak = 0
    
    if data.minutes_data:
        analysis = analyze_minutes(data.minutes_data)
        low_minute_games = analysis.low_minute_game_count
        minutes_stable = analysis.is_minutes_stable
        low_minute_streak = analysis.low_minute_streak
        warnings.extend(analysis.flags)
        
        # RULE: 3 straight low-minute games → EXCLUDE
        if low_minute_streak >= EXCLUDE_LOW_MINUTE_STREAK:
            return PlayerEligibilityResult(
                is_eligible=False,
                reason=f"{low_minute_streak} consecutive low-minute games",
                confidence_modifier=-20,
                warnings=warnings,
                low_minute_games=low_minute_games,
                minutes_stable=False,
                role_clear=False
            )
    
    # Check role clarity
    role_clear = data.role in ["starter", "rotation"]
    if not role_clear:
        warnings.append("Role uncertainty detected")
    
    # Add status warning if questionable
    if data.injury_status == PlayerStatus.QUESTIONABLE:
        warnings.append("Listed as Questionable")
    
    if data.is_game_time_decision:
        warnings.append("Game-time decision")
    
    # Calculate confidence modifier
    confidence_mod = STATUS_CONFIDENCE_MODIFIER.get(data.injury_status, 0)
    if not minutes_stable:
        confidence_mod -= 5
    if not role_clear:
        confidence_mod -= 3
    
    return PlayerEligibilityResult(
        is_eligible=True,
        reason=None,
        confidence_modifier=confidence_mod,
        warnings=warnings,
        low_minute_games=low_minute_games,
        minutes_stable=minutes_stable,
        role_clear=role_clear
    )


def analyze_minutes(data: MinutesData) -> MinutesAnalysis:
    """
    Analyze player minutes patterns.
    
    RULES:
    - <75% avg minutes = low minutes
    - Track consecutive low-minute games
    - Detect trends
    """
    if not data.minutes_last_15:
        return MinutesAnalysis(
            avg_minutes=0,
            median_minutes=0,
            low_minute_game_count=0,
            low_minute_streak=0,
            is_minutes_stable=False,
            recent_trend="unknown",
            flags=["No minutes data available"]
        )
    
    avg_minutes = data.avg_last_15
    median_minutes = median(data.minutes_last_15)
    low_threshold = data.season_average * LOW_MINUTES_THRESHOLD
    
    # Count low-minute games
    low_minute_games = []
    for i, mins in enumerate(data.minutes_last_15):
        if mins < low_threshold:
            low_minute_games.append(i)
    
    low_minute_count = len(low_minute_games)
    
    # Calculate consecutive low-minute streak (from most recent)
    low_minute_streak = 0
    for i, mins in enumerate(data.minutes_last_15):
        if mins < low_threshold:
            low_minute_streak += 1
        else:
            break
    
    # Check stability (low variance in recent games)
    recent_5 = data.minutes_last_5
    if len(recent_5) >= 5:
        minutes_range = max(recent_5) - min(recent_5)
        is_stable = minutes_range <= 8  # Within 8 minutes range
    else:
        is_stable = True
    
    # Detect trend
    if len(data.minutes_last_15) >= 10:
        first_half = mean(data.minutes_last_15[5:10])
        second_half = mean(data.minutes_last_15[0:5])
        
        if second_half > first_half + 2:
            trend = "up"
        elif second_half < first_half - 2:
            trend = "down"
        else:
            trend = "stable"
    else:
        trend = "stable"
    
    # Build flags
    flags = []
    if low_minute_count >= 2:
        flags.append(f"Minutes volatility detected ({low_minute_count} low games)")
    elif low_minute_count == 1:
        flags.append("1 low-minute game in sample")
    
    if low_minute_streak >= 2:
        flags.append(f"{low_minute_streak} consecutive low-minute games")
    
    if trend == "down":
        flags.append("Minutes trending downward")
    
    if not is_stable:
        flags.append("Minutes not stable (high variance)")
    
    return MinutesAnalysis(
        avg_minutes=round(avg_minutes, 1),
        median_minutes=round(median_minutes, 1),
        low_minute_game_count=low_minute_count,
        low_minute_streak=low_minute_streak,
        is_minutes_stable=is_stable and low_minute_streak < 2,
        recent_trend=trend,
        flags=flags
    )


def get_minutes_display(data: MinutesData) -> Dict[str, str]:
    """
    Get minutes data formatted for display.
    
    Returns dict for embed fields.
    """
    if not data.minutes_last_15:
        return {"Average Minutes": "N/A", "Low-Minute Games": "N/A"}
    
    analysis = analyze_minutes(data)
    
    return {
        "Average Minutes": f"{analysis.avg_minutes}",
        "Low-Minute Games": str(analysis.low_minute_game_count),
        "Minutes Trend": analysis.recent_trend.title()
    }


# ============================================
# ROLE DETECTION
# ============================================

@dataclass
class RoleAnalysis:
    """Analysis of player role changes."""
    current_role: str
    role_stable: bool
    role_shift_detected: bool
    shift_type: Optional[str]  # 'facilitator_up', 'scorer_down', etc.
    warnings: List[str]


def analyze_role(
    assist_rates: List[float],
    usage_rates: List[float],
    position: str = "guard"
) -> RoleAnalysis:
    """
    Analyze player role changes.
    
    Detects shifts like:
    - Increased facilitation (assist rate up)
    - Decreased scoring volume
    - Role uncertainty
    """
    warnings = []
    role_shift = False
    shift_type = None
    
    if len(assist_rates) >= 5 and len(usage_rates) >= 5:
        # Check assist rate trend
        recent_ast = mean(assist_rates[:3])
        older_ast = mean(assist_rates[3:])
        
        if recent_ast > older_ast * 1.15:  # 15% increase
            role_shift = True
            shift_type = "facilitator_up"
            warnings.append("Assist rate increased (may reduce scoring)")
        
        # Check usage rate trend
        recent_usg = mean(usage_rates[:3])
        older_usg = mean(usage_rates[3:])
        
        if recent_usg < older_usg * 0.85:  # 15% decrease
            role_shift = True
            shift_type = "usage_down"
            warnings.append("Usage rate decreased")
    
    # Determine current role
    if usage_rates and mean(usage_rates[:3]) > 25:
        current_role = "primary_option"
    elif usage_rates and mean(usage_rates[:3]) > 20:
        current_role = "secondary_option"
    else:
        current_role = "role_player"
    
    return RoleAnalysis(
        current_role=current_role,
        role_stable=not role_shift,
        role_shift_detected=role_shift,
        shift_type=shift_type,
        warnings=warnings
    )


# ============================================
# QUICK CHECKS (SIMPLIFIED)
# ============================================

def is_player_available(status_string: Optional[str]) -> bool:
    """Quick check if player is available."""
    status = parse_injury_status(status_string)
    return STATUS_ELIGIBILITY.get(status, False)


def get_status_modifier(status_string: Optional[str]) -> int:
    """Get confidence modifier for status."""
    status = parse_injury_status(status_string)
    return STATUS_CONFIDENCE_MODIFIER.get(status, 0)


def check_minutes_filter(
    minutes_list: List[float],
    season_avg: float
) -> Tuple[bool, int, List[str]]:
    """
    Quick minutes filter check.
    
    Returns:
        (passes_filter, low_minute_count, warnings)
    """
    if not minutes_list:
        return (True, 0, [])
    
    data = MinutesData(
        minutes_last_15=minutes_list,
        season_average=season_avg,
        last_game_minutes=minutes_list[0] if minutes_list else 0
    )
    
    analysis = analyze_minutes(data)
    
    # RULE: 3 straight low-minute games → EXCLUDE
    passes = analysis.low_minute_streak < EXCLUDE_LOW_MINUTE_STREAK
    
    return (passes, analysis.low_minute_game_count, analysis.flags)


# ============================================
# FORMATTING FUNCTIONS
# ============================================

def format_status_display(status: PlayerStatus) -> str:
    """Format player status for Discord display."""
    status_icons = {
        PlayerStatus.ACTIVE: "✅",
        PlayerStatus.PROBABLE: "🟢",
        PlayerStatus.QUESTIONABLE: "🟡",
        PlayerStatus.DOUBTFUL: "🟠",
        PlayerStatus.OUT: "🔴",
        PlayerStatus.SUSPENDED: "⛔",
        PlayerStatus.UNKNOWN: "❓",
    }
    
    icon = status_icons.get(status, "❓")
    return f"{icon} {status.value.title()}"


def format_minutes_for_insights(data: MinutesData) -> str:
    """
    Format minutes section for Insights output.
    
    Output:
    MINUTES
    Average Minutes: 36.8
    Low-Minute Games: 0
    """
    if not data.minutes_last_15:
        return "MINUTES\nNo data available"
    
    analysis = analyze_minutes(data)
    
    lines = [
        "MINUTES",
        f"Average Minutes: {analysis.avg_minutes}",
        f"Low-Minute Games: {analysis.low_minute_game_count}"
    ]
    
    return "\n".join(lines)


# ============================================
# PUBLIC v11 API (DO NOT BYPASS)
# ============================================

def evaluate_player_status(data: PlayerStatusData) -> PlayerEligibilityResult:
    """
    PUBLIC ENTRY POINT — v11 ONLY

    All eligibility, minutes, and role rules enforced here.
    """
    _assert_v11()
    return check_player_eligibility(data)


def analyze_player_minutes(data: MinutesData) -> MinutesAnalysis:
    """
    PUBLIC ENTRY POINT — Minutes analysis (v11 safe)
    """
    _assert_v11()
    return analyze_minutes(data)
