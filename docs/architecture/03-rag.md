# MCP Bets: RAG-Optimized Data Architecture

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  MCP BETS SYSTEM OVERVIEW                    │
└─────────────────────────────────────────────────────────────┘

User → Props Input → RAG Knowledge Base → Multi-LLM Judges → 
→ Cross-Reference Engine → Final Research Pack → User

┌─────────────────────────────────────────────────────────────┐
│               PHASE 1: DATA FOUNDATION (RAG)                 │
│                                                              │
│  SportsDataIO APIs → Ingestion → Knowledge Base Hydration   │
│  → Vector Store → Query/Retrieval → Context Augmentation    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│          PHASE 2: MCP AGENT ORCHESTRATION                    │
│                                                              │
│  MCP Agents query Knowledge Base → Retrieve context for     │
│  Weather, Injuries, Players, Matchups, Vegas Lines          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│             PHASE 3: MULTI-LLM JUDGE SYSTEM                  │
│                                                              │
│  Claude + GPT + Gemini receive augmented prompts →          │
│  Generate independent analyses → Cross-reference →          │
│  Weighted consensus output                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: RAG Data Architecture for SportsDataIO

This is the **foundational layer** that feeds everything else in MCP Bets. We'll implement a production-grade RAG system following AWS best practices.

---

## RAG Architecture: Knowledge Base Hydration Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│        SPORTSDATA.IO ENTERPRISE DATA SOURCES                 │
│                                                              │
│  • NFL Schedules & Games    • Player Props & Odds           │
│  • Injury Reports           • Game Logs & Stats             │
│  • Player Profiles          • Weather Data                  │
│  • Vegas Line Movement      • Team Analytics                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            INGESTION LAYER (Rate-Limited Gateway)            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API Client with Retry Logic & Budget Control        │  │
│  │  • Max 2 requests/second                             │  │
│  │  • Monthly budget cap: 10,000 requests               │  │
│  │  • Exponential backoff on failures                   │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│          RAW DATA STORAGE (PostgreSQL + S3)                  │
│                                                              │
│  PostgreSQL: Structured data (games, players, injuries)     │
│  S3 Buckets: Raw API responses (JSON) for audit trail       │
│                                                              │
│  Refresh Strategy:                                          │
│  • Props/Odds: Every 5 min (90 sec final hour)             │
│  • Injuries: Every 15 min (5 min on gameday)               │
│  • Player Stats: Daily + post-game backfill                │
│  • Schedules: Weekly                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│        DOCUMENT PROCESSING & CHUNKING PIPELINE               │
│                                                              │
│  Step 1: Extract & Transform                                │
│  ┌────────────────────────────────────────────────────┐    │
│  │ • Combine related data into documents              │    │
│  │ • Example: "Player Game Context" document =        │    │
│  │   Player profile + last 5 games + injury status +  │    │
│  │   matchup analytics + weather                      │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Step 2: Semantic Chunking Strategy                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Chunk Size: 500-800 tokens per chunk               │    │
│  │ Overlap: 50-100 tokens (10-20%)                    │    │
│  │                                                     │    │
│  │ Document Types & Chunking:                         │    │
│  │ • Player Context: By statistical category          │    │
│  │ • Injury Reports: By player + practice status      │    │
│  │ • Game Logs: By game + performance metrics         │    │
│  │ • Matchup Analytics: By offensive/defensive split  │    │
│  │ • Weather: By game location + time window          │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Step 3: Metadata Enrichment                                │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Each chunk includes:                               │    │
│  │ • data_type (player_profile, injury, matchup, etc) │    │
│  │ • player_id, team_id, game_id (foreign keys)       │    │
│  │ • season, week                                      │    │
│  │ • timestamp, source                                 │    │
│  │ • confidence_score (data freshness/reliability)    │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         EMBEDDINGS MODEL (Amazon Bedrock/OpenAI)             │
│                                                              │
│  Model: amazon.titan-embed-text-v2 (AWS) or                │
│         text-embedding-3-large (OpenAI)                     │
│                                                              │
│  Process:                                                   │
│  1. Convert each document chunk into vector embedding       │
│  2. Dimension: 1024 (Titan) or 3072 (OpenAI)               │
│  3. Batch processing for efficiency                         │
│                                                              │
│  Example Document Chunk:                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │ "Bijan Robinson rushing performance analysis:      │    │
│  │  Week 1-4 average: 112 combined yards/game.        │    │
│  │  Target share: 22%. Snap count: 85%.               │    │
│  │  Game-script proof: 65% rushing/35% receiving.     │    │
│  │  BUF matchup: 28th vs RB combined yards."          │    │
│  └────────────────────────────────────────────────────┘    │
│                            ↓                                 │
│  [0.234, -0.512, 0.891, ... 1024 dimensions]               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│    VECTOR STORE (PostgreSQL pgvector OR Pinecone)           │
│                                                              │
│  Storage Schema:                                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │ embeddings_table:                                  │    │
│  │ ├─ id (UUID, primary key)                          │    │
│  │ ├─ embedding (vector[1024])                        │    │
│  │ ├─ document_chunk (TEXT)                           │    │
│  │ ├─ metadata (JSONB)                                │    │
│  │ │   ├─ data_type                                   │    │
│  │ │   ├─ player_id                                   │    │
│  │ │   ├─ season, week                                │    │
│  │ │   ├─ created_at, updated_at                      │    │
│  │ │   └─ confidence_score                            │    │
│  │ └─ Indexes:                                        │    │
│  │     ├─ HNSW index on embedding (fast similarity)   │    │
│  │     └─ GIN index on metadata (fast filtering)      │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Why PostgreSQL pgvector?                                   │
│  ✅ Cost-effective (no separate vector DB license)          │
│  ✅ Already using PostgreSQL for structured data            │
│  ✅ ACID compliance for data consistency                    │
│  ✅ Excellent performance for <10M vectors                  │
│  ✅ Native metadata filtering with JSONB                    │
│                                                              │
│  Alternative: Pinecone (if scaling >10M vectors)            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            KNOWLEDGE BASE (Hydrated & Ready)                 │
│                                                              │
│  Contains semantically searchable data:                     │
│  • 50,000+ player-game context embeddings                   │
│  • 10,000+ injury report embeddings                         │
│  • 5,000+ matchup analytics embeddings                      │
│  • 2,000+ weather context embeddings                        │
│  • 100,000+ game log embeddings                             │
│                                                              │
│  Auto-Sync Strategy:                                        │
│  • Daily refresh: Player profiles, season stats            │
│  • Hourly refresh: Props, odds, line movement               │
│  • 15-min refresh: Injuries, weather                        │
│  • Post-game refresh: Final stats, results                  │
└─────────────────────────────────────────────────────────────┘
```

---

## RAG Retrieval Flow: Query → Context → Augmented Prompt

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INPUT (Example)                      │
│                                                              │
│  User uploads prop screenshot:                              │
│  "Bijan Robinson Over 100.5 Combined Rush+Rec Yards"       │
│  Game: ATL @ BUF, Sunday 1pm ET                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              QUERY PREPROCESSING & EMBEDDING                 │
│                                                              │
│  Step 1: Extract structured data from input                 │
│  ┌────────────────────────────────────────────────────┐    │
│  │ • Player: "Bijan Robinson"                         │    │
│  │ • Prop Type: "combined_yards"                      │    │
│  │ • Line: 100.5                                       │    │
│  │ • Game: ATL @ BUF                                   │    │
│  │ • Date: 2024-10-27                                  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Step 2: Generate search query                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ "Bijan Robinson rushing receiving performance      │    │
│  │  2024 season statistics matchup Buffalo Bills      │    │
│  │  game script tendencies snap count target share"   │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Step 3: Convert query to embedding                         │
│  • Use same embeddings model (Titan/OpenAI)                │
│  • Generate query vector: [0.123, -0.456, ...]             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│          VECTOR SIMILARITY SEARCH (Knowledge Base)           │
│                                                              │
│  Search Strategy: Semantic + Hybrid with Metadata Filters   │
│                                                              │
│  SQL Query (PostgreSQL pgvector):                           │
│  ┌────────────────────────────────────────────────────┐    │
│  │ SELECT                                             │    │
│  │   document_chunk,                                  │    │
│  │   metadata,                                        │    │
│  │   embedding <=> $query_vector AS distance         │    │
│  │ FROM embeddings_table                              │    │
│  │ WHERE                                              │    │
│  │   metadata->>'player_id' = 'bijan_robinson_id' AND│    │
│  │   metadata->>'season' = '2024' AND                 │    │
│  │   metadata->>'data_type' IN (                      │    │
│  │     'player_profile',                              │    │
│  │     'game_log',                                    │    │
│  │     'matchup_analytics',                           │    │
│  │     'injury_report'                                │    │
│  │   )                                                │    │
│  │ ORDER BY distance ASC                              │    │
│  │ LIMIT 10;                                          │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Retrieved Context (Top 10 chunks):                         │
│  1. Bijan Robinson season stats (4/4 games >100.5 combined) │
│  2. Last 5 games performance breakdown                      │
│  3. BUF defense vs RBs (28th ranked)                        │
│  4. Game-script analysis (dual-threat usage)                │
│  5. Snap count & target share data (85%+ snaps)             │
│  6. Injury status (healthy, no concerns)                    │
│  7. Weather forecast (clear, 68°F)                          │
│  8. Vegas line movement (stable at 100.5)                   │
│  9. ATL offensive tendencies (RB-heavy scheme)              │
│  10. Bijan post-BYE week performance history                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            CONTEXT RANKING & FILTERING                       │
│                                                              │
│  Relevance Scoring:                                         │
│  • Semantic similarity score (0-1)                          │
│  • Recency weight (newer data = higher priority)            │
│  • Data type priority (player_profile > general_stats)      │
│  • Confidence score from metadata                           │
│                                                              │
│  Deduplication:                                             │
│  • Remove redundant chunks (same info, different words)     │
│  • Merge overlapping chunks intelligently                   │
│                                                              │
│  Token Budget Management:                                   │
│  • Target: 2,000-3,000 tokens of context                    │
│  • Summarize if context exceeds budget                      │
│  • Prioritize Five Pillars data (historical, matchup, etc)  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              AUGMENTED PROMPT CONSTRUCTION                   │
│                                                              │
│  Template:                                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │ You are an expert NFL prop bet analyst.           │    │
│  │                                                     │    │
│  │ CONTEXT (Retrieved from Knowledge Base):          │    │
│  │ {retrieved_context_chunks}                         │    │
│  │                                                     │    │
│  │ USER QUERY:                                        │    │
│  │ Analyze this prop: Bijan Robinson Over 100.5      │    │
│  │ Combined Rush+Rec Yards (ATL @ BUF, Sun 1pm)      │    │
│  │                                                     │    │
│  │ TASK:                                              │    │
│  │ Using the provided context, evaluate this prop    │    │
│  │ against the Five Pillars framework:                │    │
│  │ 1. Historical Dominance                            │    │
│  │ 2. Game-Script Proof                               │    │
│  │ 3. Elite Matchup                                   │    │
│  │ 4. Volume Lock                                     │    │
│  │ 5. No Red Flags                                    │    │
│  │                                                     │    │
│  │ Provide confidence tier (Ultra Lock, Super Lock,  │    │
│  │ Standard Lock, Lotto, Mega Lotto) with reasoning. │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│               SENT TO MULTI-LLM JUDGES                       │
│                                                              │
│  All 3 Judges receive the same augmented prompt:            │
│  • Claude 4.5 (Judge #1)                                    │
│  • GPT-4o (Judge #2)                                        │
│  • Gemini 2 (Judge #3)                                      │
│                                                              │
│  Each Judge analyzes independently with full context        │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Refresh & Sync Strategy

### Knowledge Base Hydration Schedule

| Data Type | Refresh Frequency | Trigger | Priority |
|-----------|-------------------|---------|----------|
| **Props & Odds** | 5 min (90 sec final hour) | Cron + API webhook | HIGH |
| **Injuries** | 15 min (5 min gameday) | Cron + breaking news alerts | HIGH |
| **Player Profiles** | Daily (6am ET) | Cron | MEDIUM |
| **Game Logs** | Post-game + daily | Game completion trigger | MEDIUM |
| **Weather** | 15 min (5 min gameday) | Cron | MEDIUM |
| **Vegas Lines** | 3 min (1 min final hour) | Cron + line movement alerts | HIGH |
| **Season Stats** | Daily (3am ET) | Cron | LOW |
| **Schedules** | Weekly (Mon 9am ET) | Cron | LOW |

### Batch Processing Pipeline (AWS)

```
┌─────────────────────────────────────────────────────────────┐
│         NIGHTLY BATCH HYDRATION (AWS Lambda/Batch)           │
│                                                              │
│  Time: 3:00 AM ET (off-peak)                                │
│                                                              │
│  Step 1: Fetch new data from SportsDataIO                   │
│  • Season stats, player profiles, game logs                 │
│                                                              │
│  Step 2: Store raw JSON in S3                               │
│  • s3://mcp-bets/raw-data/2024-10-23/                       │
│                                                              │
│  Step 3: Transform & chunk documents                        │
│  • Lambda function processes JSON → chunks                  │
│                                                              │
│  Step 4: Generate embeddings (Bedrock batch)                │
│  • Invoke amazon.titan-embed-text-v2 in batch mode          │
│  • Cost: $0.0001 per 1K tokens (much cheaper than on-demand)│
│                                                              │
│  Step 5: Upsert vectors to PostgreSQL pgvector              │
│  • Bulk insert with ON CONFLICT UPDATE                      │
│  • Update existing embeddings if data changed               │
│                                                              │
│  Step 6: Cleanup expired embeddings                         │
│  • Delete embeddings older than 90 days                     │
│                                                              │
│  Monitoring:                                                │
│  • CloudWatch logs for errors                               │
│  • SNS alerts if batch fails                                │
│  • Cost tracking per batch run                              │
└─────────────────────────────────────────────────────────────┘
```

---

## PostgreSQL Schema: RAG Knowledge Base

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Embeddings table (core of RAG knowledge base)
CREATE TABLE embeddings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  embedding vector(1024), -- Titan embedding dimension
  document_chunk TEXT NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- HNSW index for fast vector similarity search
CREATE INDEX embeddings_hnsw_idx 
  ON embeddings 
  USING hnsw (embedding vector_cosine_ops);

-- GIN index for fast metadata filtering
CREATE INDEX embeddings_metadata_idx 
  ON embeddings 
  USING gin (metadata);

-- Metadata schema (JSONB structure)
-- {
--   "data_type": "player_profile" | "injury_report" | "game_log" | "matchup_analytics" | "weather" | "vegas_lines",
--   "player_id": "bijan_robinson_12345",
--   "team_id": "ATL",
--   "opponent_id": "BUF",
--   "game_id": "2024_week8_atl_buf",
--   "season": 2024,
--   "week": 8,
--   "confidence_score": 0.95,
--   "source": "sportsdata.io",
--   "last_verified": "2024-10-23T10:00:00Z"
-- }

-- Example similarity search query
SELECT 
  document_chunk,
  metadata,
  1 - (embedding <=> '[0.123, -0.456, ...]'::vector) AS similarity
FROM embeddings
WHERE 
  metadata->>'player_id' = 'bijan_robinson_12345' AND
  metadata->>'season' = '2024'
ORDER BY embedding <=> '[0.123, -0.456, ...]'::vector
LIMIT 10;
```

---

## Cost Optimization for RAG System

### AWS Bedrock Embeddings Pricing

| Component | Cost | MCP Bets Usage | Monthly Cost |
|-----------|------|----------------|--------------|
| **Titan Embeddings** | $0.0001/1K tokens | 50M tokens/month | $5 |
| **Batch Processing** | 50% discount | Nightly batches | $2.50 |
| **Storage (S3)** | $0.023/GB | 100GB raw JSON | $2.30 |
| **PostgreSQL RDS** | $50-150/month | t3.medium instance | $75 |
| **Total RAG Infrastructure** | | | **~$85/month** |

### Compared to Alternatives:

- **Pinecone**: ~$70/month for 10M vectors (similar cost, but separate service)
- **Weaviate Cloud**: ~$50/month for 5M vectors
- **PostgreSQL pgvector**: $75/month RDS + $7.50 embeddings = **$82.50/month** ✅ **Best value**

---

## Next Steps: Connecting RAG to MCP Agents (Phase 2)

Once the Knowledge Base is hydrated, **MCP Agents** become the interface:

```
Weather Agent → Queries embeddings (data_type='weather') → Returns context
Injury Agent → Queries embeddings (data_type='injury_report') → Returns context
Player Profile Agent → Queries embeddings (data_type='player_profile') → Returns context
Matchup Agent → Queries embeddings (data_type='matchup_analytics') → Returns context
```

Each Agent is a **function** that:
1. Takes a player/game/prop as input
2. Generates a semantic search query
3. Retrieves top K relevant chunks from Knowledge Base
4. Returns formatted context to Judges

---

## Summary: RAG Data Architecture Benefits

✅ **Cost-Effective**: ~$85/month for full RAG system (vs $500+ for alternatives)
✅ **Respects SportsDataIO Partnership**: Cache layer prevents API abuse
✅ **Semantic Search**: Find relevant context intelligently, not just keyword matching
✅ **Scalable**: Can handle 100K+ embeddings easily, expandable to millions
✅ **Fresh Data**: Auto-sync strategy keeps Knowledge Base current
✅ **Metadata Filtering**: Fast queries with player/game/date constraints
✅ **Audit Trail**: S3 stores raw API responses for debugging/compliance

---

## What You Should Build First (Week 1-2)

1. **SportsDataIO ingestion with rate limiting** (already in Phase 1 guide)
2. **PostgreSQL pgvector setup** (enable extension, create embeddings table)
3. **Document chunking pipeline** (transform API responses → chunks)
4. **Embeddings generation** (Bedrock Titan or OpenAI)
5. **Vector similarity search queries** (test retrieval quality)
6. **Batch hydration job** (nightly refresh via Lambda/cron)

Once this is working, **everything else cascades naturally** - MCP Agents just query the Knowledge Base, and Judges receive rich, contextual data.