"""
Generate Synthetic Sample Data for RAG Pipeline Testing

Creates realistic sample data without requiring SportsDataIO API access:
- Teams (3-5 teams)
- Players (15-20 players)
- Games (5-10 games)
- Player stats (50-100 records)
- Embeddings will be generated during test

Cost: $0 (synthetic data)
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from mcp_bets.config.settings import Settings
from mcp_bets.models.base import Base
from mcp_bets.models.season import Season
from mcp_bets.models.team import Team
from mcp_bets.models.player import Player
from mcp_bets.models.game import Game
from mcp_bets.models.player_game_stats import PlayerGameStats


# Sample data templates
TEAMS_DATA = [
    {
        "key": "ATL", "city": "Atlanta", "name": "Falcons",
        "conference": "NFC", "division": "South",
        "stadium_name": "Mercedes-Benz Stadium", "stadium_capacity": 71000
    },
    {
        "key": "TB", "city": "Tampa Bay", "name": "Buccaneers",
        "conference": "NFC", "division": "South",
        "stadium_name": "Raymond James Stadium", "stadium_capacity": 65890
    },
    {
        "key": "NO", "city": "New Orleans", "name": "Saints",
        "conference": "NFC", "division": "South",
        "stadium_name": "Caesars Superdome", "stadium_capacity": 73208
    },
    {
        "key": "CAR", "city": "Carolina", "name": "Panthers",
        "conference": "NFC", "division": "South",
        "stadium_name": "Bank of America Stadium", "stadium_capacity": 75523
    }
]

PLAYERS_DATA = [
    # Atlanta Falcons
    {"team_key": "ATL", "first_name": "Desmond", "last_name": "Ridder", "position": "QB", "jersey": 9, "status": "Active"},
    {"team_key": "ATL", "first_name": "Bijan", "last_name": "Robinson", "position": "RB", "jersey": 7, "status": "Active"},
    {"team_key": "ATL", "first_name": "Tyler", "last_name": "Allgeier", "position": "RB", "jersey": 25, "status": "Active"},
    {"team_key": "ATL", "first_name": "Drake", "last_name": "London", "position": "WR", "jersey": 5, "status": "Active"},
    {"team_key": "ATL", "first_name": "Kyle", "last_name": "Pitts", "position": "TE", "jersey": 8, "status": "Active"},
    
    # Tampa Bay Buccaneers
    {"team_key": "TB", "first_name": "Baker", "last_name": "Mayfield", "position": "QB", "jersey": 6, "status": "Active"},
    {"team_key": "TB", "first_name": "Rachaad", "last_name": "White", "position": "RB", "jersey": 29, "status": "Active"},
    {"team_key": "TB", "first_name": "Mike", "last_name": "Evans", "position": "WR", "jersey": 13, "status": "Active"},
    {"team_key": "TB", "first_name": "Chris", "last_name": "Godwin", "position": "WR", "jersey": 14, "status": "Active"},
    
    # New Orleans Saints
    {"team_key": "NO", "first_name": "Derek", "last_name": "Carr", "position": "QB", "jersey": 4, "status": "Active"},
    {"team_key": "NO", "first_name": "Alvin", "last_name": "Kamara", "position": "RB", "jersey": 41, "status": "Active"},
    {"team_key": "NO", "first_name": "Chris", "last_name": "Olave", "position": "WR", "jersey": 12, "status": "Active"},
    {"team_key": "NO", "first_name": "Michael", "last_name": "Thomas", "position": "WR", "jersey": 13, "status": "Active"},
    
    # Carolina Panthers
    {"team_key": "CAR", "first_name": "Bryce", "last_name": "Young", "position": "QB", "jersey": 9, "status": "Active"},
    {"team_key": "CAR", "first_name": "Miles", "last_name": "Sanders", "position": "RB", "jersey": 26, "status": "Active"},
    {"team_key": "CAR", "first_name": "DJ", "last_name": "Moore", "position": "WR", "jersey": 2, "status": "Active"},
    {"team_key": "CAR", "first_name": "Adam", "last_name": "Thielen", "position": "WR", "jersey": 19, "status": "Active"},
]


async def generate_synthetic_data():
    """Generate synthetic sample data for testing"""
    
    print("=" * 80)
    print("📊 Generating Synthetic Sample Data for RAG Testing")
    print("=" * 80)
    
    settings = Settings()
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # Step 1: Create season
            print("\n📅 Step 1: Creating 2024 season...")
            from datetime import date
            season = Season(
                id=uuid.uuid4(),
                year=2024,
                start_date=date(2024, 9, 5),
                end_date=date(2025, 2, 9)
            )
            session.add(season)
            await session.flush()
            print(f"✅ Season 2024 created: {season.id}")
            
            # Step 2: Create teams
            print("\n🏈 Step 2: Creating teams...")
            teams_map = {}
            for team_data in TEAMS_DATA:
                team = Team(
                    id=uuid.uuid4(),
                    team_id=team_data["key"],
                    key=team_data["key"],
                    city=team_data["city"],
                    name=team_data["name"],
                    conference=team_data["conference"],
                    division=team_data["division"]
                )
                session.add(team)
                teams_map[team.key] = team
                print(f"  ✅ {team.full_name}")
            
            await session.flush()
            print(f"\n✅ Created {len(TEAMS_DATA)} teams")
            
            # Step 3: Create players
            print("\n👥 Step 3: Creating players...")
            players_map = {}
            for idx, player_data in enumerate(PLAYERS_DATA):
                team = teams_map[player_data["team_key"]]
                player = Player(
                    id=uuid.uuid4(),
                    player_id=f"SYNTH-{idx+1:04d}",
                    first_name=player_data["first_name"],
                    last_name=player_data["last_name"],
                    position=player_data["position"],
                    jersey_number=player_data["jersey"],
                    status=player_data["status"],
                    team_id=team.id
                )
                session.add(player)
                players_map[f"{player.first_name}_{player.last_name}"] = player
                print(f"  ✅ #{player.jersey_number} {player.first_name} {player.last_name} ({player.position}) - {team.full_name}")
            
            await session.flush()
            print(f"\n✅ Created {len(PLAYERS_DATA)} players")
            
            # Step 4: Create games
            print("\n🏟️  Step 4: Creating games...")
            games = []
            game_date = datetime(2024, 9, 8)  # Week 1 start
            
            # Create 6 games (3 matchups between division rivals)
            matchups = [
                ("ATL", "TB", 24, 17),  # Week 1
                ("NO", "CAR", 28, 10),  # Week 1
                ("TB", "ATL", 20, 13),  # Week 5
                ("CAR", "NO", 14, 24),  # Week 5
                ("ATL", "NO", 31, 28),  # Week 9
                ("TB", "CAR", 27, 10),  # Week 9
            ]
            
            for i, (home_key, away_key, home_score, away_score) in enumerate(matchups):
                home_team = teams_map[home_key]
                away_team = teams_map[away_key]
                
                # Calculate week (weeks 1, 5, 9)
                week = (i // 2) * 4 + 1
                game_date_calc = game_date + timedelta(weeks=week-1)
                
                game = Game(
                    id=uuid.uuid4(),
                    game_id=f"2024-W{week:02d}-{away_key}-{home_key}",
                    season_id=season.id,
                    week=week,
                    game_date=game_date_calc,
                    status="Final",
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    home_score=home_score,
                    away_score=away_score
                )
                session.add(game)
                games.append((game, home_team, away_team))
                print(f"  ✅ Week {week}: {away_team.key} @ {home_team.key} ({away_score}-{home_score})")
            
            await session.flush()
            print(f"\n✅ Created {len(games)} games")
            
            # Step 5: Create player stats
            print("\n📊 Step 5: Creating player stats...")
            stats_count = 0
            
            for game, home_team, away_team in games:
                # Generate stats for key players from both teams
                for player_key, player in players_map.items():
                    # Only generate stats for players on teams playing this game
                    if player.team_id not in (home_team.id, away_team.id):
                        continue
                    
                    # Generate position-specific stats
                    stats = PlayerGameStats(
                        id=uuid.uuid4(),
                        player_id=player.id,
                        game_id=game.id
                    )
                    
                    if player.position == "QB":
                        stats.passing_attempts = 32
                        stats.passing_completions = 22
                        stats.passing_yards = 285
                        stats.passing_tds = 2
                        stats.interceptions = 1
                        stats.rushing_attempts = 3
                        stats.rushing_yards = 12
                    
                    elif player.position == "RB":
                        stats.rushing_attempts = 18
                        stats.rushing_yards = 87
                        stats.rushing_tds = 1
                        stats.receiving_targets = 5
                        stats.receptions = 4
                        stats.receiving_yards = 32
                    
                    elif player.position == "WR":
                        stats.receiving_targets = 9
                        stats.receptions = 6
                        stats.receiving_yards = 94
                        stats.receiving_tds = 1
                    
                    elif player.position == "TE":
                        stats.receiving_targets = 7
                        stats.receptions = 5
                        stats.receiving_yards = 68
                        stats.receiving_tds = 1
                    
                    session.add(stats)
                    stats_count += 1
            
            await session.flush()
            print(f"✅ Created {stats_count} player stat records")
            
            # Commit all changes
            await session.commit()
            
            # Verify data
            print("\n" + "=" * 80)
            print("📈 Verifying Data Import")
            print("=" * 80)
            
            teams_result = await session.execute(select(Team))
            teams = teams_result.scalars().all()
            print(f"✅ Teams: {len(teams)}")
            
            players_result = await session.execute(select(Player))
            players = players_result.scalars().all()
            print(f"✅ Players: {len(players)}")
            
            games_result = await session.execute(select(Game))
            games = games_result.scalars().all()
            print(f"✅ Games: {len(games)}")
            
            stats_result = await session.execute(select(PlayerGameStats))
            stats = stats_result.scalars().all()
            print(f"✅ Player Stats: {len(stats)}")
            
            print("\n" + "=" * 80)
            print("🎯 Ready to test RAG pipeline!")
            print("=" * 80)
            print("\nNext steps:")
            print("  1. Run: python3 scripts/test_rag_pipeline.py")
            print("  2. Review chunking quality and token counts")
            print("  3. Validate embedding generation and storage")
            print("  4. Test semantic search relevance")
            print("\n💰 Estimated embedding cost: ~$0.001 (synthetic data)")
            
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(generate_synthetic_data())
