"""
NBABot v10.1.0 — Odds API Client

NEW MODULE: Fetches odds and alt lines from The Odds API.
https://the-odds-api.com/

This provides:
- Main lines (moneyline, spread, totals)
- Alt lines (alt spreads, alt totals, player props)
- Live odds from multiple bookmakers
"""

import aiohttp
from datetime import datetime
from typing import Optional, List, Dict, Any
from config import (
    ODDS_API_KEY, 
    ODDS_API_BASE_URL, 
    ODDS_API_SPORT,
    ODDS_API_REGIONS,
    ODDS_API_MARKETS,
    MOCK_MODE
)


# Mock data for testing
MOCK_ODDS = {
    "spreads": [-1.5, -3.5, -5.5, -7.5, -9.5],
    "totals": [210.5, 215.5, 220.5, 225.5, 230.5],
    "player_points": [15.5, 18.5, 20.5, 22.5, 24.5, 26.5, 28.5, 30.5],
    "player_rebounds": [4.5, 6.5, 8.5, 10.5, 12.5],
    "player_assists": [2.5, 4.5, 6.5, 8.5, 10.5]
}


class OddsAPIClient:
    """
    Async client for The Odds API.
    Provides main lines, alt lines, and player props.
    """
    
    def __init__(self):
        self.base_url = ODDS_API_BASE_URL
        self.api_key = ODDS_API_KEY
        self.sport = ODDS_API_SPORT
        self.session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self.cache_ttl = 300  # 5 minutes
        self.requests_remaining = None
        self.requests_used = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid."""
        if cache_key not in self._cache_timestamps:
            return False
        age = (datetime.now() - self._cache_timestamps[cache_key]).total_seconds()
        return age < self.cache_ttl
    
    async def _request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Make API request with caching.
        """
        if MOCK_MODE:
            return {"mock": True}
        
        if not self.api_key:
            return {"error": "ODDS_API_KEY not configured"}
        
        params = params or {}
        params["apiKey"] = self.api_key
        
        cache_key = f"{endpoint}_{str(params)}"
        
        # Check cache
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        # Make request
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint}"
        
        async with session.get(url, params=params) as response:
            # Track rate limits from headers
            self.requests_remaining = response.headers.get("x-requests-remaining")
            self.requests_used = response.headers.get("x-requests-used")
            
            data = await response.json()
            
            # Cache response
            self._cache[cache_key] = data
            self._cache_timestamps[cache_key] = datetime.now()
            
            return data
    
    # ==================== MAIN METHODS ====================
    
    async def get_nba_odds(self, markets: str = "h2h,spreads,totals") -> List[Dict]:
        """
        Get odds for all NBA games.
        
        Args:
            markets: Comma-separated markets (h2h, spreads, totals)
        
        Returns:
            List of game odds objects
        """
        if MOCK_MODE:
            return self._get_mock_games()
        
        params = {
            "regions": ODDS_API_REGIONS,
            "markets": markets,
            "oddsFormat": "american"
        }
        
        data = await self._request(f"sports/{self.sport}/odds", params)
        return data if isinstance(data, list) else []
    
    async def get_game_odds(self, game_id: str) -> Dict:
        """
        Get odds for a specific game.
        
        Args:
            game_id: The Odds API game ID
        
        Returns:
            Game odds object
        """
        if MOCK_MODE:
            return self._get_mock_game_odds()
        
        params = {
            "regions": ODDS_API_REGIONS,
            "markets": ODDS_API_MARKETS,
            "oddsFormat": "american"
        }
        
        data = await self._request(f"sports/{self.sport}/events/{game_id}/odds", params)
        return data
    
    async def get_player_props(self, game_id: str = None) -> List[Dict]:
        """
        Get player prop odds.
        
        Args:
            game_id: Optional game ID to filter
        
        Returns:
            List of player prop odds
        """
        if MOCK_MODE:
            return self._get_mock_player_props()
        
        params = {
            "regions": ODDS_API_REGIONS,
            "markets": "player_points,player_rebounds,player_assists,player_threes",
            "oddsFormat": "american"
        }
        
        if game_id:
            endpoint = f"sports/{self.sport}/events/{game_id}/odds"
        else:
            endpoint = f"sports/{self.sport}/odds"
        
        data = await self._request(endpoint, params)
        return data if isinstance(data, list) else []
    
    # ==================== ALT LINES ====================
    
    async def get_alt_spreads(self, game_id: str = None) -> List[float]:
        """
        Get available alt spread lines.
        
        Returns:
            List of alt spread values (e.g., [-1.5, -3.5, -5.5, ...])
        """
        if MOCK_MODE:
            return MOCK_ODDS["spreads"]
        
        odds = await self.get_game_odds(game_id) if game_id else await self.get_nba_odds("spreads")
        
        alt_lines = set()
        
        # Extract unique spread values from all bookmakers
        if isinstance(odds, list):
            for game in odds:
                for bookmaker in game.get("bookmakers", []):
                    for market in bookmaker.get("markets", []):
                        if market.get("key") == "spreads":
                            for outcome in market.get("outcomes", []):
                                point = outcome.get("point")
                                if point is not None:
                                    alt_lines.add(point)
        
        return sorted(list(alt_lines))
    
    async def get_alt_totals(self, game_id: str = None) -> List[float]:
        """
        Get available alt total lines.
        
        Returns:
            List of alt total values (e.g., [215.5, 220.5, 225.5, ...])
        """
        if MOCK_MODE:
            return MOCK_ODDS["totals"]
        
        odds = await self.get_game_odds(game_id) if game_id else await self.get_nba_odds("totals")
        
        alt_lines = set()
        
        if isinstance(odds, list):
            for game in odds:
                for bookmaker in game.get("bookmakers", []):
                    for market in bookmaker.get("markets", []):
                        if market.get("key") == "totals":
                            for outcome in market.get("outcomes", []):
                                point = outcome.get("point")
                                if point is not None:
                                    alt_lines.add(point)
        
        return sorted(list(alt_lines))
    
    async def get_player_prop_lines(self, prop_type: str = "points") -> List[float]:
        """
        Get available player prop lines.
        
        Args:
            prop_type: 'points', 'rebounds', 'assists', 'threes'
        
        Returns:
            List of available lines
        """
        if MOCK_MODE:
            mock_key = f"player_{prop_type}"
            return MOCK_ODDS.get(mock_key, [20.5, 22.5, 24.5, 26.5])
        
        market_key = f"player_{prop_type}"
        odds = await self.get_player_props()
        
        lines = set()
        
        if isinstance(odds, list):
            for game in odds:
                for bookmaker in game.get("bookmakers", []):
                    for market in bookmaker.get("markets", []):
                        if market.get("key") == market_key:
                            for outcome in market.get("outcomes", []):
                                point = outcome.get("point")
                                if point is not None:
                                    lines.add(point)
        
        return sorted(list(lines))
    
    # ==================== ODDS LOOKUP ====================
    
    async def get_best_odds(
        self, 
        game_id: str, 
        market: str, 
        selection: str,
        line: float = None
    ) -> Dict:
        """
        Get best available odds for a specific bet.
        
        Args:
            game_id: Game ID
            market: 'h2h', 'spreads', 'totals', 'player_points', etc.
            selection: Team name or player name
            line: Line value (for spreads/totals)
        
        Returns:
            Dict with best odds and bookmaker
        """
        if MOCK_MODE:
            return {"american": -110, "decimal": 1.91, "bookmaker": "mock"}
        
        odds = await self.get_game_odds(game_id)
        
        best = {"american": -110, "decimal": 1.91, "bookmaker": "average"}
        
        if not odds or not isinstance(odds, dict):
            return best
        
        for bookmaker in odds.get("bookmakers", []):
            for mkt in bookmaker.get("markets", []):
                if mkt.get("key") == market:
                    for outcome in mkt.get("outcomes", []):
                        if selection.lower() in outcome.get("name", "").lower():
                            if line is None or outcome.get("point") == line:
                                price = outcome.get("price", -110)
                                if price > best["american"]:
                                    best = {
                                        "american": price,
                                        "decimal": self._american_to_decimal(price),
                                        "bookmaker": bookmaker.get("title", "unknown")
                                    }
        
        return best
    
    # ==================== HELPERS ====================
    
    def _american_to_decimal(self, american: int) -> float:
        """Convert American odds to decimal."""
        if american > 0:
            return round((american / 100) + 1, 3)
        else:
            return round((100 / abs(american)) + 1, 3)
    
    def _get_mock_games(self) -> List[Dict]:
        """Return mock game data."""
        return [
            {
                "id": "mock_game_1",
                "sport_key": "basketball_nba",
                "home_team": "Los Angeles Lakers",
                "away_team": "Phoenix Suns",
                "commence_time": datetime.now().isoformat(),
                "bookmakers": []
            },
            {
                "id": "mock_game_2", 
                "sport_key": "basketball_nba",
                "home_team": "Boston Celtics",
                "away_team": "New York Knicks",
                "commence_time": datetime.now().isoformat(),
                "bookmakers": []
            }
        ]
    
    def _get_mock_game_odds(self) -> Dict:
        """Return mock odds for a single game."""
        return {
            "id": "mock_game",
            "bookmakers": [
                {
                    "title": "MockBook",
                    "markets": [
                        {
                            "key": "spreads",
                            "outcomes": [
                                {"name": "Team A", "price": -110, "point": -5.5},
                                {"name": "Team B", "price": -110, "point": 5.5}
                            ]
                        },
                        {
                            "key": "totals",
                            "outcomes": [
                                {"name": "Over", "price": -110, "point": 220.5},
                                {"name": "Under", "price": -110, "point": 220.5}
                            ]
                        }
                    ]
                }
            ]
        }
    
    def _get_mock_player_props(self) -> List[Dict]:
        """Return mock player prop data."""
        return []
    
    def get_rate_limit_status(self) -> Dict:
        """Get current rate limit status."""
        return {
            "remaining": self.requests_remaining,
            "used": self.requests_used
        }


# Global instance
odds_api_client = OddsAPIClient()
