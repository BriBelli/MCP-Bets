"""
NFL Game Model

Represents an NFL game with teams, scores, spread, and over/under.
"""

from sqlalchemy import Column, String, Integer, DateTime, DECIMAL, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from mcp_bets.models.base import Base, TimestampMixin


class Game(Base, TimestampMixin):
    """NFL Game"""
    
    __tablename__ = "games"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id = Column(String(50), unique=True, nullable=False, index=True)  # From SportsDataIO
    season_id = Column(UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=False)
    week = Column(Integer, nullable=False)
    home_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    game_date = Column(DateTime(timezone=True), nullable=False, index=True)
    stadium = Column(String(200))
    channel = Column(String(50))
    status = Column(String(50))  # e.g., "Scheduled", "InProgress", "Final"
    home_score = Column(Integer)
    away_score = Column(Integer)
    spread = Column(DECIMAL(5, 2))  # e.g., -3.5 (home team favored)
    over_under = Column(DECIMAL(5, 2))  # e.g., 47.5 total points
    
    # Relationships
    season = relationship("Season", backref="games")
    home_team = relationship("Team", foreign_keys=[home_team_id], backref="home_games")
    away_team = relationship("Team", foreign_keys=[away_team_id], backref="away_games")
    
    def __repr__(self):
        return f"<Game {self.away_team.key if self.away_team else '?'} @ {self.home_team.key if self.home_team else '?'} Week {self.week}>"
