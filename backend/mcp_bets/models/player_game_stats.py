"""
Player Game Stats Model

Stores actual player performance statistics for each game.
"""

from sqlalchemy import Column, String, Integer, DECIMAL, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from mcp_bets.models.base import Base, TimestampMixin


class PlayerGameStats(Base, TimestampMixin):
    """Player Performance Statistics for a Game"""
    
    __tablename__ = "player_game_stats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False, index=True)
    
    # Passing Stats
    passing_attempts = Column(Integer)
    passing_completions = Column(Integer)
    passing_yards = Column(Integer)
    passing_tds = Column(Integer)
    interceptions = Column(Integer)
    
    # Rushing Stats
    rushing_attempts = Column(Integer)
    rushing_yards = Column(Integer)
    rushing_tds = Column(Integer)
    
    # Receiving Stats
    receptions = Column(Integer)
    receiving_targets = Column(Integer)
    receiving_yards = Column(Integer)
    receiving_tds = Column(Integer)
    
    # Other Stats
    fumbles = Column(Integer)
    fumbles_lost = Column(Integer)
    fantasy_points = Column(DECIMAL(6, 2))  # Standard fantasy points
    
    # Relationships
    player = relationship("Player", backref="game_stats")
    game = relationship("Game", backref="player_game_stats")
    
    def __repr__(self):
        return f"<PlayerGameStats {self.player.full_name if self.player else '?'} - Game {self.game_id}>"
