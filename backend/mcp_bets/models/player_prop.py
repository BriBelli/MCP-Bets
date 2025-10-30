"""
Player Props Model

Represents betting props for players (rushing yards, receptions, etc.)
from various sportsbooks.
"""

from sqlalchemy import Column, String, Integer, DECIMAL, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from mcp_bets.models.base import Base, TimestampMixin


class PlayerProp(Base, TimestampMixin):
    """Player Betting Prop"""
    
    __tablename__ = "player_props"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False, index=True)
    sportsbook = Column(String(100), nullable=False, index=True)  # "FanDuel", "DraftKings", etc.
    prop_type = Column(String(100), nullable=False, index=True)  # "rushing_yards", "receptions", etc.
    line = Column(DECIMAL(10, 2), nullable=False)  # e.g., 100.5
    over_odds = Column(Integer)  # e.g., -110
    under_odds = Column(Integer)  # e.g., -110
    posted_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    player = relationship("Player", backref="props")
    game = relationship("Game", backref="player_props")
    
    def __repr__(self):
        return f"<PlayerProp {self.player.full_name if self.player else '?'} {self.prop_type} {self.line}>"
