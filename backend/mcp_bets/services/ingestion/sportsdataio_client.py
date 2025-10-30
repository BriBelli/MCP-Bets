"""
SportsDataIO API Client

Implements comprehensive NFL data fetching with:
- Rate limiting (configurable requests per second/month)
- Retry logic with exponential backoff
- Comprehensive error handling
- All NFL endpoints (games, players, props, odds, injuries, stats)
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from mcp_bets.config.settings import settings


class RateLimiter:
    """
    Token bucket rate limiter for API requests
    
    Supports both:
    - Per-second rate limiting (burst control)
    - Per-month rate limiting (quota management)
    """
    
    def __init__(
        self,
        requests_per_second: float,
        requests_per_month: int,
        burst_size: int = 5,
    ):
        self.requests_per_second = requests_per_second
        self.requests_per_month = requests_per_month
        self.burst_size = burst_size
        
        # Token bucket for per-second limiting
        self.tokens = float(burst_size)
        self.last_update = time.time()
        
        # Monthly quota tracking
        self.monthly_requests = 0
        self.month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0)
        
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire permission to make a request (blocks if rate limited)"""
        async with self._lock:
            # Check monthly quota
            current_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0)
            if current_month > self.month_start:
                # Reset monthly counter
                self.monthly_requests = 0
                self.month_start = current_month
            
            if self.monthly_requests >= self.requests_per_month:
                raise SportsDataIOQuotaExceeded(
                    f"Monthly quota exceeded: {self.monthly_requests}/{self.requests_per_month}"
                )
            
            # Token bucket algorithm for per-second limiting
            now = time.time()
            elapsed = now - self.last_update
            
            # Add tokens based on elapsed time
            self.tokens = min(
                self.burst_size,
                self.tokens + (elapsed * self.requests_per_second)
            )
            self.last_update = now
            
            # Wait if no tokens available
            while self.tokens < 1:
                wait_time = (1 - self.tokens) / self.requests_per_second
                await asyncio.sleep(wait_time)
                
                now = time.time()
                elapsed = now - self.last_update
                self.tokens = min(
                    self.burst_size,
                    self.tokens + (elapsed * self.requests_per_second)
                )
                self.last_update = now
            
            # Consume one token
            self.tokens -= 1
            self.monthly_requests += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current rate limiter statistics"""
        return {
            "available_tokens": self.tokens,
            "burst_size": self.burst_size,
            "requests_per_second": self.requests_per_second,
            "monthly_requests": self.monthly_requests,
            "monthly_quota": self.requests_per_month,
            "quota_remaining": self.requests_per_month - self.monthly_requests,
        }


class SportsDataIOError(Exception):
    """Base exception for SportsDataIO API errors"""
    pass


class SportsDataIOQuotaExceeded(SportsDataIOError):
    """Raised when monthly API quota is exceeded"""
    pass


class SportsDataIORateLimitError(SportsDataIOError):
    """Raised when rate limit is hit"""
    pass


class SportsDataIOClient:
    """
    SportsDataIO API Client for NFL Data
    
    Endpoints covered:
    - Schedules (games by season/week)
    - Scores (game results)
    - Teams (all NFL teams)
    - Players (all active players)
    - Player Stats (game-by-game performance)
    - Injuries (injury reports)
    - Betting Props (player props from FanDuel/DraftKings)
    - Odds (game lines and spreads)
    - News (player/team news)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        requests_per_second: Optional[float] = None,
        requests_per_month: Optional[int] = None,
        burst_size: Optional[int] = None,
    ):
        self.api_key = api_key or settings.SPORTSDATAIO_API_KEY
        self.base_url = base_url or settings.SPORTSDATAIO_BASE_URL
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            requests_per_second=requests_per_second or settings.SPORTSDATAIO_REQUESTS_PER_SECOND,
            requests_per_month=requests_per_month or settings.SPORTSDATAIO_REQUESTS_PER_MONTH,
            burst_size=burst_size or settings.SPORTSDATAIO_BURST_SIZE,
        )
        
        # HTTP client with timeout
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Ocp-Apim-Subscription-Key": self.api_key},
        )
    
    async def close(self) -> None:
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    )
    async def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an API request with rate limiting and retry logic
        
        Args:
            endpoint: API endpoint path (e.g., "Scores/2024")
            params: Query parameters
        
        Returns:
            JSON response data
        
        Raises:
            SportsDataIOError: On API errors
            SportsDataIOQuotaExceeded: When monthly quota is exceeded
        """
        # Wait for rate limiter
        await self.rate_limiter.acquire()
        
        # Construct URL
        url = urljoin(self.base_url, endpoint)
        
        # Make request
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise SportsDataIORateLimitError(
                    f"Rate limit exceeded: {e.response.text}"
                )
            elif e.response.status_code == 403:
                raise SportsDataIOQuotaExceeded(
                    f"API quota exceeded or invalid key: {e.response.text}"
                )
            else:
                raise SportsDataIOError(
                    f"HTTP {e.response.status_code}: {e.response.text}"
                )
        
        except httpx.RequestError as e:
            raise SportsDataIOError(f"Request failed: {str(e)}")
    
    # =========================================================================
    # Schedules & Scores
    # =========================================================================
    
    async def get_schedules(self, season: int) -> List[Dict[str, Any]]:
        """
        Get all games for a season
        
        Args:
            season: NFL season year (e.g., 2024)
        
        Returns:
            List of game objects
        """
        return await self._request(f"Scores/{season}")
    
    async def get_schedules_by_week(
        self,
        season: int,
        week: int,
    ) -> List[Dict[str, Any]]:
        """
        Get games for a specific week
        
        Args:
            season: NFL season year (e.g., 2024)
            week: Week number (1-18 regular season, 19-22 playoffs)
        
        Returns:
            List of game objects
        """
        return await self._request(f"ScoresByWeek/{season}/{week}")
    
    async def get_current_week(self) -> int:
        """
        Get the current NFL week number
        
        Returns:
            Current week number
        """
        response = await self._request("CurrentWeek")
        return response.get("Week", 1)
    
    async def get_current_season(self) -> int:
        """
        Get the current NFL season year
        
        Returns:
            Current season year
        """
        response = await self._request("CurrentSeason")
        return response.get("Season", datetime.now(timezone.utc).year)
    
    # =========================================================================
    # Teams
    # =========================================================================
    
    async def get_teams(self) -> List[Dict[str, Any]]:
        """
        Get all NFL teams
        
        Returns:
            List of team objects with details (name, city, conference, division)
        """
        return await self._request("Teams")
    
    async def get_team_by_key(self, team_key: str) -> Dict[str, Any]:
        """
        Get single team by abbreviation
        
        Args:
            team_key: Team abbreviation (e.g., "SF", "KC")
        
        Returns:
            Team object
        """
        teams = await self.get_teams()
        for team in teams:
            if team.get("Key") == team_key:
                return team
        raise SportsDataIOError(f"Team not found: {team_key}")
    
    # =========================================================================
    # Players
    # =========================================================================
    
    async def get_players(self) -> List[Dict[str, Any]]:
        """
        Get all active NFL players
        
        Returns:
            List of player objects
        """
        return await self._request("Players")
    
    async def get_players_by_team(self, team_key: str) -> List[Dict[str, Any]]:
        """
        Get all players for a specific team
        
        Args:
            team_key: Team abbreviation (e.g., "SF")
        
        Returns:
            List of player objects
        """
        return await self._request(f"Players/{team_key}")
    
    async def get_free_agents(self) -> List[Dict[str, Any]]:
        """
        Get all free agent players
        
        Returns:
            List of free agent player objects
        """
        return await self._request("FreeAgents")
    
    # =========================================================================
    # Player Stats
    # =========================================================================
    
    async def get_player_game_stats_by_week(
        self,
        season: int,
        week: int,
    ) -> List[Dict[str, Any]]:
        """
        Get player game stats for a specific week
        
        Args:
            season: NFL season year
            week: Week number
        
        Returns:
            List of player stat objects
        """
        return await self._request(f"PlayerGameStatsByWeek/{season}/{week}")
    
    async def get_player_game_stats_by_player(
        self,
        season: int,
        week: int,
        player_id: str,
    ) -> Dict[str, Any]:
        """
        Get game stats for a specific player
        
        Args:
            season: NFL season year
            week: Week number
            player_id: SportsDataIO player ID
        
        Returns:
            Player stat object
        """
        return await self._request(f"PlayerGameStatsByPlayerID/{season}/{week}/{player_id}")
    
    async def get_player_season_stats(
        self,
        season: int,
    ) -> List[Dict[str, Any]]:
        """
        Get season stats for all players
        
        Args:
            season: NFL season year
        
        Returns:
            List of player season stat objects
        """
        return await self._request(f"PlayerSeasonStats/{season}")
    
    # =========================================================================
    # Injuries
    # =========================================================================
    
    async def get_injuries_by_week(
        self,
        season: int,
        week: int,
    ) -> List[Dict[str, Any]]:
        """
        Get injury reports for a specific week
        
        Args:
            season: NFL season year
            week: Week number
        
        Returns:
            List of injury report objects
        """
        return await self._request(f"Injuries/{season}/{week}")
    
    async def get_injuries_by_team(
        self,
        season: int,
        week: int,
        team_key: str,
    ) -> List[Dict[str, Any]]:
        """
        Get injury reports for a specific team
        
        Args:
            season: NFL season year
            week: Week number
            team_key: Team abbreviation
        
        Returns:
            List of injury report objects
        """
        return await self._request(f"Injuries/{season}/{week}/{team_key}")
    
    # =========================================================================
    # Player Props & Betting
    # =========================================================================
    
    async def get_player_props_by_week(
        self,
        season: int,
        week: int,
    ) -> List[Dict[str, Any]]:
        """
        Get player props for a specific week (FanDuel, DraftKings, etc.)
        
        Args:
            season: NFL season year
            week: Week number
        
        Returns:
            List of player prop objects
        """
        return await self._request(f"PlayerPropsByWeek/{season}/{week}")
    
    async def get_player_props_by_game(
        self,
        game_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get player props for a specific game
        
        Args:
            game_id: SportsDataIO game ID
        
        Returns:
            List of player prop objects
        """
        return await self._request(f"PlayerPropsByGameID/{game_id}")
    
    async def get_player_props_by_player(
        self,
        season: int,
        week: int,
        player_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get player props for a specific player
        
        Args:
            season: NFL season year
            week: Week number
            player_id: SportsDataIO player ID
        
        Returns:
            List of player prop objects
        """
        return await self._request(f"PlayerPropsByPlayerID/{season}/{week}/{player_id}")
    
    # =========================================================================
    # Odds & Lines
    # =========================================================================
    
    async def get_odds_by_week(
        self,
        season: int,
        week: int,
    ) -> List[Dict[str, Any]]:
        """
        Get game odds/lines for a specific week
        
        Args:
            season: NFL season year
            week: Week number
        
        Returns:
            List of odds objects with spreads, moneylines, totals
        """
        return await self._request(f"GameOddsByWeek/{season}/{week}")
    
    async def get_odds_by_game(
        self,
        game_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get odds for a specific game
        
        Args:
            game_id: SportsDataIO game ID
        
        Returns:
            List of odds objects from different sportsbooks
        """
        return await self._request(f"GameOddsByGameID/{game_id}")
    
    # =========================================================================
    # News
    # =========================================================================
    
    async def get_news(self) -> List[Dict[str, Any]]:
        """
        Get recent NFL news
        
        Returns:
            List of news article objects
        """
        return await self._request("News")
    
    async def get_news_by_player(self, player_id: str) -> List[Dict[str, Any]]:
        """
        Get news for a specific player
        
        Args:
            player_id: SportsDataIO player ID
        
        Returns:
            List of news article objects
        """
        return await self._request(f"NewsByPlayerID/{player_id}")
    
    async def get_news_by_team(self, team_key: str) -> List[Dict[str, Any]]:
        """
        Get news for a specific team
        
        Args:
            team_key: Team abbreviation
        
        Returns:
            List of news article objects
        """
        return await self._request(f"NewsByTeam/{team_key}")
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def get_rate_limiter_stats(self) -> Dict[str, Any]:
        """Get current rate limiter statistics"""
        return self.rate_limiter.get_stats()
    
    async def health_check(self) -> bool:
        """
        Check API connectivity
        
        Returns:
            True if API is reachable, False otherwise
        """
        try:
            await self.get_current_week()
            return True
        except Exception:
            return False
