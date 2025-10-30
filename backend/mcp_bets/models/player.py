"""
NFL Player Model

Represents an NFL player with position, team, and biographical info.
"""

from sqlalchemy import Column, String, Integer, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from mcp_bets.models.base import Base, TimestampMixin


class Player(Base, TimestampMixin):
    """NFL Player"""
    
    __tablename__ = "players"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(String(50), unique=True, nullable=False, index=True)  # From SportsDataIO
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"))
    position = Column(String(10), nullable=False, index=True)  # e.g., "RB", "WR", "QB"
    jersey_number = Column(Integer)
    status = Column(String(50))  # e.g., "Active", "Injured", "Inactive"
    height = Column(String(10))  # e.g., "6-0"
    weight = Column(Integer)  # pounds
    birth_date = Column(Date)
    college = Column(String(200))
    
    # Relationship
    team = relationship("Team", backref="players")
    
    def __repr__(self):
        return f"<Player {self.first_name} {self.last_name} ({self.position})>"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
