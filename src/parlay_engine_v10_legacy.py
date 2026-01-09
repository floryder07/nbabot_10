V11_SIGNATURE = "parlay-engine-v10-legacy"

def _assert_v11():
    return V11_SIGNATURE
"""
NBABot v10.0 Parlay Engine (FIXED)

Core logic for generating rule-based parlays with realistic odds.
"""

import random
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict

from eligibility import check_eligibility, calculate_hit_rate_percentage
from api_client import api_client
from config import (
    DEFAULT_LADDER, MIN_LEGS, MAX_LEGS, 
    PROP_TYPES, LEG_TYPES, VALID_LADDERS
)


@dataclass
class HitRate:
    """Hit rate data structure."""
    hits: int
    games: int
    ladder: int
    percentage: float = 0.0
    
    def __post_init__(self):
        self.percentage = calculate_hit_rate_percentage(self.hits, self.games)


@dataclass
class Selection:
    """Leg selection data structure."""
    label: str
    value: Optional[float] = None
    direction: Optional[str] = None
    player_name: Optional[str] = None
    player_id: Optional[str] = None
    team_name: Optional[str] = None
    team_id: Optional[str] = None
    prop_type: Optional[str] = None


@dataclass
class Odds:
    """Odds data structure with proper conversion."""
    american: int
    decimal: float = 0.0
    implied_probability: float = 0.0
    
    def __post_init__(self):
        self.decimal = self._american_to_decimal(self.american)
        self.implied_probability = self._calculate_implied_probability()
    
    def _american_to_decimal(self, american: int) -> float:
        """Convert American odds to decimal."""
        if american > 0:
            return round((american / 100) + 1, 3)
        else:
            return round((100 / abs(american)) + 1, 3)
    
    def _calculate_implied_probability(self) -> float:
        """Calculate implied probability from American odds."""
        if self.american > 0:
            return round(100 / (self.american + 100) * 100, 1)
        else:
            return round(abs(self.american) / (abs(self.american) + 100) * 100, 1)


@dataclass
class Matchup:
    """Game matchup data structure."""
    home_team: str
    away_team: str
    game_id: str
    game_date: Optional[str] = None
    game_time: Optional[str] = None


@dataclass
class H2HData:
    """Head-to-head data structure."""
    wins: int
    games: int
    window: str = "1_year"


@dataclass
class SpreadData:
    """Spread-specific data structure."""
    spread_value: float
    avg_margin: float
    cover_rate: Dict[str, int] = field(default_factory=dict)


@dataclass
class Leg:
    """Parlay leg data structure."""
    id: str
    type: str
    matchup: Matchup
    selection: Selection
    odds: Odds
    hit_rate: HitRate
    eligible: bool
    h2h: Optional[H2HData] = None
    spread_data: Optional[SpreadData] = None
    rejection_reason: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        return data


@dataclass
class Parlay:
    """Parlay data structure."""
    id: str
    legs: List[Leg]
    leg_count: int
    wager: float
    ladder: int
    total_odds: int
    total_odds_decimal: float
    potential_win: float
    created_at: str
    user_id: Optional[str] = None
    guild_id: Optional[str] = None
    channel_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "legs": [leg.to_dict() for leg in self.legs],
            "leg_count": self.leg_count,
            "wager": self.wager,
            "ladder": self.ladder,
            "total_odds": self.total_odds,
            "total_odds_decimal": self.total_odds_decimal,
            "potential_win": self.potential_win,
            "created_at": self.created_at,
            "user_id": self.user_id,
            "guild_id": self.guild_id,
            "channel_id": self.channel_id
        }


def generate_leg_id() -> str:
    """Generate unique leg ID."""
    return f"leg_{uuid.uuid4().hex[:8]}"


def generate_parlay_id() -> str:
    """Generate unique parlay ID."""
    return f"parlay_{uuid.uuid4().hex[:12]}"


class ParlayEngine:
    """
    Engine for generating rule-based parlays.
    """
    
    def __init__(self):
        self.api = api_client
        self._parlay_cache: Dict[str, Parlay] = {}
        self._leg_cache: Dict[str, Leg] = {}
    
    async def generate_parlay(
        self,
        legs_count: int,
        wager: float,
        ladder: int = DEFAULT_LADDER,
        user_id: str = None,
        guild_id: str = None,
        channel_id: str = None
    ) -> Optional[Parlay]:
        """
        Generate a new parlay.
        """
        # Validate inputs
        if not MIN_LEGS <= legs_count <= MAX_LEGS:
            return None
        if ladder not in VALID_LADDERS:
            ladder = DEFAULT_LADDER
        
        # Fetch today's games
        games = await self.api.get_games_today()
        if not games:
            return None
        
        # Generate candidate legs from all games
        candidates = []
        for game in games:
            game_legs = await self._generate_legs_for_game(game, ladder)
            candidates.extend(game_legs)
        
        # Filter to eligible legs only
        eligible_legs = [leg for leg in candidates if leg.eligible]
        
        if len(eligible_legs) < legs_count:
            return None
        
        # Select legs with variety
        selected_legs = self._select_varied_legs(eligible_legs, legs_count)
        
        # Calculate combined odds
        total_decimal = 1.0
        for leg in selected_legs:
            total_decimal *= leg.odds.decimal
        
        total_american = self._decimal_to_american(total_decimal)
        potential_win = round(wager * total_decimal, 2)
        
        # Create parlay
        parlay = Parlay(
            id=generate_parlay_id(),
            legs=selected_legs,
            leg_count=legs_count,
            wager=wager,
            ladder=ladder,
            total_odds=total_american,
            total_odds_decimal=round(total_decimal, 2),
            potential_win=potential_win,
            created_at=datetime.now().isoformat(),
            user_id=user_id,
            guild_id=guild_id,
            channel_id=channel_id
        )
        
        # Cache parlay and legs
        self._parlay_cache[parlay.id] = parlay
        for leg in selected_legs:
            self._leg_cache[leg.id] = leg
        
        return parlay
    
    async def _generate_legs_for_game(self, game: Dict, ladder: int) -> List[Leg]:
        """Generate all possible legs for a game."""
        legs = []
        
        home_team = game.get("teams", {}).get("home", {})
        away_team = game.get("teams", {}).get("away", {})
        game_id = str(game.get("id", ""))
        
        matchup = Matchup(
            home_team=home_team.get("name", "Unknown"),
            away_team=away_team.get("name", "Unknown"),
            game_id=game_id,
            game_date=game.get("date", "")[:10] if game.get("date") else "",
            game_time=game.get("time", "")
        )
        
        # Generate moneyline legs
        for team in [home_team, away_team]:
            ml_leg = await self._generate_moneyline_leg(team, home_team, away_team, matchup, ladder)
            if ml_leg:
                legs.append(ml_leg)
        
        # Generate spread legs
        for team in [home_team, away_team]:
            spread_leg = await self._generate_spread_leg(team, matchup, ladder)
            if spread_leg:
                legs.append(spread_leg)
        
        # Generate game total legs
        for direction in ["over", "under"]:
            total_leg = await self._generate_game_total_leg(home_team, away_team, matchup, direction, ladder)
            if total_leg:
                legs.append(total_leg)
        
        # Generate team total legs
        for team in [home_team, away_team]:
            for direction in ["over", "under"]:
                team_total_leg = await self._generate_team_total_leg(team, matchup, direction, ladder)
                if team_total_leg:
                    legs.append(team_total_leg)
        
        # Generate player prop legs
        for team in [home_team, away_team]:
            player_legs = await self._generate_player_prop_legs(team, matchup, ladder)
            legs.extend(player_legs)
        
        return legs
    
    async def _generate_moneyline_leg(
        self,
        team: Dict,
        home_team: Dict,
        away_team: Dict,
        matchup: Matchup,
        ladder: int
    ) -> Optional[Leg]:
        """Generate a moneyline leg."""
        team_id = team.get("id")
        team_name = team.get("name", "Unknown")
        
        recent_games = await self.api.get_team_games(team_id, limit=ladder)
        
        wins = 0
        for game in recent_games:
            result = self.api.parse_game_result(game, team_id)
            if result["won"]:
                wins += 1
        
        # Get H2H data
        opponent_id = away_team.get("id") if team_id == home_team.get("id") else home_team.get("id")
        h2h_games = await self.api.get_head_to_head(team_id, opponent_id)
        h2h_wins = sum(1 for g in h2h_games if self.api.parse_game_result(g, team_id)["won"])
        
        # Check eligibility
        is_eligible, rejection = check_eligibility(wins, ladder, ladder)
        
        # Generate REALISTIC odds
        odds_value = self._generate_realistic_odds("moneyline", wins, ladder)
        
        return Leg(
            id=generate_leg_id(),
            type="moneyline",
            matchup=matchup,
            selection=Selection(
                label=f"{team_name} ML",
                direction="win",
                team_name=team_name,
                team_id=str(team_id)
            ),
            odds=Odds(american=odds_value),
            hit_rate=HitRate(hits=wins, games=ladder, ladder=ladder),
            h2h=H2HData(wins=h2h_wins, games=len(h2h_games)) if h2h_games else None,
            eligible=is_eligible,
            rejection_reason=rejection
        )
    
    async def _generate_spread_leg(
        self,
        team: Dict,
        matchup: Matchup,
        ladder: int
    ) -> Optional[Leg]:
        """Generate a spread leg."""
        team_id = team.get("id")
        team_name = team.get("name", "Unknown")
        
        recent_games = await self.api.get_team_games(team_id, limit=ladder)
        
        margins = []
        for game in recent_games:
            result = self.api.parse_game_result(game, team_id)
            margins.append(result["margin"])
        
        avg_margin = sum(margins) / len(margins) if margins else 0
        
        # Generate spread
        spread_value = round(avg_margin * 0.7, 1)
        if spread_value > 0:
            spread_value = -spread_value
        
        # Count covers
        covers = 0
        for margin in margins:
            if spread_value < 0:
                if margin > abs(spread_value):
                    covers += 1
            else:
                if margin > -spread_value:
                    covers += 1
        
        is_eligible, rejection = check_eligibility(covers, ladder, ladder)
        odds_value = self._generate_realistic_odds("spread", covers, ladder)
        
        return Leg(
            id=generate_leg_id(),
            type="spread",
            matchup=matchup,
            selection=Selection(
                label=f"{team_name} {spread_value:+.1f}",
                value=spread_value,
                direction="cover",
                team_name=team_name,
                team_id=str(team_id)
            ),
            odds=Odds(american=odds_value),
            hit_rate=HitRate(hits=covers, games=ladder, ladder=ladder),
            spread_data=SpreadData(
                spread_value=spread_value,
                avg_margin=round(avg_margin, 1),
                cover_rate={"covers": covers, "games": ladder}
            ),
            eligible=is_eligible,
            rejection_reason=rejection
        )
    
    async def _generate_game_total_leg(
        self,
        home_team: Dict,
        away_team: Dict,
        matchup: Matchup,
        direction: str,
        ladder: int
    ) -> Optional[Leg]:
        """Generate a game total leg."""
        home_id = home_team.get("id")
        
        recent_games = await self.api.get_team_games(home_id, limit=ladder)
        
        totals = []
        for game in recent_games:
            result = self.api.parse_game_result(game, home_id)
            totals.append(result["total"])
        
        avg_total = sum(totals) / len(totals) if totals else 220
        
        if direction == "over":
            total_line = round(avg_total - 2, 1)
        else:
            total_line = round(avg_total + 2, 1)
        
        hits = 0
        for total in totals:
            if direction == "over" and total > total_line:
                hits += 1
            elif direction == "under" and total < total_line:
                hits += 1
        
        is_eligible, rejection = check_eligibility(hits, ladder, ladder)
        odds_value = self._generate_realistic_odds("total", hits, ladder)
        
        return Leg(
            id=generate_leg_id(),
            type="game_total",
            matchup=matchup,
            selection=Selection(
                label=f"Game Total {direction.title()} {total_line}",
                value=total_line,
                direction=direction
            ),
            odds=Odds(american=odds_value),
            hit_rate=HitRate(hits=hits, games=ladder, ladder=ladder),
            eligible=is_eligible,
            rejection_reason=rejection
        )
    
    async def _generate_team_total_leg(
        self,
        team: Dict,
        matchup: Matchup,
        direction: str,
        ladder: int
    ) -> Optional[Leg]:
        """Generate a team total leg."""
        team_id = team.get("id")
        team_name = team.get("name", "Unknown")
        
        recent_games = await self.api.get_team_games(team_id, limit=ladder)
        
        scores = []
        for game in recent_games:
            result = self.api.parse_game_result(game, team_id)
            scores.append(result["team_score"])
        
        avg_score = sum(scores) / len(scores) if scores else 110
        
        if direction == "over":
            total_line = round(avg_score - 1.5, 1)
        else:
            total_line = round(avg_score + 1.5, 1)
        
        hits = 0
        for score in scores:
            if direction == "over" and score > total_line:
                hits += 1
            elif direction == "under" and score < total_line:
                hits += 1
        
        is_eligible, rejection = check_eligibility(hits, ladder, ladder)
        odds_value = self._generate_realistic_odds("total", hits, ladder)
        
        return Leg(
            id=generate_leg_id(),
            type="team_total",
            matchup=matchup,
            selection=Selection(
                label=f"{team_name} Team Total {direction.title()} {total_line}",
                value=total_line,
                direction=direction,
                team_name=team_name,
                team_id=str(team_id)
            ),
            odds=Odds(american=odds_value),
            hit_rate=HitRate(hits=hits, games=ladder, ladder=ladder),
            eligible=is_eligible,
            rejection_reason=rejection
        )
    
    async def _generate_player_prop_legs(
        self,
        team: Dict,
        matchup: Matchup,
        ladder: int
    ) -> List[Leg]:
        """Generate player prop legs."""
        legs = []
        team_id = team.get("id")
        
        players = await self.api.get_players_by_team(team_id)
        top_players = players[:3] if players else []
        
        for player in top_players:
            player_id = player.get("id")
            player_name = f"{player.get('firstname', '')} {player.get('lastname', '')}".strip()
            
            if not player_name:
                continue
            
            stats = await self.api.get_player_stats(player_id, limit=ladder)
            
            if not stats:
                continue
            
            # Points prop
            points = [s.get("points", 0) or 0 for s in stats]
            if points:
                avg_points = sum(points) / len(points)
                line = round(avg_points - 1.5, 1)
                hits = sum(1 for p in points if p > line)
                
                is_eligible, rejection = check_eligibility(hits, ladder, ladder)
                odds_value = self._generate_realistic_odds("prop", hits, ladder)
                
                legs.append(Leg(
                    id=generate_leg_id(),
                    type="player_prop",
                    matchup=matchup,
                    selection=Selection(
                        label=f"{player_name} Over {line} Points",
                        value=line,
                        direction="over",
                        player_name=player_name,
                        player_id=str(player_id),
                        prop_type="points"
                    ),
                    odds=Odds(american=odds_value),
                    hit_rate=HitRate(hits=hits, games=len(points), ladder=ladder),
                    eligible=is_eligible,
                    rejection_reason=rejection
                ))
        
        return legs
    
    def _select_varied_legs(self, eligible_legs: List[Leg], count: int) -> List[Leg]:
        """Select legs with variety."""
        if len(eligible_legs) <= count:
            return eligible_legs[:count]
        
        selected = []
        types_used = set()
        games_used = set()
        
        shuffled = eligible_legs.copy()
        random.shuffle(shuffled)
        
        for leg in shuffled:
            if len(selected) >= count:
                break
            if leg.type not in types_used or leg.matchup.game_id not in games_used:
                selected.append(leg)
                types_used.add(leg.type)
                games_used.add(leg.matchup.game_id)
        
        for leg in shuffled:
            if len(selected) >= count:
                break
            if leg not in selected:
                selected.append(leg)
        
        return selected[:count]
    
    def _decimal_to_american(self, decimal: float) -> int:
        """Convert decimal odds to American."""
        if decimal >= 2.0:
            return round((decimal - 1) * 100)
        else:
            return round(-100 / (decimal - 1))
    
    def _generate_realistic_odds(self, bet_type: str, hits: int, games: int) -> int:
        """
        Generate REALISTIC American odds based on bet type and hit rate.
        
        Typical NBA odds ranges:
        - Moneyline favorites: -300 to -110
        - Moneyline underdogs: +110 to +300
        - Spreads/Totals: -115 to -105 (standard juice)
        - Player props: -130 to +130
        """
        hit_rate = hits / games if games > 0 else 0.5
        
        if bet_type == "moneyline":
            # Moneyline odds vary more based on matchup
            if hit_rate >= 0.8:
                return random.randint(-200, -140)
            elif hit_rate >= 0.6:
                return random.randint(-140, +110)
            else:
                return random.randint(+110, +180)
        
        elif bet_type == "spread":
            # Spreads typically have standard juice around -110
            base = -110
            variance = random.randint(-5, 5)
            return base + variance
        
        elif bet_type == "total":
            # Totals also have standard juice
            base = -110
            variance = random.randint(-5, 5)
            return base + variance
        
        elif bet_type == "prop":
            # Player props have wider variance
            if hit_rate >= 0.8:
                return random.randint(-135, -115)
            elif hit_rate >= 0.6:
                return random.randint(-120, +105)
            else:
                return random.randint(+100, +130)
        
        else:
            # Default
            return -110
    
    def get_parlay(self, parlay_id: str) -> Optional[Parlay]:
        """Get parlay from cache."""
        return self._parlay_cache.get(parlay_id)
    
    def get_leg(self, leg_id: str) -> Optional[Leg]:
        """Get leg from cache."""
        return self._leg_cache.get(leg_id)


# Global engine instance
parlay_engine = ParlayEngine()
