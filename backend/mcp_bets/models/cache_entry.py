"""
Cache Entries Model

Stores warm cache data in PostgreSQL for fallback when Redis is unavailable.
"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from mcp_bets.models.base import Base, TimestampMixin


class CacheEntry(Base, TimestampMixin):
    """Cache Entry (Warm Cache in PostgreSQL)"""
    
    __tablename__ = "cache_entries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(500), unique=True, nullable=False, index=True)
    data = Column(JSONB, nullable=False)
    cached_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    data_type = Column(String(100), nullable=False, index=True)  # "odds", "injuries", "props", etc.
    
    def __repr__(self):
        return f"<CacheEntry {self.key} ({self.data_type})>"
    
    @property
    def is_expired(self):
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.expires_at
