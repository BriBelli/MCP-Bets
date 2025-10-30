"""
Player Injury Model

Tracks injury reports, practice status, and injury details for players.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from mcp_bets.models.base import Base, TimestampMixin


class Injury(Base, TimestampMixin):
    """Player Injury Report"""
    
    __tablename__ = "injuries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    season_id = Column(UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=False)
    week = Column(Integer, nullable=False, index=True)
    injury_status = Column(String(50), nullable=False)  # "Out", "Questionable", "Doubtful", etc.
    body_part = Column(String(100))  # "Ankle", "Hamstring", etc.
    practice_status = Column(String(50))  # "Full", "Limited", "DNP"
    practice_description = Column(Text)  # Additional notes
    reported_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    player = relationship("Player", backref="injuries")
    season = relationship("Season")
    
    def __repr__(self):
        return f"<Injury {self.player.full_name if self.player else '?'} - {self.injury_status}>"
