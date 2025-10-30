"""
NFL Season Model

Represents an NFL season (year) with start/end dates.
"""

from sqlalchemy import Column, String, Date, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid

from mcp_bets.models.base import Base, TimestampMixin


class Season(Base, TimestampMixin):
    """NFL Season"""
    
    __tablename__ = "seasons"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    year = Column(Integer, unique=True, nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    def __repr__(self):
        return f"<Season {self.year}>"
