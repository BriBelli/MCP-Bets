"""
API Request Telemetry Model

Tracks all API requests for cost monitoring and usage analytics.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid

from mcp_bets.models.base import Base


class APIRequest(Base):
    """API Request Telemetry"""
    
    __tablename__ = "api_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint = Column(String(500), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)  # "success" or "error"
    status_code = Column(Integer)
    duration_ms = Column(Integer, nullable=False)
    error_message = Column(Text)
    requested_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    def __repr__(self):
        return f"<APIRequest {self.endpoint} - {self.status}>"
