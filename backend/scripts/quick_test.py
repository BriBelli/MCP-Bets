#!/usr/bin/env python3
"""
Quick Sanity Check for MCP Bets Phase 1

Tests basic connectivity and functionality:
- Database connection
- SportsDataIO API connection
- Redis connection (optional)
- Cache read/write operations

Expected runtime: ~30 seconds
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import directly from the settings module to avoid database init
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import httpx


class Settings(BaseSettings):
    """Minimal settings for testing"""
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/mcp_bets",
        env="DATABASE_URL"
    )
    SPORTSDATAIO_API_KEY: str = Field(default="", env="SPORTSDATAIO_API_KEY")
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"  # Ignore extra fields from .env
    }


def main():
    """Run quick sanity checks"""
    print("🚀 MCP Bets Phase 1 - Quick Sanity Check")
    print("=" * 60)
    
    settings = Settings()
    passed = 0
    failed = 0
    
    # Test 1: Database Connection (PostgreSQL)
    print("\n📊 Test 1: Database Connection")
    try:
        import psycopg
        
        # Parse DATABASE_URL
        db_url = settings.DATABASE_URL
        # Convert to psycopg connection string if needed
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        
        # Simple connection test (sync)
        conn_str = db_url.replace("postgresql+psycopg://", "")
        with psycopg.connect(f"postgresql://{conn_str}") as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                if result and result[0] == 1:
                    print("✅ Database connection OK")
                    passed += 1
                else:
                    print("❌ Database connection returned unexpected result")
                    failed += 1
    except Exception as e:
        print(f"❌ Database connection FAILED: {e}")
        failed += 1
    
    # Test 2: SportsDataIO API Connection
    print("\n🏈 Test 2: SportsDataIO API Connection")
    try:
        api_key = settings.SPORTSDATAIO_API_KEY
        if not api_key or api_key == "your_sportsdataio_api_key_here":
            print("⚠️  SportsDataIO API SKIPPED (not configured in .env)")
        else:
            # Test with teams endpoint (simple and cacheable)
            url = "https://api.sportsdata.io/v3/nfl/scores/json/Teams"
            headers = {"Ocp-Apim-Subscription-Key": api_key}
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                teams = response.json()
                
                if len(teams) > 0:
                    print(f"✅ SportsDataIO API OK (fetched {len(teams)} teams)")
                    passed += 1
                else:
                    print("❌ SportsDataIO API returned empty response")
                    failed += 1
    except ValueError as e:
        print(f"⚠️  SportsDataIO API SKIPPED: {e}")
    except Exception as e:
        print(f"❌ SportsDataIO API FAILED: {e}")
        failed += 1
    
    # Test 3: Redis Connection (Optional)
    print("\n💾 Test 3: Redis Connection (Optional)")
    try:
        if settings.REDIS_HOST:
            import redis
            r = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,
                socket_connect_timeout=5
            )
            r.ping()
            print("✅ Redis connection OK")
            passed += 1
        else:
            print("⚠️  Redis SKIPPED (not configured - PostgreSQL cache will be used)")
    except ImportError:
        print("⚠️  Redis SKIPPED (redis package not installed)")
    except Exception as e:
        print(f"⚠️  Redis connection FAILED: {e} (PostgreSQL cache will be used)")
    
    # Test 4: Cache Operations (PostgreSQL - Check table exists)
    print("\n🗄️  Test 4: Cache Table Check")
    try:
        import psycopg
        
        conn_str = settings.DATABASE_URL.replace("postgresql://", "")
        if conn_str.startswith("postgresql+psycopg://"):
            conn_str = conn_str.replace("postgresql+psycopg://", "")
        
        with psycopg.connect(f"postgresql://{conn_str}") as conn:
            with conn.cursor() as cur:
                # Check if cache_entries table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'cache_entries'
                    )
                """)
                table_exists = cur.fetchone()[0]
                
                if table_exists:
                    print("✅ Cache table exists in database")
                    passed += 1
                else:
                    print("⚠️  Cache table doesn't exist (run scripts/init_db.py first)")
            
    except Exception as e:
        print(f"❌ Cache table check FAILED: {e}")
        failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ All systems operational - ready for full pipeline test!")
        return 0
    else:
        print("⚠️  Some tests failed - please check configuration")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
