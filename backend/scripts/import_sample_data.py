"""
Import Sample Data for RAG Testing

Fetches minimal sample data from SportsDataIO:
- 1 team (Atlanta Falcons - Bijan Robinson's team)
- 5-10 players from that team
- Recent games (last 3-5)
- Player stats for those games

This provides enough data to test the RAG pipeline without full hydration.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from mcp_bets.config.settings import Settings
from mcp_bets.services.ingestion.sportsdataio_client import SportsDataIOClient
from mcp_bets.models.team import Team
from mcp_bets.models.player import Player
from mcp_bets.models.season import Season
from mcp_bets.models.game import Game
from mcp_bets.models.player_game_stats import PlayerGameStats


async def import_sample_data():
    """Import minimal sample data for testing"""
    
    print("=" * 80)
    print("📥 Importing Sample Data for RAG Testing")
    print("=" * 80)
    print()
    
    settings = Settings()
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    client = SportsDataIOClient(
        api_key=settings.SPORTSDATAIO_API_KEY,
        base_url=settings.SPORTSDATAIO_BASE_URL,
        requests_per_second=settings.SPORTSDATAIO_REQUESTS_PER_SECOND
    )
    
    try:
        async with async_session() as session:
            # Step 1: Import 2024 season
            print("📅 Step 1: Creating 2024 season...")
            season_2024 = Season(
                year=2024,
                start_date=datetime(2024, 9, 5).date(),
                end_date=datetime(2025, 2, 9).date()
            )
            session.add(season_2024)
            await session.flush()
            print(f"✅ Season 2024 created: {season_2024.id}")
            
            # Step 2: Import teams (just get all teams, it's fast)
            print("\n🏈 Step 2: Importing NFL teams...")
            teams_data = await client.get_teams()
            teams_map = {}
            
            for team_data in teams_data:
                team = Team(
                    team_id=str(team_data["TeamID"]),
                    key=team_data["Key"],
                    city=team_data["City"],
                    name=team_data["Name"],
                    conference=team_data.get("Conference"),
                    division=team_data.get("Division")
                )
                session.add(team)
                teams_map[team_data["Key"]] = team
            
            await session.flush()
            print(f"✅ Imported {len(teams_map)} teams")
            
            # Step 3: Import Atlanta Falcons players (Bijan Robinson's team)
            print("\n👥 Step 3: Importing Atlanta Falcons players...")
            atl_team = teams_map.get("ATL")
            
            if not atl_team:
                print("❌ Atlanta Falcons not found")
                return
            
            players_data = await client.get_players_by_team("ATL")
            players_imported = 0
            bijan_robinson = None
            
            for player_data in players_data[:15]:  # Import top 15 players
                player = Player(
                    player_id=str(player_data["PlayerID"]),
                    first_name=player_data["FirstName"],
                    last_name=player_data["LastName"],
                    team_id=atl_team.id,
                    position=player_data["Position"],
                    jersey_number=player_data.get("Number"),
                    status=player_data.get("Status"),
                    height=player_data.get("Height"),
                    weight=player_data.get("Weight"),
                    college=player_data.get("College")
                )
                session.add(player)
                players_imported += 1
                
                # Find Bijan Robinson
                if "bijan" in player_data["FirstName"].lower():
                    bijan_robinson = player
                    print(f"   🌟 Found Bijan Robinson!")
            
            await session.flush()
            print(f"✅ Imported {players_imported} players")
            
            # Step 4: Import recent Falcons games (Week 1-8 of 2024)
            print("\n🏟️  Step 4: Importing recent games...")
            games_imported = 0
            
            for week in range(1, 9):  # Weeks 1-8
                try:
                    schedule_data = await client.get_schedules_by_week(2024, week)
                    
                    for game_data in schedule_data:
                        # Only import Falcons games
                        if game_data.get("AwayTeam") != "ATL" and game_data.get("HomeTeam") != "ATL":
                            continue
                        
                        away_team = teams_map.get(game_data["AwayTeam"])
                        home_team = teams_map.get(game_data["HomeTeam"])
                        
                        if not away_team or not home_team:
                            continue
                        
                        game = Game(
                            game_id=str(game_data["GameKey"]),
                            season_id=season_2024.id,
                            week=week,
                            home_team_id=home_team.id,
                            away_team_id=away_team.id,
                            game_date=datetime.fromisoformat(game_data["Date"].replace("Z", "+00:00")),
                            stadium=game_data.get("StadiumDetails", {}).get("Name"),
                            channel=game_data.get("Channel"),
                            status=game_data.get("Status"),
                            home_score=game_data.get("HomeScore"),
                            away_score=game_data.get("AwayScore")
                        )
                        session.add(game)
                        games_imported += 1
                
                except Exception as e:
                    print(f"   ⚠️  Week {week}: {e}")
                    continue
            
            await session.flush()
            print(f"✅ Imported {games_imported} games")
            
            # Step 5: Import player stats for those games
            print("\n📊 Step 5: Importing player stats...")
            stats_imported = 0
            
            # Get all games we just imported
            result = await session.execute(
                "SELECT id, game_id, week FROM games WHERE season_id = :season_id",
                {"season_id": season_2024.id}
            )
            games = result.fetchall()
            
            for game_id_uuid, game_key, week in games[:5]:  # Just first 5 games for speed
                try:
                    stats_data = await client.get_box_score_by_game(game_key)
                    
                    if not stats_data or "PlayerGames" not in stats_data:
                        continue
                    
                    for stat_data in stats_data["PlayerGames"]:
                        # Find player in our database
                        player_result = await session.execute(
                            "SELECT id FROM players WHERE player_id = :player_id",
                            {"player_id": str(stat_data["PlayerID"])}
                        )
                        player_row = player_result.fetchone()
                        
                        if not player_row:
                            continue
                        
                        stat = PlayerGameStats(
                            player_id=player_row[0],
                            game_id=game_id_uuid,
                            passing_attempts=stat_data.get("PassingAttempts"),
                            passing_completions=stat_data.get("PassingCompletions"),
                            passing_yards=stat_data.get("PassingYards"),
                            passing_tds=stat_data.get("PassingTouchdowns"),
                            interceptions=stat_data.get("PassingInterceptions"),
                            rushing_attempts=stat_data.get("RushingAttempts"),
                            rushing_yards=stat_data.get("RushingYards"),
                            rushing_tds=stat_data.get("RushingTouchdowns"),
                            receptions=stat_data.get("Receptions"),
                            receiving_targets=stat_data.get("ReceivingTargets"),
                            receiving_yards=stat_data.get("ReceivingYards"),
                            receiving_tds=stat_data.get("ReceivingTouchdowns"),
                            fumbles=stat_data.get("Fumbles"),
                            fumbles_lost=stat_data.get("FumblesLost"),
                            fantasy_points=stat_data.get("FantasyPoints")
                        )
                        session.add(stat)
                        stats_imported += 1
                
                except Exception as e:
                    print(f"   ⚠️  Stats error: {e}")
                    continue
            
            await session.flush()
            print(f"✅ Imported {stats_imported} player stat records")
            
            # Commit all changes
            await session.commit()
            
            print("\n" + "=" * 80)
            print("✅ Sample Data Import Complete!")
            print("=" * 80)
            print(f"\nImported:")
            print(f"  - 1 season (2024)")
            print(f"  - {len(teams_map)} teams")
            print(f"  - {players_imported} players")
            print(f"  - {games_imported} games")
            print(f"  - {stats_imported} player stats")
            print(f"\n🎯 Ready to test RAG pipeline!")
            
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(import_sample_data())
