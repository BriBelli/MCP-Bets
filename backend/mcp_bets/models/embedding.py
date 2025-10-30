"""
Embeddings Model for RAG Knowledge Base

Stores vector embeddings for semantic search using pgvector extension.
"""

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
import uuid

from mcp_bets.models.base import Base, TimestampMixin


class Embedding(Base, TimestampMixin):
    """Vector Embedding for RAG Knowledge Base"""
    
    __tablename__ = "embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    embedding = Column(Vector(3072), nullable=False)  # OpenAI text-embedding-3-large dimension
    document_chunk = Column(Text, nullable=False)
    metadata = Column(JSONB, nullable=False)  # Flexible metadata storage
    
    # Metadata structure example:
    # {
    #   "data_type": "player_profile" | "injury_report" | "game_log" | "matchup_analytics" | "weather" | "vegas_lines",
    #   "player_id": "uuid",
    #   "team_id": "uuid",
    #   "opponent_id": "uuid",
    #   "game_id": "uuid",
    #   "season": 2024,
    #   "week": 8,
    #   "confidence_score": 0.95,
    #   "source": "sportsdata.io",
    #   "last_verified": "2024-10-23T10:00:00Z"
    # }
    
    def __repr__(self):
        data_type = self.metadata.get("data_type", "unknown") if self.metadata else "unknown"
        return f"<Embedding {data_type} - {self.document_chunk[:50]}...>"
