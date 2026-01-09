"""
NBABot v10.0 API Client

Handles all API-Basketball API interactions.
"""

import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from config import API_BASKETBALL_KEY, API_BASKETBALL_BASE_URL, H2H_WINDOW_YEARS, MOCK_MODE


# Mock data for testing without API
MOCK_GAMES = [
    {
        "id": 12345,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": "19:00",
        "status": {"short": "NS"},
        "teams": {
            "home": {"id": 1, "name": "Los Angeles Lakers"},
            "away": {"id": 2, "name": "Phoenix Suns"}
        },
        "scores": {"home": {"total": 0}, "away": {"total": 0}}
    },
    {
        "id": 12346,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": "20:30",
        "status": {"short": "NS"},
        "teams": {
            "home": {"id": 3, "name": "Milwaukee Bucks"},
            "away": {"id": 4, "name": "Miami Heat"}
        },
        "scores": {"home": {"total": 0}, "away": {"total": 0}}
    },
    {
        "id": 12347,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": "21:00",
        "status": {"short": "NS"},
        "teams": {
            "home": {"id": 5, "name": "Boston Celtics"},
            "away": {"id": 6, "name": "New York Knicks"}
        },
        "scores": {"home": {"total": 0}, "away": {"total": 0}}
    }
]

def _generate_mock_team_games(team_id: int, limit: int) -> List[Dict]:
    """Generate mock historical games for a team."""
    import random
    games = []
    for i in range(limit):
        team_score = random.randint(95, 125)
        opp_score = random.randint(95, 125)
        won = team_score > opp_score
        games.append({
            "id": 10000 + i,
            "date": (datetime.now() - timedelta(days=i+1)).strftime("%Y-%m-%d"),
            "status": {"short": "FT"},
            "teams": {
                "home": {"id": team_id, "name": "Team"},
                "away": {"id": 99, "name": "Opponent"}
            },
            "scores": {
                "home": {"total": team_score},
                "away": {"total": opp_score}
            }
        })
    return games

def _generate_mock_player_stats(player_id: int, limit: int) -> List[Dict]:
    """Generate mock player statistics."""
    import random
    stats = []
    for i in range(limit):
        stats.append({
            "game": {"date": (datetime.now() - timedelta(days=i+1)).strftime("%Y-%m-%d")},
            "points": random.randint(15, 35),
            "rebounds": random.randint(3, 12),
            "assists": random.randint(2, 10),
            "steals": random.randint(0, 3),
            "blocks": random.randint(0, 3)
        })
    return stats


class APIBasketballClient:
    """
    Async client for API-Basketball.
    """
    
    def __init__(self):
        self.base_url = API_BASKETBALL_BASE_URL
        self.headers = {
            "x-rapidapi-key": API_BASKETBALL_KEY,
            "x-rapidapi-host": "v1.basketball.api-sports.io"
        }
        self.session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.session
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate cache key from endpoint and params."""
        param_str = "_".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{endpoint}_{param_str}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid."""
        if cache_key not in self._cache_timestamps:
            return False
        age = (datetime.now() - self._cache_timestamps[cache_key]).total_seconds()
        return age < self.cache_ttl
    
    async def _request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Make API request with caching.
        
        Args:
            endpoint: API endpoint (e.g., 'games')
            params: Query parameters
        
        Returns:
            API response as dict
        """
        params = params or {}
        cache_key = self._get_cache_key(endpoint, params)
        
        # Check cache
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        # Make request
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint}"
        
        async with session.get(url, params=params) as response:
            data = await response.json()
            
            # Cache response
            self._cache[cache_key] = data
            self._cache_timestamps[cache_key] = datetime.now()
            
            return data
    
    # ========== GAMES ==========
    
    async def get_games_today(self, league_id: int = 12) -> List[Dict]:
        """
        Get today's NBA games.
        
        Args:
            league_id: NBA league ID (default: 12 for NBA)
        
        Returns:
            List of game objects
        """
        # Return mock data if in mock mode
        if MOCK_MODE:
            return MOCK_GAMES
        
        today = datetime.now().strftime("%Y-%m-%d")
        params = {
            "league": league_id,
            "date": today
        }
        
        response = await self._request("games", params)
        return response.get("response", [])
    
    async def get_games_by_date(self, date: str, league_id: int = 12) -> List[Dict]:
        """
        Get NBA games for a specific date.
        
        Args:
            date: Date string in YYYY-MM-DD format
            league_id: NBA league ID
        
        Returns:
            List of game objects
        """
        params = {
            "league": league_id,
            "date": date
        }
        
        response = await self._request("games", params)
        return response.get("response", [])
    
    # ========== TEAMS ==========
    
    async def get_team_games(self, team_id: int, limit: int = 15, league_id: int = 12) -> List[Dict]:
        """
        Get recent games for a team.
        
        Args:
            team_id: Team ID
            limit: Number of games to fetch
            league_id: NBA league ID
        
        Returns:
            List of game objects (most recent first)
        """
        # Return mock data if in mock mode
        if MOCK_MODE:
            return _generate_mock_team_games(team_id, limit)
        
        # Get current season
        season = self._get_current_season()
        
        params = {
            "league": league_id,
            "season": season,
            "team": team_id
        }
        
        response = await self._request("games", params)
        games = response.get("response", [])
        
        # Filter to completed games and sort by date (newest first)
        completed = [g for g in games if g.get("status", {}).get("short") == "FT"]
        completed.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        return completed[:limit]
    
    async def get_team_stats(self, team_id: int, season: str = None, league_id: int = 12) -> Dict:
        """
        Get team statistics.
        
        Args:
            team_id: Team ID
            season: Season string (e.g., "2024-2025")
            league_id: NBA league ID
        
        Returns:
            Team statistics object
        """
        season = season or self._get_current_season()
        
        params = {
            "league": league_id,
            "season": season,
            "team": team_id
        }
        
        response = await self._request("statistics", params)
        return response.get("response", {})
    
    async def get_head_to_head(self, team1_id: int, team2_id: int, league_id: int = 12) -> List[Dict]:
        """
        Get head-to-head games between two teams (last 1 year).
        
        Args:
            team1_id: First team ID
            team2_id: Second team ID
            league_id: NBA league ID
        
        Returns:
            List of H2H game objects
        """
        # Return mock data if in mock mode
        if MOCK_MODE:
            return _generate_mock_team_games(team1_id, 5)  # Return 5 mock H2H games
        
        # Calculate date range (last 1 year)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * H2H_WINDOW_YEARS)
        
        params = {
            "league": league_id,
            "h2h": f"{team1_id}-{team2_id}"
        }
        
        response = await self._request("games", params)
        games = response.get("response", [])
        
        # Filter to games within the window
        filtered = []
        for game in games:
            game_date_str = game.get("date", "")[:10]  # Get YYYY-MM-DD
            try:
                game_date = datetime.strptime(game_date_str, "%Y-%m-%d")
                if start_date <= game_date <= end_date:
                    filtered.append(game)
            except ValueError:
                continue
        
        return filtered
    
    # ========== PLAYERS ==========
    
    async def get_player_stats(self, player_id: int, limit: int = 15, league_id: int = 12) -> List[Dict]:
        """
        Get recent game stats for a player.
        
        Args:
            player_id: Player ID
            limit: Number of games to fetch
            league_id: NBA league ID
        
        Returns:
            List of player game stat objects (most recent first)
        """
        # Return mock data if in mock mode
        if MOCK_MODE:
            return _generate_mock_player_stats(player_id, limit)
        
        season = self._get_current_season()
        
        params = {
            "league": league_id,
            "season": season,
            "player": player_id
        }
        
        response = await self._request("players/statistics", params)
        stats = response.get("response", [])
        
        # Sort by game date (newest first)
        stats.sort(key=lambda x: x.get("game", {}).get("date", ""), reverse=True)
        
        return stats[:limit]
    
    async def get_players_by_team(self, team_id: int, league_id: int = 12) -> List[Dict]:
        """
        Get all players on a team.
        
        Args:
            team_id: Team ID
            league_id: NBA league ID
        
        Returns:
            List of player objects
        """
        # Return mock data if in mock mode
        if MOCK_MODE:
            # Return mock players
            mock_players = [
                {"id": team_id * 100 + 1, "firstname": "Star", "lastname": "Player"},
                {"id": team_id * 100 + 2, "firstname": "Point", "lastname": "Guard"},
                {"id": team_id * 100 + 3, "firstname": "Power", "lastname": "Forward"},
            ]
            return mock_players
        
        season = self._get_current_season()
        
        params = {
            "league": league_id,
            "season": season,
            "team": team_id
        }
        
        response = await self._request("players", params)
        return response.get("response", [])
    
    # ========== ODDS ==========
    
    async def get_game_odds(self, game_id: int) -> Dict:
        """
        Get betting odds for a game.
        
        Args:
            game_id: Game ID
        
        Returns:
            Odds object
        """
        params = {
            "game": game_id
        }
        
        response = await self._request("odds", params)
        return response.get("response", {})
    
    # ========== HELPERS ==========
    
    def _get_current_season(self) -> str:
        """
        Get current NBA season string.
        
        Returns:
            Season string (e.g., "2024-2025")
        """
        now = datetime.now()
        # NBA season typically starts in October
        if now.month >= 10:
            return f"{now.year}-{now.year + 1}"
        else:
            return f"{now.year - 1}-{now.year}"
    
    def parse_game_result(self, game: Dict, team_id: int) -> Dict:
        """
        Parse game result for a specific team.
        
        Args:
            game: Game object from API
            team_id: Team ID to analyze
        
        Returns:
            Dict with team_score, opponent_score, won, margin
        """
        home_team = game.get("teams", {}).get("home", {})
        away_team = game.get("teams", {}).get("away", {})
        
        scores = game.get("scores", {})
        home_score = scores.get("home", {}).get("total", 0)
        away_score = scores.get("away", {}).get("total", 0)
        
        if home_team.get("id") == team_id:
            team_score = home_score
            opponent_score = away_score
            is_home = True
        else:
            team_score = away_score
            opponent_score = home_score
            is_home = False
        
        won = team_score > opponent_score
        margin = team_score - opponent_score
        
        return {
            "team_score": team_score,
            "opponent_score": opponent_score,
            "won": won,
            "margin": margin,
            "is_home": is_home,
            "total": team_score + opponent_score
        }


# Global client instance
api_client = APIBasketballClient()
