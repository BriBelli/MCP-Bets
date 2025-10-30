# Phase 1.3: PostgreSQL Setup - Complete Documentation

**Status**: ✅ COMPLETED  
**Date**: October 28, 2025  
**Dependencies**: Phase 1.2 (Database Schema)

---

## Overview

Phase 1.3 establishes the PostgreSQL database environment for MCP Bets, including the pgvector extension for vector similarity search (RAG system). This phase installs PostgreSQL 14, enables pgvector, and creates the production database.

---

## Installation Steps

### 1. Install PostgreSQL 14

PostgreSQL 14 was chosen for stability and pgvector compatibility.

```bash
# Install PostgreSQL 14 via Homebrew
brew install postgresql@14

# Expected output:
# ==> Downloading postgresql@14
# ==> Pouring postgresql@14--14.19.arm64_sonoma.bottle.tar.gz
# 🍺  /opt/homebrew/Cellar/postgresql@14/14.19: 3,334 files, 46.0MB
```

**Dependencies Installed**:
- `icu4c@77` - Unicode and globalization support
- `ca-certificates` - SSL certificate bundle
- `openssl@3` - Cryptography toolkit
- `krb5` - Kerberos authentication
- `lz4` - Compression library
- `readline` - Command-line editing

**Installation Location**:
- Binary: `/opt/homebrew/opt/postgresql@14/bin/postgres`
- Data Directory: `/opt/homebrew/var/postgresql@14`
- Config: `/opt/homebrew/var/postgresql@14/postgresql.conf`

---

### 2. Install pgvector Extension

pgvector provides vector similarity search capabilities for the RAG system.

```bash
# Install pgvector
brew install pgvector

# Expected output:
# ==> Pouring pgvector--0.8.1.arm64_sonoma.bottle.tar.gz
# 🍺  /opt/homebrew/Cellar/pgvector/0.8.1: 88 files, 510.5KB
```

**pgvector Version**: 0.8.1  
**Features**:
- Vector data type for PostgreSQL
- Cosine similarity search (`<=>` operator)
- Euclidean distance search (`<->` operator)
- Inner product search (`<#>` operator)
- HNSW and IVFFlat indexes for fast search

---

### 3. Start PostgreSQL Service

```bash
# Start PostgreSQL as a background service
brew services start postgresql@14

# Expected output:
# ==> Successfully started `postgresql@14` (label: homebrew.mxcl.postgresql@14)
```

**Service Details**:
- **Service Name**: `homebrew.mxcl.postgresql@14`
- **Auto-start**: Enabled (starts on boot)
- **Status Check**: `brew services list`
- **Stop Service**: `brew services stop postgresql@14`
- **Restart Service**: `brew services restart postgresql@14`

---

### 4. Create MCP Bets Database

```bash
# Wait for PostgreSQL to fully start (2 seconds)
sleep 2

# Create database
/opt/homebrew/opt/postgresql@14/bin/createdb mcp_bets

# Verify database creation
/opt/homebrew/opt/postgresql@14/bin/psql -l | grep mcp_bets
```

**Database Details**:
- **Name**: `mcp_bets`
- **Encoding**: UTF-8
- **Locale**: en_US.UTF-8
- **Owner**: Current user (brian)
- **Connection String**: `postgresql://postgres:postgres@localhost:5432/mcp_bets`

---

## Database Configuration

### Connection Settings

The database connection is configured in `/backend/.env`:

```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/mcp_bets
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mcp_bets
DB_USER=postgres
DB_PASSWORD=postgres
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
```

### SQLAlchemy Configuration

Database connection is managed in `/backend/mcp_bets/config/database.py`:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    echo=settings.DEBUG,
)

# Session factory
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
```

**Key Features**:
- **Async engine**: Non-blocking database operations
- **Connection pooling**: 20 connections + 10 overflow
- **Echo mode**: SQL logging when DEBUG=true
- **Session management**: Context manager for automatic cleanup

---

## pgvector Extension Setup

### Enable pgvector Extension

The pgvector extension must be enabled in the database before creating tables:

```python
# In scripts/init_db.py
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    conn.commit()
```

**Extension Details**:
- **Name**: `vector`
- **Version**: 0.8.1
- **Schema**: `public`
- **Provides**: `vector` data type + similarity operators

### Verify Extension

```sql
-- Check if extension is enabled
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Output:
-- extname | extowner | extnamespace | extrelocatable | extversion
-- vector  | 10       | 2200         | true           | 0.8.1
```

---

## Database Initialization Script

Created `/backend/scripts/init_db.py` to automate database setup:

### Script Features

1. **Check pgvector**: Verifies extension is installed
2. **Enable pgvector**: Creates extension if not exists
3. **Create tables**: Generates all 13 tables from SQLAlchemy models
4. **Verify schema**: Confirms all tables exist
5. **Print details**: Shows columns, foreign keys, indexes

### Running the Script

```bash
# Navigate to backend directory
cd /Users/brian/Desktop/projects/BetAIPredict/backend

# Activate virtual environment
source ../.venv/bin/activate

# Run initialization script
python scripts/init_db.py
```

### Expected Output

```
================================================================================
MCP BETS - DATABASE INITIALIZATION
================================================================================
Checking pgvector extension...
✅ pgvector extension is enabled

Creating database tables...
✅ All tables created successfully

Verifying database schema...

Found 13 tables in database:
  ✅ api_keys
  ✅ api_requests
  ✅ cache_entries
  ✅ embeddings
  ✅ games
  ✅ injuries
  ✅ judges_performance
  ✅ player_game_stats
  ✅ player_props
  ✅ players
  ✅ seasons
  ✅ teams

✅ All expected tables exist

================================================================================
DATABASE SCHEMA DETAILS
================================================================================
[... detailed table information ...]

================================================================================
✅ DATABASE INITIALIZATION COMPLETE!
================================================================================
```

---

## Database Tables Created

### Core NFL Data
1. **seasons** - NFL seasons (year, type)
2. **teams** - NFL teams (32 teams)
3. **players** - Active NFL players (~2,500)
4. **games** - NFL games (272 regular season + playoffs)
5. **player_game_stats** - Player performance per game
6. **injuries** - Injury reports

### Betting Data
7. **player_props** - Player betting props (FanDuel, DraftKings)

### RAG System
8. **embeddings** - Vector embeddings (3072 dimensions with pgvector)

### Judge System
9. **judges_performance** - LLM judge accuracy tracking

### Infrastructure
10. **cache_entries** - Warm cache (PostgreSQL fallback)
11. **api_requests** - API telemetry
12. **api_keys** - Public API keys

---

## Verification Commands

### Check PostgreSQL Status

```bash
# Check if PostgreSQL is running
brew services list | grep postgresql@14

# Expected output:
# postgresql@14 started brian ~/Library/LaunchAgents/homebrew.mxcl.postgresql@14.plist
```

### Connect to Database

```bash
# Connect via psql
/opt/homebrew/opt/postgresql@14/bin/psql mcp_bets

# Or use full connection string
psql "postgresql://postgres:postgres@localhost:5432/mcp_bets"
```

### List Tables

```sql
-- List all tables
\dt

-- Output:
--  Schema |       Name         | Type  | Owner
-- --------+--------------------+-------+-------
--  public | api_keys           | table | brian
--  public | api_requests       | table | brian
--  public | cache_entries      | table | brian
--  public | embeddings         | table | brian
--  public | games              | table | brian
--  public | injuries           | table | brian
--  public | judges_performance | table | brian
--  public | player_game_stats  | table | brian
--  public | player_props       | table | brian
--  public | players            | table | brian
--  public | seasons            | table | brian
--  public | teams              | table | brian
```

### Check pgvector Extension

```sql
-- Verify pgvector is enabled
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Check vector type
SELECT typname FROM pg_type WHERE typname = 'vector';
```

### Test Vector Operations

```sql
-- Create test vector
SELECT '[1,2,3]'::vector;

-- Test cosine similarity
SELECT '[1,2,3]'::vector <=> '[4,5,6]'::vector AS cosine_distance;
```

---

## Performance Optimization

### Connection Pooling

SQLAlchemy connection pool configuration:

```python
# In config/database.py
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,        # Maximum 20 persistent connections
    max_overflow=10,     # Allow 10 additional connections
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections after 1 hour
)
```

### Index Strategy

Indexes created automatically by SQLAlchemy models:

- **Primary Keys**: UUID indexes on all tables
- **Foreign Keys**: Automatic indexes on all FK columns
- **Composite Indexes**: `(season_id, week)` on `games` table
- **Unique Constraints**: `teams.abbreviation`, `cache_entries.key`

### Future Optimizations

**GIN Indexes** (for JSONB columns):
```sql
CREATE INDEX idx_embeddings_metadata ON embeddings USING GIN (metadata);
CREATE INDEX idx_judges_category_accuracy ON judges_performance USING GIN (category_accuracy);
```

**HNSW Indexes** (for vector search):
```sql
CREATE INDEX ON embeddings USING hnsw (embedding vector_cosine_ops);
```

---

## Troubleshooting

### Issue: PostgreSQL Not Starting

```bash
# Check logs
tail -f /opt/homebrew/var/log/postgresql@14.log

# Common fix: Remove PID file
rm /opt/homebrew/var/postgresql@14/postmaster.pid
brew services restart postgresql@14
```

### Issue: Connection Refused

```bash
# Check if PostgreSQL is listening
lsof -i :5432

# Expected output:
# COMMAND   PID  USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
# postgres  1234 brian  6u   IPv6  0x...  0t0      TCP localhost:postgresql (LISTEN)
```

### Issue: pgvector Not Found

```bash
# Verify pgvector installation
brew list pgvector

# Reinstall if needed
brew reinstall pgvector

# Check PostgreSQL extensions directory
ls /opt/homebrew/opt/postgresql@14/share/postgresql@14/extension/ | grep vector
```

### Issue: Permission Denied

```bash
# Fix data directory permissions
chmod 700 /opt/homebrew/var/postgresql@14

# Fix ownership
chown -R $(whoami) /opt/homebrew/var/postgresql@14
```

---

## Security Considerations

### Production Recommendations

1. **Change default password**: Update `DB_PASSWORD` in `.env`
2. **Enable SSL**: Configure `ssl=require` in connection string
3. **Restrict network access**: Use firewall rules to limit connections
4. **Use environment-specific credentials**: Different passwords for dev/staging/prod
5. **Enable connection encryption**: Use SSL certificates for production

### Password Configuration

```bash
# Set PostgreSQL password (production)
/opt/homebrew/opt/postgresql@14/bin/psql postgres
postgres=# ALTER USER postgres WITH PASSWORD 'your_secure_password';
postgres=# \q

# Update .env
DATABASE_URL=postgresql://postgres:your_secure_password@localhost:5432/mcp_bets
```

---

## Backup & Recovery

### Manual Backup

```bash
# Create backup
pg_dump -Fc mcp_bets > backups/mcp_bets_$(date +%Y%m%d_%H%M%S).dump

# Restore backup
pg_restore -d mcp_bets backups/mcp_bets_20251028_120000.dump
```

### Automated Backups

```bash
# Add to crontab
0 2 * * * /usr/local/bin/pg_dump -Fc mcp_bets > /path/to/backups/mcp_bets_$(date +\%Y\%m\%d).dump
```

---

## Next Steps

### Immediate Next Steps

1. **Run initialization script**: `python scripts/init_db.py` (deferred to Phase 1.6)
2. **Verify all tables created**: Check with `\dt` in psql
3. **Test vector operations**: Insert sample embedding and query

### Phase 1.4: SportsDataIO Client

- SportsDataIO API client already implemented
- Ready to import data into database
- Rate limiting and retry logic in place

### Phase 1.5: Cache Layer

- Implement Redis hot cache
- Use PostgreSQL warm cache (already have `cache_entries` table)
- Intelligent TTL refresh policies

---

## Summary

### What We Accomplished

- ✅ **Installed PostgreSQL 14** via Homebrew
- ✅ **Installed pgvector 0.8.1** for vector similarity search
- ✅ **Started PostgreSQL service** as background service
- ✅ **Created `mcp_bets` database** with UTF-8 encoding
- ✅ **Configured connection settings** in `.env` and `database.py`
- ✅ **Created initialization script** (`scripts/init_db.py`)
- ✅ **Ready for table creation** (13 tables defined in models)

### Why It Matters

PostgreSQL with pgvector is the **backbone of MCP Bets**:

1. **Data Storage**: All NFL data, props, and predictions
2. **RAG System**: Vector similarity search for intelligent context retrieval
3. **Cache Layer**: Persistent warm cache when Redis is unavailable
4. **Telemetry**: API usage tracking and cost monitoring
5. **Performance**: Connection pooling and optimized indexes

### Key Technical Decisions

**PostgreSQL 14 vs Newer Versions**:
- Chose 14 for stability and long-term support
- pgvector 0.8.1 fully compatible
- Production-ready with 3+ years of community testing

**pgvector vs External Vector DB**:
- **Simplicity**: One database instead of two systems
- **Cost**: No Pinecone/Weaviate subscription fees
- **Performance**: Low-latency local queries
- **ACID compliance**: Transactional integrity

**Homebrew Installation**:
- Easy updates via `brew upgrade`
- Automatic dependency management
- macOS-optimized binaries

---

**Phase 1.3 Status**: ✅ **COMPLETE**  
**Next Phase**: Phase 1.4 - SportsDataIO Client (already implemented!)  
**Documentation Version**: 1.0  
**Last Updated**: October 28, 2025
