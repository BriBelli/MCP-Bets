"""
Redis Configuration and Connection Management

Handles Redis connection for hot cache layer with automatic reconnection.
"""

import redis
from redis import Redis
from typing import Optional
import logging

from mcp_bets.config.settings import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """
    Singleton Redis connection manager with automatic reconnection
    """
    
    _instance: Optional[Redis] = None
    _connected: bool = False
    
    @classmethod
    def get_client(cls) -> Redis:
        """
        Get Redis client instance (singleton pattern)
        
        Returns:
            Redis: Connected Redis client
        """
        if cls._instance is None:
            cls._instance = cls._create_client()
        
        # Test connection
        if not cls._test_connection():
            logger.warning("Redis connection lost, reconnecting...")
            cls._instance = cls._create_client()
        
        return cls._instance
    
    @classmethod
    def _create_client(cls) -> Redis:
        """Create new Redis client with connection pooling"""
        try:
            client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,  # Automatically decode bytes to strings
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            
            # Test connection
            client.ping()
            cls._connected = True
            logger.info("✅ Redis connected successfully")
            
            return client
            
        except redis.ConnectionError as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
    
    @classmethod
    def _test_connection(cls) -> bool:
        """Test if Redis connection is alive"""
        if cls._instance is None:
            return False
        
        try:
            cls._instance.ping()
            return True
        except redis.ConnectionError:
            cls._connected = False
            return False
    
    @classmethod
    def disconnect(cls):
        """Close Redis connection (call on shutdown)"""
        if cls._instance:
            cls._instance.close()
            cls._instance = None
            cls._connected = False
            logger.info("✅ Redis disconnected")
    
    @classmethod
    def is_connected(cls) -> bool:
        """Check if Redis is currently connected"""
        return cls._connected and cls._test_connection()
    
    @classmethod
    def get_stats(cls) -> dict:
        """Get Redis connection and memory stats"""
        if not cls.is_connected():
            return {"status": "disconnected"}
        
        try:
            info = cls._instance.info()
            return {
                "status": "connected",
                "version": info.get("redis_version"),
                "used_memory_human": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            logger.error(f"Failed to get Redis stats: {e}")
            return {"status": "error", "error": str(e)}


# Convenience function to get Redis client
def get_redis() -> Redis:
    """
    Get Redis client instance
    
    Usage:
        redis_client = get_redis()
        redis_client.set("key", "value")
    """
    return RedisManager.get_client()


# Health check function
def check_redis_health() -> bool:
    """
    Check if Redis is accessible and healthy
    
    Returns:
        bool: True if Redis is healthy, False otherwise
    """
    try:
        client = get_redis()
        client.ping()
        logger.info("✅ Redis health check passed")
        return True
    except Exception as e:
        logger.error(f"❌ Redis health check failed: {e}")
        return False
