"""
Cache Manager

Intelligent multi-tier caching system with:
- Hot cache: Redis (sub-second access, 15-min TTL)
- Warm cache: PostgreSQL (persistent fallback, 1-hour TTL)
- Cold cache: SportsDataIO API (source of truth)

Features:
- Automatic fallback from Redis → PostgreSQL → API
- Intelligent TTL refresh based on data type
- Cache statistics and monitoring
- Async/await for high performance
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Callable
from enum import Enum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mcp_bets.config.redis_config import RedisManager
from mcp_bets.config.settings import settings
from mcp_bets.models import CacheEntry


class CacheDataType(str, Enum):
    """Cache data type categories with different TTL policies"""
    ODDS = "odds"                    # 5 minutes (changes frequently)
    PROPS = "props"                  # 15 minutes (changes frequently)
    INJURIES = "injuries"            # 1 hour (updated daily)
    SCHEDULES = "schedules"          # 6 hours (rarely changes)
    TEAMS = "teams"                  # 24 hours (static)
    PLAYERS = "players"              # 12 hours (roster changes)
    STATS = "stats"                  # 24 hours (historical data)
    NEWS = "news"                    # 30 minutes (updated frequently)


class CacheTier(str, Enum):
    """Cache tier identifiers"""
    HOT = "redis"      # Redis (sub-second)
    WARM = "postgres"  # PostgreSQL (milliseconds)
    COLD = "api"       # SportsDataIO API (seconds)


class CacheManager:
    """
    Multi-tier cache manager
    
    Cache Strategy:
    1. Check Redis (hot cache) - fastest
    2. If miss, check PostgreSQL (warm cache) - persistent
    3. If miss, fetch from API and populate caches
    4. Return data to caller
    
    TTL Policies by Data Type:
    - Odds: Redis 5min, PostgreSQL 15min
    - Props: Redis 15min, PostgreSQL 1hr
    - Injuries: Redis 1hr, PostgreSQL 6hr
    - Schedules: Redis 6hr, PostgreSQL 24hr
    - Teams: Redis 24hr, PostgreSQL 7days
    - Players: Redis 12hr, PostgreSQL 3days
    - Stats: Redis 24hr, PostgreSQL 7days
    - News: Redis 30min, PostgreSQL 2hr
    """
    
    # TTL configurations (in seconds)
    HOT_TTL = {
        CacheDataType.ODDS: 300,        # 5 minutes
        CacheDataType.PROPS: 900,       # 15 minutes
        CacheDataType.INJURIES: 3600,   # 1 hour
        CacheDataType.SCHEDULES: 21600, # 6 hours
        CacheDataType.TEAMS: 86400,     # 24 hours
        CacheDataType.PLAYERS: 43200,   # 12 hours
        CacheDataType.STATS: 86400,     # 24 hours
        CacheDataType.NEWS: 1800,       # 30 minutes
    }
    
    WARM_TTL = {
        CacheDataType.ODDS: 900,        # 15 minutes
        CacheDataType.PROPS: 3600,      # 1 hour
        CacheDataType.INJURIES: 21600,  # 6 hours
        CacheDataType.SCHEDULES: 86400, # 24 hours
        CacheDataType.TEAMS: 604800,    # 7 days
        CacheDataType.PLAYERS: 259200,  # 3 days
        CacheDataType.STATS: 604800,    # 7 days
        CacheDataType.NEWS: 7200,       # 2 hours
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis = RedisManager.get_client()
        
        # Statistics
        self.stats = {
            "hot_hits": 0,
            "warm_hits": 0,
            "cold_hits": 0,
            "total_requests": 0,
        }
    
    async def get(
        self,
        key: str,
        data_type: CacheDataType,
        fetch_fn: Optional[Callable] = None,
    ) -> Optional[Any]:
        """
        Get data from cache with automatic fallback
        
        Args:
            key: Cache key (e.g., "props:week:2024:8")
            data_type: Type of data for TTL policy
            fetch_fn: Optional async function to fetch data if cache miss
        
        Returns:
            Cached data or None if not found and no fetch_fn provided
        
        Example:
            data = await cache.get(
                "props:week:2024:8",
                CacheDataType.PROPS,
                fetch_fn=lambda: client.get_player_props_by_week(2024, 8)
            )
        """
        self.stats["total_requests"] += 1
        
        # Try hot cache (Redis)
        data = await self._get_from_hot_cache(key)
        if data is not None:
            self.stats["hot_hits"] += 1
            return data
        
        # Try warm cache (PostgreSQL)
        data = await self._get_from_warm_cache(key)
        if data is not None:
            self.stats["warm_hits"] += 1
            # Promote to hot cache
            await self._set_hot_cache(key, data, data_type)
            return data
        
        # Cold cache (API fetch)
        if fetch_fn is None:
            return None
        
        self.stats["cold_hits"] += 1
        data = await fetch_fn()
        
        # Populate caches
        await self._set_hot_cache(key, data, data_type)
        await self._set_warm_cache(key, data, data_type)
        
        return data
    
    async def set(
        self,
        key: str,
        data: Any,
        data_type: CacheDataType,
    ) -> None:
        """
        Set data in both cache tiers
        
        Args:
            key: Cache key
            data: Data to cache (must be JSON-serializable)
            data_type: Type of data for TTL policy
        """
        await self._set_hot_cache(key, data, data_type)
        await self._set_warm_cache(key, data, data_type)
    
    async def delete(self, key: str) -> None:
        """
        Delete data from all cache tiers
        
        Args:
            key: Cache key to delete
        """
        # Delete from Redis
        if self.redis:
            await self.redis.delete(key)
        
        # Delete from PostgreSQL
        await self.db.execute(
            select(CacheEntry).where(CacheEntry.key == key)
        )
        result = await self.db.execute(
            select(CacheEntry).where(CacheEntry.key == key)
        )
        entry = result.scalar_one_or_none()
        if entry:
            await self.db.delete(entry)
            await self.db.commit()
    
    async def clear_by_pattern(self, pattern: str) -> int:
        """
        Clear cache entries matching a pattern
        
        Args:
            pattern: Key pattern (e.g., "props:*", "injuries:2024:*")
        
        Returns:
            Number of keys deleted
        """
        count = 0
        
        # Clear from Redis
        if self.redis:
            keys = await self.redis.keys(pattern)
            if keys:
                count += await self.redis.delete(*keys)
        
        # Clear from PostgreSQL (SQL LIKE pattern)
        sql_pattern = pattern.replace("*", "%")
        result = await self.db.execute(
            select(CacheEntry).where(CacheEntry.key.like(sql_pattern))
        )
        entries = result.scalars().all()
        
        for entry in entries:
            await self.db.delete(entry)
        
        await self.db.commit()
        count += len(entries)
        
        return count
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics
        
        Returns:
            Dictionary with hit rates, counts, and performance metrics
        """
        total = self.stats["total_requests"]
        if total == 0:
            return {
                "total_requests": 0,
                "hot_hit_rate": 0.0,
                "warm_hit_rate": 0.0,
                "cold_hit_rate": 0.0,
                "overall_cache_hit_rate": 0.0,
            }
        
        hot_rate = (self.stats["hot_hits"] / total) * 100
        warm_rate = (self.stats["warm_hits"] / total) * 100
        cold_rate = (self.stats["cold_hits"] / total) * 100
        cache_hit_rate = hot_rate + warm_rate
        
        # Get warm cache stats from PostgreSQL
        result = await self.db.execute(
            select(CacheEntry)
        )
        warm_entries = result.scalars().all()
        
        # Get Redis stats
        redis_info = {}
        if self.redis:
            info = await self.redis.info()
            redis_info = {
                "used_memory_human": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
            }
        
        return {
            "total_requests": total,
            "hot_hits": self.stats["hot_hits"],
            "warm_hits": self.stats["warm_hits"],
            "cold_hits": self.stats["cold_hits"],
            "hot_hit_rate": round(hot_rate, 2),
            "warm_hit_rate": round(warm_rate, 2),
            "cold_hit_rate": round(cold_rate, 2),
            "overall_cache_hit_rate": round(cache_hit_rate, 2),
            "warm_cache_entries": len(warm_entries),
            "redis_info": redis_info,
        }
    
    async def cleanup_expired(self) -> int:
        """
        Remove expired entries from warm cache
        
        Returns:
            Number of entries removed
        """
        now = datetime.now(timezone.utc)
        
        result = await self.db.execute(
            select(CacheEntry).where(CacheEntry.expires_at < now)
        )
        expired_entries = result.scalars().all()
        
        for entry in expired_entries:
            await self.db.delete(entry)
        
        await self.db.commit()
        return len(expired_entries)
    
    # =========================================================================
    # Internal Cache Tier Methods
    # =========================================================================
    
    async def _get_from_hot_cache(self, key: str) -> Optional[Any]:
        """Get data from Redis (hot cache)"""
        if not self.redis:
            return None
        
        try:
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
        except Exception:
            # Redis error - fail gracefully
            return None
        
        return None
    
    async def _get_from_warm_cache(self, key: str) -> Optional[Any]:
        """Get data from PostgreSQL (warm cache)"""
        result = await self.db.execute(
            select(CacheEntry).where(CacheEntry.key == key)
        )
        entry = result.scalar_one_or_none()
        
        if not entry:
            return None
        
        # Check if expired
        if entry.is_expired:
            await self.db.delete(entry)
            await self.db.commit()
            return None
        
        return entry.data
    
    async def _set_hot_cache(
        self,
        key: str,
        data: Any,
        data_type: CacheDataType,
    ) -> None:
        """Set data in Redis (hot cache)"""
        if not self.redis:
            return
        
        try:
            ttl = self.HOT_TTL.get(data_type, 900)  # Default 15 minutes
            await self.redis.setex(
                key,
                ttl,
                json.dumps(data, default=str),
            )
        except Exception:
            # Redis error - fail gracefully
            pass
    
    async def _set_warm_cache(
        self,
        key: str,
        data: Any,
        data_type: CacheDataType,
    ) -> None:
        """Set data in PostgreSQL (warm cache)"""
        ttl_seconds = self.WARM_TTL.get(data_type, 3600)  # Default 1 hour
        
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)
        
        # Check if entry exists
        result = await self.db.execute(
            select(CacheEntry).where(CacheEntry.key == key)
        )
        entry = result.scalar_one_or_none()
        
        if entry:
            # Update existing entry
            entry.data = data
            entry.cached_at = now
            entry.expires_at = expires_at
        else:
            # Create new entry
            entry = CacheEntry(
                key=key,
                data=data,
                cached_at=now,
                expires_at=expires_at,
                data_type=data_type.value,
            )
            self.db.add(entry)
        
        await self.db.commit()


# ============================================================================
# Cache Key Builders
# ============================================================================

def build_cache_key(*parts: str) -> str:
    """
    Build a cache key from parts
    
    Args:
        *parts: Key components
    
    Returns:
        Colon-separated cache key
    
    Example:
        build_cache_key("props", "week", "2024", "8")
        # Returns: "props:week:2024:8"
    """
    return ":".join(str(part) for part in parts)


def parse_cache_key(key: str) -> list[str]:
    """
    Parse a cache key into parts
    
    Args:
        key: Cache key
    
    Returns:
        List of key components
    
    Example:
        parse_cache_key("props:week:2024:8")
        # Returns: ["props", "week", "2024", "8"]
    """
    return key.split(":")
