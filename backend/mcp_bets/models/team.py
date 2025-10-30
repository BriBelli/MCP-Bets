"""
NFL Team Model

Represents an NFL team with city, name, conference, and division.
"""

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
import uuid

from mcp_bets.models.base import Base, TimestampMixin


class Team(Base, TimestampMixin):
    """NFL Team"""
    
    __tablename__ = "teams"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(String(10), unique=True, nullable=False, index=True)  # From SportsDataIO
    key = Column(String(10), nullable=False)  # e.g., "ATL", "BUF"
    city = Column(String(100), nullable=False)  # e.g., "Atlanta", "Buffalo"
    name = Column(String(100), nullable=False)  # e.g., "Falcons", "Bills"
    conference = Column(String(3))  # "NFC" or "AFC"
    division = Column(String(10))  # e.g., "South", "East"
    
    def __repr__(self):
        return f"<Team {self.key} - {self.city} {self.name}>"
    
    @property
    def full_name(self):
        return f"{self.city} {self.name}"
