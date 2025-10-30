"""
Cached SportsDataIO Client

Wraps SportsDataIO client methods with automatic caching.
"""

from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from mcp_bets.services.ingestion import SportsDataIOClient
from mcp_bets.services.cache.cache_manager import (
    CacheManager,
    CacheDataType,
    build_cache_key,
)


class CachedSportsDataIOClient:
    """
    SportsDataIO client with automatic caching
    
    All methods cache responses in Redis + PostgreSQL to reduce API calls.
    """
    
    def __init__(self, client: SportsDataIOClient, db: AsyncSession):
        self.client = client
        self.cache = CacheManager(db)
    
    # =========================================================================
    # Schedules & Scores (Cached)
    # =========================================================================
    
    async def get_schedules(self, season: int) -> List[Dict[str, Any]]:
        """Get all games for a season (cached 6 hours)"""
        key = build_cache_key("schedules", "season", season)
        return await self.cache.get(
            key,
            CacheDataType.SCHEDULES,
            fetch_fn=lambda: self.client.get_schedules(season),
        )
    
    async def get_schedules_by_week(
        self,
        season: int,
        week: int,
    ) -> List[Dict[str, Any]]:
        """Get games for a specific week (cached 6 hours)"""
        key = build_cache_key("schedules", "week", season, week)
        return await self.cache.get(
            key,
            CacheDataType.SCHEDULES,
            fetch_fn=lambda: self.client.get_schedules_by_week(season, week),
        )
    
    async def get_current_week(self) -> int:
        """Get current week (cached 1 hour)"""
        key = build_cache_key("schedules", "current_week")
        return await self.cache.get(
            key,
            CacheDataType.SCHEDULES,
            fetch_fn=lambda: self.client.get_current_week(),
        )
    
    async def get_current_season(self) -> int:
        """Get current season (cached 24 hours)"""
        key = build_cache_key("schedules", "current_season")
        return await self.cache.get(
            key,
            CacheDataType.SCHEDULES,
            fetch_fn=lambda: self.client.get_current_season(),
        )
    
    # =========================================================================
    # Teams (Cached)
    # =========================================================================
    
    async def get_teams(self) -> List[Dict[str, Any]]:
        """Get all teams (cached 24 hours)"""
        key = build_cache_key("teams", "all")
        return await self.cache.get(
            key,
            CacheDataType.TEAMS,
            fetch_fn=lambda: self.client.get_teams(),
        )
    
    async def get_team_by_key(self, team_key: str) -> Dict[str, Any]:
        """Get single team (cached 24 hours)"""
        key = build_cache_key("teams", "key", team_key)
        return await self.cache.get(
            key,
            CacheDataType.TEAMS,
            fetch_fn=lambda: self.client.get_team_by_key(team_key),
        )
    
    # =========================================================================
    # Players (Cached)
    # =========================================================================
    
    async def get_players(self) -> List[Dict[str, Any]]:
        """Get all players (cached 12 hours)"""
        key = build_cache_key("players", "all")
        return await self.cache.get(
            key,
            CacheDataType.PLAYERS,
            fetch_fn=lambda: self.client.get_players(),
        )
    
    async def get_players_by_team(self, team_key: str) -> List[Dict[str, Any]]:
        """Get players by team (cached 12 hours)"""
        key = build_cache_key("players", "team", team_key)
        return await self.cache.get(
            key,
            CacheDataType.PLAYERS,
            fetch_fn=lambda: self.client.get_players_by_team(team_key),
        )
    
    # =========================================================================
    # Player Stats (Cached)
    # =========================================================================
    
    async def get_player_game_stats_by_week(
        self,
        season: int,
        week: int,
    ) -> List[Dict[str, Any]]:
        """Get player stats for week (cached 24 hours)"""
        key = build_cache_key("stats", "week", season, week)
        return await self.cache.get(
            key,
            CacheDataType.STATS,
            fetch_fn=lambda: self.client.get_player_game_stats_by_week(season, week),
        )
    
    async def get_player_season_stats(
        self,
        season: int,
    ) -> List[Dict[str, Any]]:
        """Get season stats (cached 24 hours)"""
        key = build_cache_key("stats", "season", season)
        return await self.cache.get(
            key,
            CacheDataType.STATS,
            fetch_fn=lambda: self.client.get_player_season_stats(season),
        )
    
    # =========================================================================
    # Injuries (Cached)
    # =========================================================================
    
    async def get_injuries_by_week(
        self,
        season: int,
        week: int,
    ) -> List[Dict[str, Any]]:
        """Get injury reports (cached 1 hour)"""
        key = build_cache_key("injuries", "week", season, week)
        return await self.cache.get(
            key,
            CacheDataType.INJURIES,
            fetch_fn=lambda: self.client.get_injuries_by_week(season, week),
        )
    
    async def get_injuries_by_team(
        self,
        season: int,
        week: int,
        team_key: str,
    ) -> List[Dict[str, Any]]:
        """Get team injuries (cached 1 hour)"""
        key = build_cache_key("injuries", "team", season, week, team_key)
        return await self.cache.get(
            key,
            CacheDataType.INJURIES,
            fetch_fn=lambda: self.client.get_injuries_by_team(season, week, team_key),
        )
    
    # =========================================================================
    # Player Props (Cached)
    # =========================================================================
    
    async def get_player_props_by_week(
        self,
        season: int,
        week: int,
    ) -> List[Dict[str, Any]]:
        """Get player props (cached 15 minutes)"""
        key = build_cache_key("props", "week", season, week)
        return await self.cache.get(
            key,
            CacheDataType.PROPS,
            fetch_fn=lambda: self.client.get_player_props_by_week(season, week),
        )
    
    async def get_player_props_by_game(
        self,
        game_id: str,
    ) -> List[Dict[str, Any]]:
        """Get props for game (cached 15 minutes)"""
        key = build_cache_key("props", "game", game_id)
        return await self.cache.get(
            key,
            CacheDataType.PROPS,
            fetch_fn=lambda: self.client.get_player_props_by_game(game_id),
        )
    
    async def get_player_props_by_player(
        self,
        season: int,
        week: int,
        player_id: str,
    ) -> List[Dict[str, Any]]:
        """Get props for player (cached 15 minutes)"""
        key = build_cache_key("props", "player", season, week, player_id)
        return await self.cache.get(
            key,
            CacheDataType.PROPS,
            fetch_fn=lambda: self.client.get_player_props_by_player(season, week, player_id),
        )
    
    # =========================================================================
    # Odds & Lines (Cached)
    # =========================================================================
    
    async def get_odds_by_week(
        self,
        season: int,
        week: int,
    ) -> List[Dict[str, Any]]:
        """Get game odds (cached 5 minutes)"""
        key = build_cache_key("odds", "week", season, week)
        return await self.cache.get(
            key,
            CacheDataType.ODDS,
            fetch_fn=lambda: self.client.get_odds_by_week(season, week),
        )
    
    async def get_odds_by_game(
        self,
        game_id: str,
    ) -> List[Dict[str, Any]]:
        """Get odds for game (cached 5 minutes)"""
        key = build_cache_key("odds", "game", game_id)
        return await self.cache.get(
            key,
            CacheDataType.ODDS,
            fetch_fn=lambda: self.client.get_odds_by_game(game_id),
        )
    
    # =========================================================================
    # News (Cached)
    # =========================================================================
    
    async def get_news(self) -> List[Dict[str, Any]]:
        """Get NFL news (cached 30 minutes)"""
        key = build_cache_key("news", "all")
        return await self.cache.get(
            key,
            CacheDataType.NEWS,
            fetch_fn=lambda: self.client.get_news(),
        )
    
    async def get_news_by_player(self, player_id: str) -> List[Dict[str, Any]]:
        """Get player news (cached 30 minutes)"""
        key = build_cache_key("news", "player", player_id)
        return await self.cache.get(
            key,
            CacheDataType.NEWS,
            fetch_fn=lambda: self.client.get_news_by_player(player_id),
        )
    
    async def get_news_by_team(self, team_key: str) -> List[Dict[str, Any]]:
        """Get team news (cached 30 minutes)"""
        key = build_cache_key("news", "team", team_key)
        return await self.cache.get(
            key,
            CacheDataType.NEWS,
            fetch_fn=lambda: self.client.get_news_by_team(team_key),
        )
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    async def invalidate_week_data(self, season: int, week: int) -> None:
        """
        Invalidate all cached data for a specific week
        
        Useful when you know data has changed (e.g., after games complete)
        """
        patterns = [
            f"schedules:week:{season}:{week}",
            f"props:week:{season}:{week}",
            f"odds:week:{season}:{week}",
            f"injuries:week:{season}:{week}",
            f"stats:week:{season}:{week}",
        ]
        
        for pattern in patterns:
            await self.cache.delete(pattern)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        return await self.cache.get_stats()
    
    async def cleanup_expired_cache(self) -> int:
        """Remove expired cache entries from warm cache"""
        return await self.cache.cleanup_expired()
