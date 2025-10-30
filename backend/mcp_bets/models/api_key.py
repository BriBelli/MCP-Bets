"""
API Keys Model for Public API Gateway

Manages API keys for third-party developers using MCP Bets API.
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid

from mcp_bets.models.base import Base, TimestampMixin


class APIKey(Base, TimestampMixin):
    """API Key for Public API Access"""
    
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)  # Hashed API key
    key_prefix = Column(String(10), nullable=False)  # First 10 chars for display (e.g., "sk_live_abc")
    tier = Column(String(20), nullable=False, index=True)  # "free", "pro", "enterprise"
    rate_limit_per_day = Column(Integer, nullable=False)  # Max requests per day
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True))  # Optional expiration
    last_used_at = Column(DateTime(timezone=True))
    
    # Tier limits:
    # Free: 100 requests/day
    # Pro: 1,000 requests/day
    # Enterprise: Unlimited (9999999)
    
    def __repr__(self):
        return f"<APIKey {self.key_prefix}... ({self.tier})>"
