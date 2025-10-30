"""
Full Pipeline Test for Phase 1

Tests the complete data ingestion pipeline:
1. Team import (static data)
2. Player import (season data)
3. Schedule import (week data)
4. Cache performance validation

Expected runtime: 2-5 minutes depending on API rate limiting

Note: Uses IngestionService from mcp_bets.services.ingestion.data_ingestion
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import time
from datetime import datetime

# Load environment variables from .env file
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Minimal Settings to avoid database init
class Settings:
    """Minimal settings for testing"""
    # Database (read from environment or use defaults)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg://brian@localhost:5432/mcp_bets")
    
    # SportsDataIO API
    SPORTSDATAIO_API_KEY: str = os.getenv("SPORTSDATAIO_API_KEY", "")
    SPORTSDATAIO_BASE_URL: str = "https://api.sportsdata.io/v3/nfl"
    
    # Redis (optional)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # Cache TTLs (in seconds)
    CACHE_TTL_TEAMS: int = 604800  # 7 days
    CACHE_TTL_PLAYERS: int = 86400  # 1 day
    CACHE_TTL_SCHEDULE: int = 86400  # 1 day
    CACHE_TTL_STATS: int = 3600  # 1 hour
    CACHE_TTL_PROPS: int = 300  # 5 minutes
    CACHE_TTL_INJURIES: int = 3600  # 1 hour


async def test_team_import():
    """Test team data import"""
    print("\n" + "="*80)
    print("TEST 1: TEAM IMPORT (Static Data)")
    print("="*80)
    
    from mcp_bets.services.cache.cached_client import CachedSportsDataIOClient
    from mcp_bets.services.ingestion.data_ingestion import IngestionService
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text
    
    settings = Settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    start_time = time.time()
    
    try:
        async with async_session() as session:
            # Create base SportsDataIO client
            from mcp_bets.services.ingestion.sportsdataio_client import SportsDataIOClient
            client = SportsDataIOClient(
                api_key=settings.SPORTSDATAIO_API_KEY,
                base_url=settings.SPORTSDATAIO_BASE_URL
            )
            
            # Create ingestion service
            service = IngestionService(session, client)
            
            # Import teams
            print("\n📥 Importing teams from SportsDataIO...")
            team_count = await service.import_teams()
            
            # Verify database count
            result = await session.execute(text("SELECT COUNT(*) FROM teams"))
            db_count = result.scalar()
            
            elapsed = time.time() - start_time
            
            print(f"✅ Imported {team_count} teams in {elapsed:.2f}s")
            print(f"✅ Database contains {db_count} teams")
            
            # Show sample teams
            result = await session.execute(text("SELECT key, city, name FROM teams LIMIT 5"))
            print("\n📋 Sample Teams:")
            for row in result:
                print(f"  • {row[0]}: {row[1]} {row[2]}")
            
            return {
                "status": "passed",
                "teams_imported": team_count,
                "db_count": db_count,
                "elapsed_time": elapsed
            }
            
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "failed", "error": str(e)}


async def test_player_import():
    """Test player data import"""
    print("\n" + "="*80)
    print("TEST 2: PLAYER IMPORT (Season Data)")
    print("="*80)
    
    from mcp_bets.services.cache.cached_client import CachedSportsDataIOClient
    from mcp_bets.services.ingestion.data_ingestion import IngestionService
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text
    
    settings = Settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    start_time = time.time()
    
    try:
        from mcp_bets.services.ingestion.sportsdataio_client import SportsDataIOClient
        client = SportsDataIOClient(api_key=settings.SPORTSDATAIO_API_KEY, base_url=settings.SPORTSDATAIO_BASE_URL)
        
        async with async_session() as session:
            service = IngestionService(session, client)
            
            print("\n📥 Importing all active players...")
            player_count = await service.import_all_players()
            
            # Verify database count
            result = await session.execute(text("SELECT COUNT(*) FROM players"))
            db_count = result.scalar()
            
            elapsed = time.time() - start_time
            
            print(f"✅ Imported {player_count} players in {elapsed:.2f}s")
            print(f"✅ Database contains {db_count} players")
            
            # Show position breakdown
            result = await session.execute(text("""
                SELECT position, COUNT(*) as count
                FROM players
                GROUP BY position
                ORDER BY count DESC
                LIMIT 10
            """))
            print("\n📋 Top Positions:")
            for row in result:
                print(f"  • {row[0]}: {row[1]} players")
            
            return {
                "status": "passed",
                "players_imported": player_count,
                "db_count": db_count,
                "elapsed_time": elapsed
            }
            
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "failed", "error": str(e)}


async def test_schedule_import():
    """Test schedule import for Week 18"""
    print("\n" + "="*80)
    print("TEST 3: SCHEDULE IMPORT (2024 Week 18)")
    print("="*80)
    
    from mcp_bets.services.cache.cached_client import CachedSportsDataIOClient
    from mcp_bets.services.ingestion.data_ingestion import IngestionService
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text
    
    settings = Settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    start_time = time.time()
    
    try:
        from mcp_bets.services.ingestion.sportsdataio_client import SportsDataIOClient
        client = SportsDataIOClient(api_key=settings.SPORTSDATAIO_API_KEY, base_url=settings.SPORTSDATAIO_BASE_URL)
        
        async with async_session() as session:
            service = IngestionService(session, client)
            
            # First import 2024 season
            print("\n📅 Creating 2024 season record...")
            from datetime import date
            
            await service.import_season(
                year=2024,
                start_date=date(2024, 9, 5),
                end_date=date(2025, 2, 9)
            )
            print(f"✅ Created 2024 season")
            
            print("\n📥 Importing Week 18 schedule...")
            game_count = await service.import_games_by_week(2024, 18)
            
            result = await session.execute(text("SELECT COUNT(*) FROM games WHERE week = 18"))
            db_count = result.scalar()
            
            elapsed = time.time() - start_time
            
            print(f"✅ Imported {game_count} games in {elapsed:.2f}s")
            print(f"✅ Database contains {db_count} Week 18 games")
            
            # Show sample games
            result = await session.execute(text("""
                SELECT g.game_date, ht.key as home, at.key as away
                FROM games g
                JOIN teams ht ON g.home_team_id = ht.id
                JOIN teams at ON g.away_team_id = at.id
                WHERE g.week = 18
                LIMIT 5
            """))
            print("\n📋 Sample Week 18 Games:")
            for row in result:
                print(f"  • {row[0]}: {row[1]} vs {row[2]}")
            
            return {
                "status": "passed",
                "games_imported": game_count,
                "db_count": db_count,
                "elapsed_time": elapsed
            }
            
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "failed", "error": str(e)}


async def test_cache_performance():
    """Test cache hit rate"""
    print("\n" + "="*80)
    print("TEST 4: CACHE PERFORMANCE")
    print("="*80)
    
    from mcp_bets.services.cache.cached_client import CachedSportsDataIOClient
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    settings = Settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    start_time = time.time()
    
    try:
        from mcp_bets.services.ingestion.sportsdataio_client import SportsDataIOClient
        client = SportsDataIOClient(api_key=settings.SPORTSDATAIO_API_KEY, base_url=settings.SPORTSDATAIO_BASE_URL)
        
        print("\n🔄 First call (cache miss expected)...")
        start = time.time()
        teams1 = await client.get_teams()
        first_time = time.time() - start
        print(f"  ⏱️  First call: {first_time:.3f}s (API call)")
        
        print("\n🔄 Second call (cache hit expected)...")
        start = time.time()
        teams2 = await client.get_teams()
        second_time = time.time() - start
        print(f"  ⏱️  Second call: {second_time:.3f}s (from cache)")
        
        speedup = first_time / second_time if second_time > 0 else 0
        print(f"\n⚡ Cache speedup: {speedup:.1f}x faster")
        
        # Check cache statistics
        async with async_session() as session:
            result = await session.execute(text("""
                SELECT data_type, COUNT(*) as entries
                FROM cache_entries
                GROUP BY data_type
                ORDER BY entries DESC
            """))
            
            print("\n📊 Cache Statistics:")
            total_entries = 0
            for row in result:
                print(f"  • {row[0]}: {row[1]} entries")
                total_entries += row[1]
            
            print(f"\n✅ Total cache entries: {total_entries}")
        
        elapsed = time.time() - start_time
        
        return {
            "status": "passed",
            "cache_speedup": speedup,
            "total_entries": total_entries,
            "elapsed_time": elapsed
        }
        
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "failed", "error": str(e)}


async def main():
    """Run all pipeline tests"""
    print("\n" + "="*80)
    print("🧪 MCP BETS - PHASE 1 FULL PIPELINE TEST")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    overall_start = time.time()
    results = {}
    
    # Test 1: Teams
    results["teams"] = await test_team_import()
    
    # Test 2: Players
    results["players"] = await test_player_import()
    
    # Test 3: Schedule
    results["schedule"] = await test_schedule_import()
    
    # Test 4: Cache
    results["cache"] = await test_cache_performance()
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results.values() if r.get("status") == "passed")
    failed = sum(1 for r in results.values() if r.get("status") == "failed")
    
    print(f"\n✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    overall_elapsed = time.time() - overall_start
    print(f"\n⏱️  Total runtime: {overall_elapsed:.2f}s")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED - Phase 1 pipeline operational!")
        print("\nNext steps:")
        print("  1. Review cache hit rates and performance")
        print("  2. Proceed to Phase 2 (RAG Knowledge Base)")
        print("  3. Consider installing pgvector for Phase 2")
    else:
        print("\n⚠️  Some tests failed - review errors above")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
