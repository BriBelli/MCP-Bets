"""
OpenAI Embeddings Service for RAG Knowledge Base

Generates vector embeddings using OpenAI's text-embedding-3-small model.
Implements rate limiting, batching, and retry logic for production use.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI, RateLimitError, APIError
import logging

from mcp_bets.config.settings import Settings
from mcp_bets.services.rag.document_chunker import DocumentChunk

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """
    Generate embeddings using OpenAI text-embedding-3-small
    
    Model: text-embedding-3-small
    Dimensions: 1536
    Cost: $0.02 per 1M tokens
    Rate Limit: 3000 RPM, 1M TPM (Tier 1)
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        
        # Model configuration
        self.model = "text-embedding-3-small"
        self.dimensions = 1536
        
        # Rate limiting (Tier 1: 3000 RPM, 1M TPM)
        self.max_requests_per_minute = 3000
        self.max_tokens_per_minute = 1_000_000
        self.max_batch_size = 2048  # OpenAI limit for embeddings
        
        # Retry configuration
        self.max_retries = 3
        self.initial_retry_delay = 1.0  # seconds
        self.max_retry_delay = 60.0  # seconds
        
        # Rate limiting state
        self._request_timestamps: List[float] = []
        self._token_usage: List[tuple[float, int]] = []  # (timestamp, tokens)
    
    async def generate_embedding(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[float]:
        """
        Generate embedding for single text
        
        Args:
            text: Input text to embed
            metadata: Optional metadata (for logging/debugging)
            
        Returns:
            1536-dimensional embedding vector
            
        Raises:
            APIError: If OpenAI API fails after retries
        """
        # Wait if rate limit would be exceeded
        await self._wait_for_rate_limit(estimated_tokens=len(text.split()))
        
        for attempt in range(self.max_retries):
            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=text,
                    dimensions=self.dimensions
                )
                
                # Track usage
                self._record_request()
                tokens_used = response.usage.total_tokens
                self._record_tokens(tokens_used)
                
                logger.info(
                    f"Generated embedding: {tokens_used} tokens, "
                    f"${tokens_used * 0.02 / 1_000_000:.6f} cost"
                )
                
                return response.data[0].embedding
            
            except RateLimitError as e:
                delay = self._calculate_retry_delay(attempt)
                logger.warning(
                    f"Rate limit hit (attempt {attempt + 1}/{self.max_retries}). "
                    f"Waiting {delay:.1f}s: {e}"
                )
                await asyncio.sleep(delay)
            
            except APIError as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"OpenAI API error after {self.max_retries} retries: {e}")
                    raise
                
                delay = self._calculate_retry_delay(attempt)
                logger.warning(
                    f"API error (attempt {attempt + 1}/{self.max_retries}). "
                    f"Retrying in {delay:.1f}s: {e}"
                )
                await asyncio.sleep(delay)
        
        raise APIError("Max retries exceeded")
    
    async def generate_batch(
        self,
        chunks: List[DocumentChunk],
        show_progress: bool = True
    ) -> List[tuple[DocumentChunk, List[float]]]:
        """
        Generate embeddings for batch of chunks with rate limiting
        
        Args:
            chunks: List of DocumentChunk objects
            show_progress: Print progress updates
            
        Returns:
            List of (chunk, embedding) tuples
            
        Note:
            Automatically splits large batches to respect OpenAI limits
        """
        results = []
        total_chunks = len(chunks)
        
        # Split into batches respecting OpenAI's limits
        for batch_start in range(0, total_chunks, self.max_batch_size):
            batch_end = min(batch_start + self.max_batch_size, total_chunks)
            batch = chunks[batch_start:batch_end]
            
            if show_progress:
                logger.info(
                    f"Processing batch {batch_start // self.max_batch_size + 1}: "
                    f"chunks {batch_start + 1}-{batch_end} of {total_chunks}"
                )
            
            # Extract texts from chunks
            texts = [chunk.content for chunk in batch]
            
            # Estimate tokens (rough approximation: 1 token ≈ 0.75 words)
            estimated_tokens = sum(len(text.split()) for text in texts)
            
            # Wait if rate limit would be exceeded
            await self._wait_for_rate_limit(estimated_tokens=estimated_tokens)
            
            # Generate embeddings for batch
            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=texts,
                    dimensions=self.dimensions
                )
                
                # Track usage
                self._record_request()
                tokens_used = response.usage.total_tokens
                self._record_tokens(tokens_used)
                
                if show_progress:
                    logger.info(
                        f"Batch complete: {tokens_used} tokens, "
                        f"${tokens_used * 0.02 / 1_000_000:.6f} cost"
                    )
                
                # Match embeddings to chunks
                for chunk, embedding_data in zip(batch, response.data):
                    results.append((chunk, embedding_data.embedding))
            
            except RateLimitError as e:
                logger.warning(f"Rate limit hit during batch. Retrying with delay: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on rate limit
                
                # Retry this batch
                batch_start -= self.max_batch_size  # Go back one batch
                continue
            
            except APIError as e:
                logger.error(f"API error during batch processing: {e}")
                # Continue with next batch instead of failing completely
                continue
        
        return results
    
    async def _wait_for_rate_limit(self, estimated_tokens: int):
        """Wait if necessary to respect rate limits"""
        now = time.time()
        
        # Clean old timestamps (older than 1 minute)
        self._request_timestamps = [
            ts for ts in self._request_timestamps
            if now - ts < 60
        ]
        self._token_usage = [
            (ts, tokens) for ts, tokens in self._token_usage
            if now - ts < 60
        ]
        
        # Check request rate limit
        if len(self._request_timestamps) >= self.max_requests_per_minute:
            oldest_request = self._request_timestamps[0]
            wait_time = 60 - (now - oldest_request)
            if wait_time > 0:
                logger.info(f"Rate limit: Waiting {wait_time:.1f}s for request quota")
                await asyncio.sleep(wait_time)
        
        # Check token rate limit
        total_tokens = sum(tokens for _, tokens in self._token_usage)
        if total_tokens + estimated_tokens > self.max_tokens_per_minute:
            oldest_token_use = self._token_usage[0][0]
            wait_time = 60 - (now - oldest_token_use)
            if wait_time > 0:
                logger.info(f"Rate limit: Waiting {wait_time:.1f}s for token quota")
                await asyncio.sleep(wait_time)
    
    def _record_request(self):
        """Record API request timestamp"""
        self._request_timestamps.append(time.time())
    
    def _record_tokens(self, tokens: int):
        """Record token usage"""
        self._token_usage.append((time.time(), tokens))
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay"""
        delay = self.initial_retry_delay * (2 ** attempt)
        # Add jitter (±25%)
        import random
        jitter = delay * 0.25 * (2 * random.random() - 1)
        return min(delay + jitter, self.max_retry_delay)
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        now = time.time()
        
        recent_requests = len([
            ts for ts in self._request_timestamps
            if now - ts < 60
        ])
        
        recent_tokens = sum(
            tokens for ts, tokens in self._token_usage
            if now - ts < 60
        )
        
        return {
            "requests_last_minute": recent_requests,
            "requests_limit": self.max_requests_per_minute,
            "requests_available": self.max_requests_per_minute - recent_requests,
            "tokens_last_minute": recent_tokens,
            "tokens_limit": self.max_tokens_per_minute,
            "tokens_available": self.max_tokens_per_minute - recent_tokens,
            "model": self.model,
            "dimensions": self.dimensions,
            "cost_per_1m_tokens": 0.02
        }
    
    async def close(self):
        """Close the OpenAI client"""
        await self.client.close()
