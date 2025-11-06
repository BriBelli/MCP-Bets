"""
RAG Pipeline End-to-End Test

Tests the complete RAG pipeline with sample data:
1. Fetch sample player data from SportsDataIO
2. Chunk the data using DocumentChunker
3. Generate embeddings using EmbeddingsService
4. Store embeddings in PostgreSQL
5. Test semantic search queries
6. Measure performance and quality

Cost: ~$0.001 (negligible)
Time: ~5 minutes
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from mcp_bets.config.settings import Settings
from mcp_bets.models.base import Base
from mcp_bets.models.player import Player
from mcp_bets.models.team import Team
from mcp_bets.models.game import Game
from mcp_bets.models.season import Season
from mcp_bets.models.player_game_stats import PlayerGameStats
from mcp_bets.models.embedding import Embedding
from mcp_bets.services.rag import DocumentChunker, EmbeddingsService, SemanticSearch


class RAGPipelineTest:
    """Test harness for RAG pipeline"""
    
    def __init__(self):
        self.settings = Settings()
        self.engine = create_async_engine(self.settings.DATABASE_URL)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Initialize services
        self.chunker = DocumentChunker()
        self.embeddings_service = EmbeddingsService(self.settings)
        
        # Test results
        self.results = {
            "chunks_created": 0,
            "embeddings_generated": 0,
            "embeddings_stored": 0,
            "search_tests": [],
            "errors": []
        }
    
    async def run_all_tests(self):
        """Run complete test suite"""
        print("=" * 80)
        print("🧪 RAG Pipeline End-to-End Test")
        print("=" * 80)
        print()
        
        try:
            async with self.async_session() as session:
                # Initialize search service
                self.search_service = SemanticSearch(session, self.embeddings_service)
                
                # Test 1: Verify database connection
                print("📊 Test 1: Database Connection")
                await self._test_database_connection(session)
                
                # Test 2: Fetch sample data
                print("\n📊 Test 2: Fetch Sample Data")
                player, games, stats = await self._fetch_sample_data(session)
                
                if not player:
                    print("❌ No sample data available. Please run data import first.")
                    return
                
                # Test 3: Chunk player data
                print("\n📊 Test 3: Document Chunking")
                chunks = await self._test_chunking(player, games, stats)
                
                # Test 4: Generate embeddings
                print("\n📊 Test 4: Generate Embeddings")
                embeddings = await self._test_embeddings(chunks)
                
                # Test 5: Store in database
                print("\n📊 Test 5: Store Embeddings")
                await self._test_storage(session, chunks, embeddings)
                
                # Test 6: Semantic search
                print("\n📊 Test 6: Semantic Search")
                await self._test_search(session, player)
                
                # Test 7: Performance metrics
                print("\n📊 Test 7: Performance Metrics")
                await self._test_performance(session)
                
                await session.commit()
            
            # Print summary
            self._print_summary()
            
        except Exception as e:
            self.results["errors"].append(str(e))
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await self.embeddings_service.close()
            await self.engine.dispose()
    
    async def _test_database_connection(self, session: AsyncSession):
        """Test database connectivity"""
        try:
            result = await session.execute(select(Embedding).limit(1))
            print("✅ Database connection OK")
            print("✅ Embeddings table accessible")
        except Exception as e:
            print(f"❌ Database error: {e}")
            self.results["errors"].append(f"Database: {e}")
            raise
    
    async def _fetch_sample_data(self, session: AsyncSession):
        """Fetch sample player data"""
        try:
            from sqlalchemy.orm import selectinload
            
            # Find a player with recent stats (eager load team relationship)
            stmt = (
                select(Player)
                .options(selectinload(Player.team))
                .join(PlayerGameStats)
                .where(Player.position.in_(["RB", "WR", "QB"]))
                .limit(1)
            )
            result = await session.execute(stmt)
            player = result.scalar_one_or_none()
            
            if not player:
                print("⚠️  No players with stats found")
                return None, [], []
            
            print(f"✅ Found player: {player.first_name} {player.last_name} ({player.position})")
            
            # Fetch recent games (eager load all relationships)
            stmt = (
                select(Game)
                .options(
                    selectinload(Game.home_team),
                    selectinload(Game.away_team),
                    selectinload(Game.season)
                )
                .join(PlayerGameStats)
                .where(PlayerGameStats.player_id == player.id)
                .order_by(Game.game_date.desc())
                .limit(3)
            )
            result = await session.execute(stmt)
            games = result.scalars().all()
            
            print(f"✅ Found {len(games)} recent games")
            
            # Fetch stats for those games
            game_ids = [game.id for game in games]
            stmt = (
                select(PlayerGameStats)
                .where(
                    PlayerGameStats.player_id == player.id,
                    PlayerGameStats.game_id.in_(game_ids)
                )
            )
            result = await session.execute(stmt)
            stats = result.scalars().all()
            
            print(f"✅ Found {len(stats)} stat records")
            
            return player, games, stats
            
        except Exception as e:
            print(f"❌ Data fetch error: {e}")
            self.results["errors"].append(f"Data fetch: {e}")
            raise
    
    async def _test_chunking(self, player, games, stats):
        """Test document chunking"""
        try:
            chunks = []
            
            # Test player profile chunking
            profile_chunks = self.chunker.chunk_player_profile(
                player=player,
                season=2024,
                recent_stats=stats[:5]
            )
            chunks.extend(profile_chunks)
            print(f"✅ Created {len(profile_chunks)} player profile chunks")
            
            # Test game log chunking
            for game, stat in zip(games[:2], stats[:2]):
                game_chunks = self.chunker.chunk_game_log(
                    player=player,
                    game=game,
                    stats=stat
                )
                chunks.extend(game_chunks)
            print(f"✅ Created {len(chunks) - len(profile_chunks)} game log chunks")
            
            # Validate chunk sizes
            token_counts = [chunk.token_count for chunk in chunks]
            avg_tokens = sum(token_counts) / len(token_counts)
            min_tokens = min(token_counts)
            max_tokens = max(token_counts)
            
            print(f"   Token stats: avg={avg_tokens:.0f}, min={min_tokens}, max={max_tokens}")
            
            if min_tokens < 100:
                print(f"   ⚠️  Warning: Some chunks are very small ({min_tokens} tokens)")
            
            if max_tokens > 1000:
                print(f"   ⚠️  Warning: Some chunks are very large ({max_tokens} tokens)")
            
            self.results["chunks_created"] = len(chunks)
            return chunks
            
        except Exception as e:
            print(f"❌ Chunking error: {e}")
            self.results["errors"].append(f"Chunking: {e}")
            raise
    
    async def _test_embeddings(self, chunks):
        """Test embedding generation"""
        try:
            print(f"   Generating embeddings for {len(chunks)} chunks...")
            print(f"   Estimated cost: ${len(chunks) * 650 * 0.02 / 1_000_000:.6f}")
            
            # Generate embeddings in batch
            embeddings = await self.embeddings_service.generate_batch(
                chunks,
                show_progress=True
            )
            
            print(f"✅ Generated {len(embeddings)} embeddings")
            
            # Validate embedding dimensions
            if embeddings:
                first_embedding = embeddings[0][1]
                print(f"   Embedding dimensions: {len(first_embedding)}")
                
                if len(first_embedding) != 1536:
                    print(f"   ⚠️  Warning: Expected 1536 dimensions, got {len(first_embedding)}")
            
            self.results["embeddings_generated"] = len(embeddings)
            
            # Get usage stats
            stats = await self.embeddings_service.get_usage_stats()
            print(f"   Rate limit usage: {stats['requests_last_minute']}/{stats['requests_limit']} requests")
            print(f"   Token usage: {stats['tokens_last_minute']}/{stats['tokens_limit']} tokens")
            
            return embeddings
            
        except Exception as e:
            print(f"❌ Embeddings error: {e}")
            self.results["errors"].append(f"Embeddings: {e}")
            raise
    
    async def _test_storage(self, session: AsyncSession, chunks, embeddings):
        """Test storing embeddings in database"""
        try:
            stored_count = 0
            
            for chunk, embedding_vector in embeddings:
                # Create embedding record
                embedding_record = Embedding(
                    embedding=embedding_vector,
                    document_chunk=chunk.content,
                    meta=chunk.metadata
                )
                session.add(embedding_record)
                stored_count += 1
            
            await session.flush()
            print(f"✅ Stored {stored_count} embeddings in database")
            
            self.results["embeddings_stored"] = stored_count
            
        except Exception as e:
            print(f"❌ Storage error: {e}")
            self.results["errors"].append(f"Storage: {e}")
            raise
    
    async def _test_search(self, session: AsyncSession, player):
        """Test semantic search queries"""
        try:
            player_name = f"{player.first_name} {player.last_name}"
            
            # Test queries
            test_queries = [
                {
                    "query": f"{player_name} recent performance",
                    "expected_type": "game_log",
                    "min_similarity": 0.5
                },
                {
                    "query": f"{player_name} player profile stats",
                    "expected_type": "player_profile",
                    "min_similarity": 0.5
                },
                {
                    "query": f"How many yards did {player_name} rush for?",
                    "expected_type": None,  # Any type OK
                    "min_similarity": 0.3
                }
            ]
            
            for i, test in enumerate(test_queries, 1):
                print(f"\n   Query {i}: '{test['query']}'")
                
                try:
                    results = await self.search_service.search(
                        query=test["query"],
                        top_k=3,
                        filters={"player_name": player_name}
                    )
                    
                    if not results:
                        print(f"   ⚠️  No results found")
                        test_result = {
                            "query": test["query"],
                            "results": 0,
                            "top_similarity": 0.0,
                            "passed": False
                        }
                    else:
                        top_similarity = results[0].similarity
                        top_type = results[0].metadata.get("data_type")
                        
                        print(f"   ✅ Found {len(results)} results")
                        print(f"   Top result: similarity={top_similarity:.3f}, type={top_type}")
                        
                        # Validate results
                        passed = top_similarity >= test["min_similarity"]
                        if test["expected_type"] and top_type != test["expected_type"]:
                            print(f"   ⚠️  Expected type '{test['expected_type']}', got '{top_type}'")
                            passed = False
                        
                        test_result = {
                            "query": test["query"],
                            "results": len(results),
                            "top_similarity": top_similarity,
                            "top_type": top_type,
                            "passed": passed
                        }
                        
                        if passed:
                            print(f"   ✅ Search test passed")
                        else:
                            print(f"   ❌ Search test failed (similarity too low)")
                    
                    self.results["search_tests"].append(test_result)
                    
                except Exception as e:
                    import traceback
                    print(f"   ❌ Search error: {e}")
                    print(f"   Traceback: {traceback.format_exc()}")
                    self.results["search_tests"].append({
                        "query": test["query"],
                        "error": str(e),
                        "passed": False
                    })
            
        except Exception as e:
            print(f"❌ Search test error: {e}")
            self.results["errors"].append(f"Search: {e}")
            raise
    
    async def _test_performance(self, session: AsyncSession):
        """Test performance metrics"""
        try:
            import time
            
            # Test search latency
            test_query = "player performance statistics"
            
            start_time = time.time()
            results = await self.search_service.search(
                query=test_query,
                top_k=10
            )
            latency_ms = (time.time() - start_time) * 1000
            
            print(f"✅ Search latency: {latency_ms:.1f}ms")
            
            if latency_ms > 500:
                print(f"   ⚠️  Warning: Latency exceeds 500ms target")
            else:
                print(f"   ✅ Latency within target (<500ms)")
            
            # Get index statistics
            stats = await self.search_service.get_statistics()
            print(f"✅ Total embeddings in index: {stats['total_embeddings']}")
            print(f"   Data types: {stats['data_type_distribution']}")
            
        except Exception as e:
            print(f"❌ Performance test error: {e}")
            self.results["errors"].append(f"Performance: {e}")
    
    def _print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        print(f"\n✅ Chunks created: {self.results['chunks_created']}")
        print(f"✅ Embeddings generated: {self.results['embeddings_generated']}")
        print(f"✅ Embeddings stored: {self.results['embeddings_stored']}")
        
        print(f"\n🔍 Search Tests:")
        passed_tests = sum(1 for t in self.results["search_tests"] if t.get("passed", False))
        total_tests = len(self.results["search_tests"])
        print(f"   {passed_tests}/{total_tests} tests passed")
        
        for test in self.results["search_tests"]:
            status = "✅" if test.get("passed", False) else "❌"
            query = test["query"][:50] + "..." if len(test["query"]) > 50 else test["query"]
            similarity = test.get("top_similarity", 0.0)
            print(f"   {status} {query} (similarity: {similarity:.3f})")
        
        if self.results["errors"]:
            print(f"\n❌ Errors encountered: {len(self.results['errors'])}")
            for error in self.results["errors"]:
                print(f"   - {error}")
        else:
            print(f"\n✅ No errors encountered")
        
        print("\n" + "=" * 80)
        
        if self.results["errors"] or passed_tests < total_tests:
            print("⚠️  RESULT: Tests completed with issues - review before full hydration")
        else:
            print("✅ RESULT: All tests passed - ready for full data hydration!")
        
        print("=" * 80)


async def main():
    """Run RAG pipeline test"""
    test = RAGPipelineTest()
    await test.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
