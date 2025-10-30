"""
Data Ingestion Service

Orchestrates importing data from SportsDataIO into the database.
Handles idempotent imports using external IDs.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mcp_bets.models import (
    Season,
    Team,
    Player,
    Game,
    Injury,
    PlayerGameStats,
    PlayerProp,
)
from mcp_bets.services.ingestion.sportsdataio_client import SportsDataIOClient


class IngestionService:
    """
    Data Ingestion Service
    
    Imports data from SportsDataIO API into database with:
    - Idempotent imports (no duplicates)
    - Relationship management
    - Error handling
    """
    
    def __init__(self, db: AsyncSession, client: SportsDataIOClient):
        self.db = db
        self.client = client
    
    # =========================================================================
    # Teams
    # =========================================================================
    
    async def import_teams(self) -> int:
        """
        Import all NFL teams
        
        Returns:
            Number of teams imported/updated
        """
        teams_data = await self.client.get_teams()
        count = 0
        
        for team_data in teams_data:
            # Check if team already exists
            result = await self.db.execute(
                select(Team).where(
                    Team.sportsdata_team_id == str(team_data["TeamID"])
                )
            )
            team = result.scalar_one_or_none()
            
            if team:
                # Update existing team
                team.name = team_data["FullName"]
                team.abbreviation = team_data["Key"]
                team.city = team_data["City"]
                team.conference = team_data["Conference"]
                team.division = team_data["Division"]
            else:
                # Create new team
                team = Team(
                    name=team_data["FullName"],
                    abbreviation=team_data["Key"],
                    city=team_data["City"],
                    conference=team_data["Conference"],
                    division=team_data["Division"],
                    sportsdata_team_id=str(team_data["TeamID"]),
                )
                self.db.add(team)
            
            count += 1
        
        await self.db.commit()
        return count
    
    # =========================================================================
    # Seasons
    # =========================================================================
    
    async def import_season(
        self,
        year: int,
        season_type: str = "Regular",
    ) -> Season:
        """
        Import/get a season
        
        Args:
            year: Season year (e.g., 2024)
            season_type: "Regular", "Postseason", or "Preseason"
        
        Returns:
            Season object
        """
        # Check if season exists
        result = await self.db.execute(
            select(Season).where(
                Season.year == year,
                Season.season_type == season_type,
            )
        )
        season = result.scalar_one_or_none()
        
        if not season:
            season = Season(
                year=year,
                season_type=season_type,
                sportsdata_season_id=f"{year}{season_type}",
            )
            self.db.add(season)
            await self.db.commit()
            await self.db.refresh(season)
        
        return season
    
    # =========================================================================
    # Games
    # =========================================================================
    
    async def import_games_by_week(
        self,
        season: int,
        week: int,
    ) -> int:
        """
        Import games for a specific week
        
        Args:
            season: Season year
            week: Week number
        
        Returns:
            Number of games imported/updated
        """
        # Ensure season exists
        season_obj = await self.import_season(season)
        
        # Get games from API
        games_data = await self.client.get_schedules_by_week(season, week)
        count = 0
        
        for game_data in games_data:
            # Get home and away teams
            home_team = await self._get_team_by_key(game_data["HomeTeam"])
            away_team = await self._get_team_by_key(game_data["AwayTeam"])
            
            if not home_team or not away_team:
                continue  # Skip if teams not found
            
            # Check if game exists
            result = await self.db.execute(
                select(Game).where(
                    Game.sportsdata_game_id == str(game_data["GameID"])
                )
            )
            game = result.scalar_one_or_none()
            
            # Parse game datetime
            game_datetime = None
            if game_data.get("Date"):
                game_datetime = datetime.fromisoformat(
                    game_data["Date"].replace("Z", "+00:00")
                )
            
            if game:
                # Update existing game
                game.season_id = season_obj.id
                game.week = week
                game.home_team_id = home_team.id
                game.away_team_id = away_team.id
                game.game_datetime = game_datetime
                game.home_score = game_data.get("HomeScore")
                game.away_score = game_data.get("AwayScore")
                game.is_final = game_data.get("IsClosed", False)
            else:
                # Create new game
                game = Game(
                    season_id=season_obj.id,
                    week=week,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    game_datetime=game_datetime,
                    home_score=game_data.get("HomeScore"),
                    away_score=game_data.get("AwayScore"),
                    is_final=game_data.get("IsClosed", False),
                    sportsdata_game_id=str(game_data["GameID"]),
                )
                self.db.add(game)
            
            count += 1
        
        await self.db.commit()
        return count
    
    # =========================================================================
    # Players
    # =========================================================================
    
    async def import_players_by_team(self, team_key: str) -> int:
        """
        Import all players for a team
        
        Args:
            team_key: Team abbreviation (e.g., "SF")
        
        Returns:
            Number of players imported/updated
        """
        team = await self._get_team_by_key(team_key)
        if not team:
            return 0
        
        players_data = await self.client.get_players_by_team(team_key)
        count = 0
        
        for player_data in players_data:
            # Check if player exists
            result = await self.db.execute(
                select(Player).where(
                    Player.sportsdata_player_id == str(player_data["PlayerID"])
                )
            )
            player = result.scalar_one_or_none()
            
            if player:
                # Update existing player
                player.first_name = player_data["FirstName"]
                player.last_name = player_data["LastName"]
                player.position = player_data.get("Position")
                player.jersey_number = player_data.get("Number")
                player.team_id = team.id
                player.is_active = player_data.get("Active", True)
            else:
                # Create new player
                player = Player(
                    first_name=player_data["FirstName"],
                    last_name=player_data["LastName"],
                    position=player_data.get("Position"),
                    jersey_number=player_data.get("Number"),
                    team_id=team.id,
                    sportsdata_player_id=str(player_data["PlayerID"]),
                    is_active=player_data.get("Active", True),
                )
                self.db.add(player)
            
            count += 1
        
        await self.db.commit()
        return count
    
    async def import_all_players(self) -> int:
        """
        Import all active NFL players
        
        Returns:
            Number of players imported/updated
        """
        players_data = await self.client.get_players()
        count = 0
        
        for player_data in players_data:
            # Get player's team
            team = None
            if player_data.get("Team"):
                team = await self._get_team_by_key(player_data["Team"])
            
            # Check if player exists
            result = await self.db.execute(
                select(Player).where(
                    Player.sportsdata_player_id == str(player_data["PlayerID"])
                )
            )
            player = result.scalar_one_or_none()
            
            if player:
                # Update existing player
                player.first_name = player_data["FirstName"]
                player.last_name = player_data["LastName"]
                player.position = player_data.get("Position")
                player.jersey_number = player_data.get("Number")
                player.team_id = team.id if team else None
                player.is_active = player_data.get("Active", True)
            else:
                # Create new player
                player = Player(
                    first_name=player_data["FirstName"],
                    last_name=player_data["LastName"],
                    position=player_data.get("Position"),
                    jersey_number=player_data.get("Number"),
                    team_id=team.id if team else None,
                    sportsdata_player_id=str(player_data["PlayerID"]),
                    is_active=player_data.get("Active", True),
                )
                self.db.add(player)
            
            count += 1
        
        await self.db.commit()
        return count
    
    # =========================================================================
    # Injuries
    # =========================================================================
    
    async def import_injuries_by_week(
        self,
        season: int,
        week: int,
    ) -> int:
        """
        Import injury reports for a specific week
        
        Args:
            season: Season year
            week: Week number
        
        Returns:
            Number of injury reports imported
        """
        # Ensure season exists
        season_obj = await self.import_season(season)
        
        # Get injuries from API
        injuries_data = await self.client.get_injuries_by_week(season, week)
        count = 0
        
        for injury_data in injuries_data:
            # Get player
            player = await self._get_player_by_id(str(injury_data["PlayerID"]))
            if not player:
                continue
            
            # Parse reported date
            reported_at = datetime.now(timezone.utc)
            if injury_data.get("Updated"):
                reported_at = datetime.fromisoformat(
                    injury_data["Updated"].replace("Z", "+00:00")
                )
            
            # Create injury report (don't update - track all reports)
            injury = Injury(
                player_id=player.id,
                season_id=season_obj.id,
                week=week,
                injury_status=injury_data.get("Status", "Unknown"),
                body_part=injury_data.get("BodyPart"),
                practice_status=injury_data.get("Practice"),
                practice_description=injury_data.get("PracticeDescription"),
                reported_at=reported_at,
            )
            self.db.add(injury)
            count += 1
        
        await self.db.commit()
        return count
    
    # =========================================================================
    # Player Props
    # =========================================================================
    
    async def import_player_props_by_week(
        self,
        season: int,
        week: int,
    ) -> int:
        """
        Import player props for a specific week
        
        Args:
            season: Season year
            week: Week number
        
        Returns:
            Number of props imported
        """
        props_data = await self.client.get_player_props_by_week(season, week)
        count = 0
        
        for prop_data in props_data:
            # Get player and game
            player = await self._get_player_by_id(str(prop_data["PlayerID"]))
            game = await self._get_game_by_id(str(prop_data["GameID"]))
            
            if not player or not game:
                continue
            
            # Parse posted time
            posted_at = datetime.now(timezone.utc)
            if prop_data.get("Created"):
                posted_at = datetime.fromisoformat(
                    prop_data["Created"].replace("Z", "+00:00")
                )
            
            # Create prop (track all line movements)
            prop = PlayerProp(
                player_id=player.id,
                game_id=game.id,
                sportsbook=prop_data.get("Sportsbook", "Unknown"),
                prop_type=prop_data.get("PropType", "Unknown"),
                line=prop_data.get("Line"),
                over_odds=prop_data.get("OverOdds"),
                under_odds=prop_data.get("UnderOdds"),
                posted_at=posted_at,
            )
            self.db.add(prop)
            count += 1
        
        await self.db.commit()
        return count
    
    # =========================================================================
    # Player Stats
    # =========================================================================
    
    async def import_player_stats_by_week(
        self,
        season: int,
        week: int,
    ) -> int:
        """
        Import player game stats for a specific week
        
        Args:
            season: Season year
            week: Week number
        
        Returns:
            Number of stat records imported/updated
        """
        stats_data = await self.client.get_player_game_stats_by_week(season, week)
        count = 0
        
        for stat_data in stats_data:
            # Get player and game
            player = await self._get_player_by_id(str(stat_data["PlayerID"]))
            game = await self._get_game_by_id(str(stat_data["GameID"]))
            
            if not player or not game:
                continue
            
            # Check if stats already exist
            result = await self.db.execute(
                select(PlayerGameStats).where(
                    PlayerGameStats.player_id == player.id,
                    PlayerGameStats.game_id == game.id,
                )
            )
            stats = result.scalar_one_or_none()
            
            if stats:
                # Update existing stats
                self._update_player_stats(stats, stat_data)
            else:
                # Create new stats
                stats = PlayerGameStats(
                    player_id=player.id,
                    game_id=game.id,
                )
                self._update_player_stats(stats, stat_data)
                self.db.add(stats)
            
            count += 1
        
        await self.db.commit()
        return count
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    async def _get_team_by_key(self, team_key: str) -> Optional[Team]:
        """Get team by abbreviation"""
        result = await self.db.execute(
            select(Team).where(Team.abbreviation == team_key)
        )
        return result.scalar_one_or_none()
    
    async def _get_player_by_id(self, sportsdata_id: str) -> Optional[Player]:
        """Get player by SportsDataIO ID"""
        result = await self.db.execute(
            select(Player).where(Player.sportsdata_player_id == sportsdata_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_game_by_id(self, sportsdata_id: str) -> Optional[Game]:
        """Get game by SportsDataIO ID"""
        result = await self.db.execute(
            select(Game).where(Game.sportsdata_game_id == sportsdata_id)
        )
        return result.scalar_one_or_none()
    
    def _update_player_stats(
        self,
        stats: PlayerGameStats,
        data: Dict,
    ) -> None:
        """Update player stats from API data"""
        # Passing stats
        stats.passing_attempts = data.get("PassingAttempts")
        stats.passing_completions = data.get("PassingCompletions")
        stats.passing_yards = data.get("PassingYards")
        stats.passing_tds = data.get("PassingTouchdowns")
        stats.interceptions = data.get("Interceptions")
        
        # Rushing stats
        stats.rushing_attempts = data.get("RushingAttempts")
        stats.rushing_yards = data.get("RushingYards")
        stats.rushing_tds = data.get("RushingTouchdowns")
        
        # Receiving stats
        stats.receptions = data.get("Receptions")
        stats.receiving_targets = data.get("ReceivingTargets")
        stats.receiving_yards = data.get("ReceivingYards")
        stats.receiving_tds = data.get("ReceivingTouchdowns")
        
        # Other stats
        stats.fumbles = data.get("Fumbles")
        stats.fumbles_lost = data.get("FumblesLost")
        stats.fantasy_points = data.get("FantasyPoints")
