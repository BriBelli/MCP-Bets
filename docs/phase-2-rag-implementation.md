# Phase 2: RAG Knowledge Base Implementation

**Status**: Ready to begin (Phase 1 complete ✅)  
**Timeline**: Week 1-4  
**Goal**: Build production-grade RAG system for semantic search across SportsDataIO data

---

## Architecture Overview

```
SportsDataIO APIs → Data Ingestion → Document Chunking → 
→ Embeddings Generation → Vector Store (pgvector) → 
→ Semantic Search → Context Retrieval → Multi-LLM Judges
```

---

## Phase 1 Foundation (Completed ✅)

- PostgreSQL 14 with 11 tables (teams, players, games, injuries, props, stats)
- SportsDataIO client with rate limiting (2 req/sec, 10K/month quota)
- Cache layer (PostgreSQL-based, Redis optional)
- Quick test passing (database ✅, API ✅, cache ✅)
- 100+ Python dependencies installed

---

## Phase 2 Objectives

### Week 1: Core RAG Infrastructure

**1. pgvector Installation** (Day 1-2)
- **Issue**: Current pgvector (0.8.1) built for PostgreSQL 17/18, we're on 14
- **Solution Options**:
  - Option A: Compile pgvector from source for PostgreSQL 14
  - Option B: Upgrade to PostgreSQL 17 (breaking change, requires testing)
  - Option C: Use Pinecone/Weaviate (external vector DB, +$50/month)
- **Recommendation**: Option A (compile from source) - keeps costs low, PostgreSQL 14 stable

**2. Embeddings Table Schema** (Day 2-3)
```sql
-- Already defined in backend/mcp_bets/models/embedding.py
CREATE TABLE embeddings (
  id UUID PRIMARY KEY,
  embedding VECTOR(3072),  -- text-embedding-3-large dimensions
  document_chunk TEXT NOT NULL,
  meta JSONB NOT NULL,  -- Renamed from 'metadata' to avoid SQLAlchemy conflict
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- HNSW index for fast vector similarity
CREATE INDEX embeddings_hnsw_idx 
  ON embeddings 
  USING hnsw (embedding vector_cosine_ops);

-- GIN index for metadata filtering
CREATE INDEX embeddings_metadata_idx 
  ON embeddings 
  USING gin (meta);
```

**Metadata Structure** (JSONB):
```json
{
  "data_type": "player_profile" | "injury_report" | "game_log" | "matchup_analytics" | "weather" | "vegas_lines",
  "player_id": "uuid",
  "team_id": "ATL",
  "opponent_id": "BUF",
  "game_id": "uuid",
  "season": 2024,
  "week": 8,
  "confidence_score": 0.95,
  "source": "sportsdata.io",
  "last_verified": "2024-10-23T10:00:00Z"
}
```

**3. Document Chunking Service** (Day 3-5)
```python
# backend/mcp_bets/services/rag/document_chunker.py

class DocumentChunker:
    """
    Transform SportsDataIO data into semantic chunks
    
    Chunking Strategy:
    - Size: 500-800 tokens per chunk
    - Overlap: 50-100 tokens (10-20%)
    - Metadata enrichment for filtering
    """
    
    CHUNK_SIZE = 600  # tokens
    CHUNK_OVERLAP = 75  # tokens
    
    async def chunk_player_profile(self, player: Player) -> List[DocumentChunk]:
        """
        Create player profile chunks:
        - Season statistics (passing/rushing/receiving)
        - Last 5 games performance
        - Usage metrics (snap count, target share)
        - Injury history
        """
        pass
    
    async def chunk_matchup_analytics(
        self, 
        player: Player, 
        opponent: Team
    ) -> List[DocumentChunk]:
        """
        Create matchup analysis chunks:
        - Opponent defense rankings vs position
        - Historical performance vs opponent
        - Game script tendencies
        """
        pass
    
    async def chunk_game_log(self, stats: PlayerGameStats) -> List[DocumentChunk]:
        """
        Create game log chunks:
        - Single game performance breakdown
        - Key metrics (yards, TDs, targets)
        - Game context (score, game script)
        """
        pass
```

**4. Embeddings Service** (Day 5-7)
```python
# backend/mcp_bets/services/rag/embeddings_service.py

from openai import AsyncOpenAI

class EmbeddingsService:
    """
    Generate embeddings using OpenAI text-embedding-3-large
    
    Model: text-embedding-3-large
    Dimensions: 3072
    Cost: $0.00013 per 1K tokens (~$6.50 per 50M tokens)
    """
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "text-embedding-3-large"
        self.dimensions = 3072
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for single text chunk"""
        response = await self.client.embeddings.create(
            input=text,
            model=self.model,
            dimensions=self.dimensions
        )
        return response.data[0].embedding
    
    async def generate_batch(
        self, 
        texts: List[str]
    ) -> List[List[float]]:
        """
        Generate embeddings in batch (up to 2048 texts)
        More efficient than one-by-one
        """
        response = await self.client.embeddings.create(
            input=texts,
            model=self.model,
            dimensions=self.dimensions
        )
        return [item.embedding for item in response.data]
```

### Week 2: Semantic Search Implementation

**5. Vector Similarity Search** (Day 8-10)
```python
# backend/mcp_bets/services/rag/semantic_search.py

class SemanticSearchService:
    """
    Query Knowledge Base using vector similarity
    """
    
    async def search(
        self,
        query: str,
        filters: Dict[str, Any],
        limit: int = 10
    ) -> List[RetrievedChunk]:
        """
        1. Convert query to embedding
        2. Vector similarity search with metadata filters
        3. Rank by relevance
        4. Return top K chunks
        
        Example:
          query = "Bijan Robinson rushing receiving performance 2024"
          filters = {
            "player_id": "bijan_uuid",
            "season": 2024,
            "data_type": ["player_profile", "game_log"]
          }
        """
        
        # Step 1: Generate query embedding
        query_embedding = await self.embeddings_service.generate_embedding(query)
        
        # Step 2: PostgreSQL pgvector similarity search
        sql = """
        SELECT 
          id,
          document_chunk,
          meta,
          1 - (embedding <=> :query_vector) AS similarity
        FROM embeddings
        WHERE 
          meta->>'player_id' = :player_id AND
          meta->>'season' = :season AND
          meta->>'data_type' = ANY(:data_types)
        ORDER BY embedding <=> :query_vector
        LIMIT :limit
        """
        
        results = await self.db.execute(
            sql,
            {
                "query_vector": query_embedding,
                "player_id": filters["player_id"],
                "season": str(filters["season"]),
                "data_types": filters["data_type"],
                "limit": limit
            }
        )
        
        return [RetrievedChunk(**row) for row in results]
```

**6. Context Augmentation** (Day 10-12)
```python
# backend/mcp_bets/services/rag/context_builder.py

class ContextBuilder:
    """
    Build augmented prompts for LLM Judges
    """
    
    MAX_CONTEXT_TOKENS = 2500  # Target context size
    
    async def build_prop_analysis_context(
        self,
        prop: PlayerProp
    ) -> str:
        """
        Build context for prop bet analysis
        
        Returns formatted context string ready for LLM prompt
        """
        
        # Step 1: Generate search query
        query = f"{prop.player.name} {prop.prop_type} performance {prop.season}"
        
        # Step 2: Retrieve relevant chunks
        chunks = await self.semantic_search.search(
            query=query,
            filters={
                "player_id": prop.player_id,
                "season": prop.season,
                "data_type": ["player_profile", "game_log", "matchup_analytics"]
            },
            limit=15
        )
        
        # Step 3: Rank and deduplicate
        ranked_chunks = self._rank_by_relevance(chunks)
        unique_chunks = self._deduplicate(ranked_chunks)
        
        # Step 4: Fit to token budget
        context_chunks = self._fit_to_budget(unique_chunks, self.MAX_CONTEXT_TOKENS)
        
        # Step 5: Format for prompt
        return self._format_context(context_chunks)
    
    def _format_context(self, chunks: List[RetrievedChunk]) -> str:
        """
        Format chunks into structured context string
        
        Example output:
        '''
        PLAYER PROFILE:
        Bijan Robinson - 2024 season: 4/4 games over 100.5 combined yards...
        
        MATCHUP ANALYSIS:
        BUF defense vs RBs: 28th ranked (allows 135 yards/game)...
        
        RECENT PERFORMANCE:
        Last 5 games: 118.3 avg combined yards, 85% snap share...
        '''
        """
        sections = {
            "player_profile": "PLAYER PROFILE",
            "matchup_analytics": "MATCHUP ANALYSIS",
            "game_log": "RECENT PERFORMANCE",
            "injury_report": "INJURY STATUS",
            "weather": "WEATHER CONDITIONS"
        }
        
        output = []
        for data_type, header in sections.items():
            type_chunks = [c for c in chunks if c.meta["data_type"] == data_type]
            if type_chunks:
                output.append(f"\n{header}:")
                output.extend([c.document_chunk for c in type_chunks])
        
        return "\n".join(output)
```

### Week 3: Knowledge Base Hydration

**7. Initial Data Import** (Day 13-16)
```python
# backend/scripts/hydrate_knowledge_base.py

async def hydrate_2024_season():
    """
    Initial batch import: Generate embeddings for all 2024 data
    
    Target volumes:
    - 50K+ player-game context embeddings
    - 10K+ injury report embeddings
    - 5K+ matchup analytics embeddings
    - 100K+ game log embeddings
    
    Estimated cost: ~$8-10 for embeddings generation
    Estimated time: 2-4 hours (rate-limited by OpenAI API)
    """
    
    chunker = DocumentChunker()
    embeddings_service = EmbeddingsService(settings.OPENAI_API_KEY)
    
    # Step 1: Chunk all players
    print("Chunking player profiles...")
    players = await db.execute(select(Player))
    for player in players:
        chunks = await chunker.chunk_player_profile(player)
        embeddings = await embeddings_service.generate_batch(
            [c.text for c in chunks]
        )
        await store_embeddings(chunks, embeddings)
    
    # Step 2: Chunk all game logs
    print("Chunking game logs...")
    stats = await db.execute(select(PlayerGameStats).where(season=2024))
    for stat in stats:
        chunks = await chunker.chunk_game_log(stat)
        embeddings = await embeddings_service.generate_batch(
            [c.text for c in chunks]
        )
        await store_embeddings(chunks, embeddings)
    
    # Step 3: Chunk matchup data
    # ... (similar pattern)
```

**8. Auto-Sync Strategy** (Day 16-18)
```python
# backend/mcp_bets/services/rag/sync_scheduler.py

class KnowledgeBaseSyncScheduler:
    """
    Auto-refresh embeddings based on data volatility
    
    Refresh Frequencies:
    - Props/Odds: 5 min (90 sec final hour before game)
    - Injuries: 15 min (5 min on gameday)
    - Player Stats: Daily (6am ET)
    - Game Logs: Post-game + daily backfill
    - Schedules: Weekly (Monday 9am ET)
    """
    
    async def sync_props(self):
        """Refresh prop embeddings (high volatility)"""
        pass
    
    async def sync_injuries(self):
        """Refresh injury embeddings (daily updates)"""
        pass
    
    async def sync_player_stats(self):
        """Refresh player profile embeddings (daily)"""
        pass
```

### Week 4: Testing & Optimization

**9. End-to-End RAG Test** (Day 19-21)
```python
# backend/tests/test_rag_pipeline.py

async def test_rag_retrieval_quality():
    """
    Test Case: Bijan Robinson Over 100.5 Combined Yards
    
    Expected Retrieved Context:
    1. Season stats (4/4 games >100.5) ✅
    2. Last 5 games breakdown ✅
    3. BUF defense vs RBs (28th ranked) ✅
    4. Game-script analysis (dual-threat usage) ✅
    5. Snap count/target share data ✅
    6. Injury status (healthy) ✅
    7. Weather forecast ✅
    8. Vegas line movement ✅
    
    Performance Targets:
    - Retrieval latency: <500ms
    - Context relevance score: >0.85
    - Token count: 2000-2500
    """
    
    prop = await create_test_prop(
        player="Bijan Robinson",
        prop_type="combined_yards",
        line=100.5
    )
    
    context = await context_builder.build_prop_analysis_context(prop)
    
    assert context.relevance_score > 0.85
    assert 2000 <= context.token_count <= 2500
    assert "BUF defense" in context.text
    assert "4/4 games" in context.text
```

**10. Performance Optimization** (Day 21-28)
- HNSW index tuning (m=16, ef_construction=64)
- Query plan analysis (EXPLAIN ANALYZE)
- Connection pooling optimization
- Embedding cache layer (Redis)
- Monitoring setup (query latency, cache hit rates)

---

## Cost Analysis

| Component | Unit Cost | MCP Bets Usage | Monthly Cost |
|-----------|-----------|----------------|--------------|
| **OpenAI Embeddings** | $0.00013/1K tokens | 50M tokens/month | $6.50 |
| **PostgreSQL RDS** (t3.medium) | $0.104/hour | 730 hours | $75.92 |
| **S3 Storage** (raw JSON) | $0.023/GB | 100 GB | $2.30 |
| **OpenAI API Calls** (batch) | Included above | - | - |
| **Total Phase 2 Infrastructure** | | | **~$85/month** |

**Compared to Alternatives**:
- Pinecone: ~$70/month (10M vectors) + $75 PostgreSQL = $145/month
- Weaviate: ~$50/month (5M vectors) + $75 PostgreSQL = $125/month
- **pgvector**: $75 PostgreSQL + $6.50 embeddings = **$81.50/month** ✅ **Best value**

---

## Success Criteria

Phase 2 complete when:
- ✅ pgvector installed and HNSW index working
- ✅ Embeddings table with 50K+ vectors
- ✅ Semantic search retrieves relevant context (<500ms)
- ✅ Context quality validated (manual review + automated tests)
- ✅ Auto-sync working (daily/hourly refreshes)
- ✅ API endpoints ready for Phase 3 (MCP Agents)
- ✅ Documentation complete

---

## Next Phase Preview

**Phase 3: Multi-LLM Judges** (Week 5-8)
- Each Judge receives augmented prompts from RAG
- Independent analysis using Five Pillars framework
- Cross-reference engine weighs Judge consensus
- Output: Ultra Lock / Super Lock / Standard Lock / Lotto / Mega Lotto

**Phase 4: MCP Agent Orchestration** (Week 9-12)
- Weather Agent queries weather embeddings
- Injury Agent queries injury embeddings
- Player Profile Agent queries player embeddings
- Each Agent formats context for Judges

---

## Let's Begin! 🚀

**First Task**: Install/fix pgvector for PostgreSQL 14

Would you like me to start with pgvector installation, or would you prefer to upgrade PostgreSQL to version 17 first?
