"""
Semantic Search Service for RAG Knowledge Base

Retrieves relevant context using vector similarity search with pgvector.
Implements filtering, ranking, and deduplication for optimal retrieval.
"""

import time
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import JSONB
import logging

from mcp_bets.models.embedding import Embedding
from mcp_bets.services.rag.embeddings_service import EmbeddingsService

logger = logging.getLogger(__name__)


class SearchResult:
    """Represents a single search result with relevance score"""
    
    def __init__(
        self,
        chunk: str,
        metadata: Dict[str, Any],
        distance: float,
        rank: int
    ):
        self.chunk = chunk
        self.metadata = metadata
        self.distance = distance
        self.similarity = 1 - distance  # Convert distance to similarity
        self.rank = rank
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "chunk": self.chunk,
            "metadata": self.metadata,
            "distance": self.distance,
            "similarity": self.similarity,
            "rank": self.rank
        }


class SemanticSearch:
    """
    Semantic search using pgvector HNSW index
    
    Features:
    - Vector similarity search (<=> cosine distance)
    - JSONB metadata filtering
    - Result ranking and deduplication
    - Query rewriting and expansion
    """
    
    def __init__(
        self,
        session: AsyncSession,
        embeddings_service: EmbeddingsService
    ):
        self.session = session
        self.embeddings_service = embeddings_service
    
    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        min_similarity: float = 0.0,
        rerank: bool = True
    ) -> List[SearchResult]:
        """
        Search for relevant document chunks
        
        Args:
            query: Natural language query
            top_k: Number of results to return
            filters: JSONB metadata filters (e.g., {"season": 2024, "position": "RB"})
            min_similarity: Minimum similarity threshold (0-1)
            rerank: Apply reranking logic
            
        Returns:
            List of SearchResult objects ranked by relevance
        """
        start_time = time.time()
        
        # Generate query embedding
        query_embedding = await self.embeddings_service.generate_embedding(query)
        
        # Build query with filters
        stmt = select(
            Embedding.document_chunk,
            Embedding.meta,
            Embedding.embedding.cosine_distance(query_embedding).label("distance")
        )
        
        # Apply metadata filters
        if filters:
            conditions = []
            for key, value in filters.items():
                if isinstance(value, list):
                    # Match any value in list
                    conditions.append(
                        Embedding.meta[key].astext.in_([str(v) for v in value])
                    )
                elif value is not None:
                    conditions.append(
                        Embedding.meta[key].astext == str(value)
                    )
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
        
        # Apply similarity threshold
        max_distance = 1 - min_similarity
        stmt = stmt.where(
            Embedding.embedding.cosine_distance(query_embedding) <= max_distance
        )
        
        # Order by similarity and limit
        # Fetch extra results for deduplication
        fetch_limit = top_k * 2
        stmt = stmt.order_by("distance").limit(fetch_limit)
        
        # Execute query
        result = await self.session.execute(stmt)
        rows = result.all()
        
        # Convert to SearchResult objects
        results = [
            SearchResult(
                chunk=row.document_chunk,
                metadata=row.meta,
                distance=row.distance,
                rank=i + 1
            )
            for i, row in enumerate(rows)
        ]
        
        # Deduplicate similar chunks
        results = self._deduplicate_results(results)
        
        # Rerank if requested
        if rerank:
            results = self._rerank_results(results, query)
        
        # Limit to top_k
        results = results[:top_k]
        
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        query_preview = query[:50].replace('{', '{{').replace('}', '}}')
        top_sim = f"{results[0].similarity:.3f}" if results else "0.000"
        logger.info(
            f"Search completed in {elapsed_time:.1f}ms: "
            f"query='{query_preview}...', results={len(results)}, "
            f"top_similarity={top_sim}"
        )
        
        return results
    
    async def search_by_player(
        self,
        player_name: str,
        query: str,
        season: Optional[int] = None,
        data_types: Optional[List[str]] = None,
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        Search for context about specific player
        
        Args:
            player_name: Player's full name
            query: Natural language query
            season: Filter by season year
            data_types: Filter by data types (e.g., ["player_profile", "game_log"])
            top_k: Number of results
            
        Returns:
            List of SearchResult objects
        """
        filters = {"player_name": player_name}
        
        if season:
            filters["season"] = season
        
        if data_types:
            filters["data_type"] = data_types
        
        return await self.search(query, top_k=top_k, filters=filters)
    
    async def search_by_matchup(
        self,
        player_name: str,
        opponent_team_id: str,
        week: int,
        season: int,
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        Search for matchup-specific context
        
        Args:
            player_name: Player's full name
            opponent_team_id: Opponent team UUID
            week: Week number
            season: Season year
            top_k: Number of results
            
        Returns:
            List of SearchResult objects
        """
        query = f"{player_name} performance against opponent week {week}"
        
        filters = {
            "player_name": player_name,
            "season": season,
            "data_type": ["matchup_analytics", "game_log"]
        }
        
        return await self.search(query, top_k=top_k, filters=filters)
    
    async def retrieve_context(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        max_tokens: int = 2500
    ) -> str:
        """
        Retrieve concatenated context for LLM prompt
        
        Args:
            query: Natural language query
            filters: Optional metadata filters
            max_tokens: Maximum tokens to return (for LLM context window)
            
        Returns:
            Concatenated context string ready for LLM prompt
        """
        # Search with higher top_k to ensure we have enough content
        results = await self.search(
            query,
            top_k=20,
            filters=filters,
            min_similarity=0.5  # Only include reasonably relevant results
        )
        
        if not results:
            return "No relevant context found."
        
        # Build context string
        context_parts = []
        current_tokens = 0
        
        for result in results:
            # Estimate tokens (rough: 1 token ≈ 0.75 words)
            chunk_tokens = len(result.chunk.split()) * 0.75
            
            if current_tokens + chunk_tokens > max_tokens:
                break
            
            # Format chunk with metadata
            chunk_header = (
                f"[{result.metadata.get('data_type', 'unknown')} | "
                f"Relevance: {result.similarity:.2f}]"
            )
            
            context_parts.append(f"{chunk_header}\n{result.chunk}\n")
            current_tokens += chunk_tokens
        
        context = "\n---\n\n".join(context_parts)
        
        logger.info(
            f"Retrieved context: {len(context_parts)} chunks, "
            f"~{int(current_tokens)} tokens"
        )
        
        return context
    
    def _deduplicate_results(
        self,
        results: List[SearchResult],
        similarity_threshold: float = 0.95
    ) -> List[SearchResult]:
        """
        Remove near-duplicate results
        
        Compares chunks using Jaccard similarity on words.
        Keeps the result with higher similarity score.
        """
        if len(results) <= 1:
            return results
        
        deduplicated = []
        seen_chunks = []
        
        for result in results:
            # Check if similar to any seen chunk
            is_duplicate = False
            result_words = set(result.chunk.lower().split())
            
            for seen_chunk in seen_chunks:
                seen_words = set(seen_chunk.lower().split())
                
                # Calculate Jaccard similarity
                intersection = len(result_words & seen_words)
                union = len(result_words | seen_words)
                jaccard = intersection / union if union > 0 else 0
                
                if jaccard >= similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(result)
                seen_chunks.append(result.chunk)
        
        logger.debug(
            f"Deduplication: {len(results)} -> {len(deduplicated)} results"
        )
        
        return deduplicated
    
    def _rerank_results(
        self,
        results: List[SearchResult],
        query: str
    ) -> List[SearchResult]:
        """
        Apply heuristic reranking based on metadata and query
        
        Boosts results with:
        - Recent data (higher season/week)
        - Matching data types mentioned in query
        - Higher confidence scores
        """
        query_lower = query.lower()
        
        # Keywords to boost specific data types
        data_type_keywords = {
            "matchup": "matchup_analytics",
            "vs": "matchup_analytics",
            "against": "matchup_analytics",
            "injury": "injury_report",
            "hurt": "injury_report",
            "status": "injury_report",
            "recent": "game_log",
            "last game": "game_log",
            "performance": "game_log",
            "profile": "player_profile",
            "stats": "player_profile"
        }
        
        for result in results:
            boost = 0.0
            
            # Boost recent data (assume 2024 is current)
            season = result.metadata.get("season")
            if season:
                if season >= 2024:
                    boost += 0.05
                elif season >= 2023:
                    boost += 0.02
            
            # Boost matching data types
            data_type = result.metadata.get("data_type", "")
            for keyword, dt in data_type_keywords.items():
                if keyword in query_lower and dt in data_type:
                    boost += 0.1
                    break
            
            # Boost high confidence
            confidence = result.metadata.get("confidence_score", 0.0)
            if confidence >= 0.9:
                boost += 0.05
            
            # Apply boost to similarity (capped at 1.0)
            result.similarity = min(result.similarity + boost, 1.0)
            result.distance = 1 - result.similarity
        
        # Re-sort by adjusted similarity
        results.sort(key=lambda r: r.similarity, reverse=True)
        
        # Update ranks
        for i, result in enumerate(results):
            result.rank = i + 1
        
        return results
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get search index statistics"""
        # Count total embeddings
        count_stmt = select(Embedding)
        result = await self.session.execute(
            select(func.count()).select_from(Embedding)
        )
        total_embeddings = result.scalar()
        
        # Get data type distribution
        data_type_col = Embedding.meta["data_type"].astext.label("data_type")
        type_stmt = select(
            data_type_col,
            func.count().label("count")
        ).group_by(data_type_col)
        
        result = await self.session.execute(type_stmt)
        type_distribution = {row.data_type: row.count for row in result.all()}
        
        return {
            "total_embeddings": total_embeddings,
            "data_type_distribution": type_distribution,
            "index_type": "HNSW",
            "vector_dimensions": 1536,
            "distance_metric": "cosine"
        }
