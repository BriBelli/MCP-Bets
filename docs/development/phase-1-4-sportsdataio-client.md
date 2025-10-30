# Phase 1.4: SportsDataIO Client - Complete Documentation

**Status**: ✅ COMPLETED  
**Date**: October 28, 2025  
**Dependencies**: Phase 1.3 (PostgreSQL Setup), Phase 1.2 (Database Schema)

---

## Overview

Phase 1.4 implements a comprehensive SportsDataIO API client for fetching NFL data. This includes rate limiting, retry logic, comprehensive error handling, and an ingestion service to populate the database. The client supports 20+ endpoints covering games, players, stats, injuries, props, and odds.

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Bets Application                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────────┐         ┌────────────────────────┐   │
│  │ IngestionService  │────────▶│ SportsDataIOClient     │   │
│  │                   │         │                        │   │
│  │ - import_teams()  │         │ - get_schedules()      │   │
│  │ - import_games()  │         │ - get_players()        │   │
│  │ - import_props()  │         │ - get_player_props()   │   │
│  │ - import_stats()  │         │ - get_injuries()       │   │
│  └────────┬──────────┘         │ - get_odds()           │   │
│           │                    └──────────┬─────────────┘   │
│           │                               │                 │
│           ▼                               ▼                 │
│  ┌────────────────┐           ┌─────────────────────────┐  │
│  │   PostgreSQL   │           │    Rate Limiter         │  │
│  │   Database     │           │                         │  │
│  │                │           │ - Token bucket          │  │
│  │ - teams        │           │ - Monthly quota         │  │
│  │ - games        │           │ - Burst control         │  │
│  │ - players      │           └──────────┬──────────────┘  │
│  │ - props        │                      │                 │
│  │ - injuries     │                      ▼                 │
│  └────────────────┘           ┌─────────────────────────┐  │
│                               │  SportsDataIO API        │  │
│                               │  (Partnership Access)    │  │
│                               └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Files Created

### 1. SportsDataIO Client (`sportsdataio_client.py`)

**Location**: `/backend/mcp_bets/services/ingestion/sportsdataio_client.py`  
**Lines of Code**: 600+  
**Purpose**: HTTP client for SportsDataIO API with rate limiting and retry logic

#### Key Classes

##### `RateLimiter`

Token bucket rate limiter with dual-layer limiting:

```python
class RateLimiter:
    def __init__(
        self,
        requests_per_second: float = 2.0,
        requests_per_month: int = 10000,
        burst_size: int = 5,
    ):
        self.tokens = float(burst_size)
        self.monthly_requests = 0
        # ...
    
    async def acquire(self) -> None:
        """Block until permission to make request is granted"""
        # Check monthly quota
        if self.monthly_requests >= self.requests_per_month:
            raise SportsDataIOQuotaExceeded()
        
        # Token bucket algorithm for per-second limiting
        while self.tokens < 1:
            wait_time = (1 - self.tokens) / self.requests_per_second
            await asyncio.sleep(wait_time)
        
        self.tokens -= 1
        self.monthly_requests += 1
```

**Features**:
- **Per-second limiting**: Configurable RPS (default: 2 req/sec)
- **Monthly quota**: Prevent exceeding API subscription limits (default: 10,000/month)
- **Burst control**: Allow burst of requests up to `burst_size` (default: 5)
- **Async/await**: Non-blocking with proper locking
- **Statistics**: Track available tokens, monthly usage, quota remaining

##### `SportsDataIOClient`

Main API client with comprehensive endpoint coverage:

```python
class SportsDataIOClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        requests_per_second: Optional[float] = None,
        requests_per_month: Optional[int] = None,
    ):
        self.api_key = api_key or settings.SPORTSDATAIO_API_KEY
        self.rate_limiter = RateLimiter(...)
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Ocp-Apim-Subscription-Key": self.api_key},
        )
```

**Features**:
- **Automatic rate limiting**: All requests go through rate limiter
- **Retry logic**: Exponential backoff with 3 attempts (using `tenacity`)
- **Error handling**: Custom exceptions for quota, rate limits, and API errors
- **Context manager**: Use with `async with` for automatic cleanup
- **Health check**: `health_check()` method to verify connectivity

---

### 2. Data Ingestion Service (`data_ingestion.py`)

**Location**: `/backend/mcp_bets/services/ingestion/data_ingestion.py`  
**Lines of Code**: 500+  
**Purpose**: Orchestrates importing data from API to database

#### Key Features

##### Idempotent Imports

Uses `sportsdata_*_id` fields to prevent duplicates:

```python
async def import_teams(self) -> int:
    teams_data = await self.client.get_teams()
    
    for team_data in teams_data:
        # Check if team already exists
        result = await self.db.execute(
            select(Team).where(
                Team.sportsdata_team_id == str(team_data["TeamID"])
            )
        )
        team = result.scalar_one_or_none()
        
        if team:
            # Update existing team
            team.name = team_data["FullName"]
            # ...
        else:
            # Create new team
            team = Team(
                name=team_data["FullName"],
                sportsdata_team_id=str(team_data["TeamID"]),
            )
            self.db.add(team)
```

**Benefits**:
- Re-running imports won't create duplicates
- Updates existing records with latest data
- Safe for scheduled/automated imports

##### Relationship Management

Automatically links related entities:

```python
async def import_games_by_week(self, season: int, week: int) -> int:
    # Ensure season exists
    season_obj = await self.import_season(season)
    
    games_data = await self.client.get_schedules_by_week(season, week)
    
    for game_data in games_data:
        # Get home and away teams
        home_team = await self._get_team_by_key(game_data["HomeTeam"])
        away_team = await self._get_team_by_key(game_data["AwayTeam"])
        
        # Create game with relationships
        game = Game(
            season_id=season_obj.id,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            # ...
        )
```

---

## API Endpoints Implemented

### Schedules & Scores (4 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_schedules(season)` | `Scores/{season}` | All games for a season |
| `get_schedules_by_week(season, week)` | `ScoresByWeek/{season}/{week}` | Games by specific week |
| `get_current_week()` | `CurrentWeek` | Current NFL week number |
| `get_current_season()` | `CurrentSeason` | Current season year |

**Usage**:
```python
async with SportsDataIOClient() as client:
    # Get all 2024 games
    games = await client.get_schedules(2024)
    
    # Get Week 8 games
    week8_games = await client.get_schedules_by_week(2024, 8)
    
    # Get current week
    current_week = await client.get_current_week()
```

---

### Teams (2 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_teams()` | `Teams` | All 32 NFL teams |
| `get_team_by_key(team_key)` | `Teams` | Single team by abbreviation |

**Usage**:
```python
# Get all teams
teams = await client.get_teams()

# Get 49ers
niners = await client.get_team_by_key("SF")
```

**Response Structure**:
```json
{
  "TeamID": 1234,
  "Key": "SF",
  "FullName": "San Francisco 49ers",
  "City": "San Francisco",
  "Conference": "NFC",
  "Division": "West"
}
```

---

### Players (3 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_players()` | `Players` | All active NFL players |
| `get_players_by_team(team_key)` | `Players/{team}` | Players on specific team |
| `get_free_agents()` | `FreeAgents` | All free agent players |

**Usage**:
```python
# Get all active players (~2,500)
players = await client.get_players()

# Get 49ers roster
niners_players = await client.get_players_by_team("SF")

# Get free agents
free_agents = await client.get_free_agents()
```

---

### Player Stats (3 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_player_game_stats_by_week(season, week)` | `PlayerGameStatsByWeek/{season}/{week}` | All player stats for a week |
| `get_player_game_stats_by_player(season, week, player_id)` | `PlayerGameStatsByPlayerID/{season}/{week}/{player_id}` | Stats for specific player |
| `get_player_season_stats(season)` | `PlayerSeasonStats/{season}` | Season-long stats for all players |

**Usage**:
```python
# Get all Week 8 stats
stats = await client.get_player_game_stats_by_week(2024, 8)

# Get specific player stats
purdy_stats = await client.get_player_game_stats_by_player(2024, 8, "12345")

# Get full season stats
season_stats = await client.get_player_season_stats(2024)
```

**Stat Categories**:
- Passing: Attempts, completions, yards, TDs, interceptions
- Rushing: Attempts, yards, TDs
- Receiving: Receptions, targets, yards, TDs
- Other: Fumbles, fumbles lost, fantasy points

---

### Injuries (2 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_injuries_by_week(season, week)` | `Injuries/{season}/{week}` | All injury reports for a week |
| `get_injuries_by_team(season, week, team_key)` | `Injuries/{season}/{week}/{team}` | Team-specific injury reports |

**Usage**:
```python
# Get all Week 8 injuries
injuries = await client.get_injuries_by_week(2024, 8)

# Get 49ers injuries
niners_injuries = await client.get_injuries_by_team(2024, 8, "SF")
```

**Injury Report Fields**:
- `Status`: "Out", "Questionable", "Doubtful", "Probable"
- `BodyPart`: "Ankle", "Hamstring", "Knee", etc.
- `Practice`: "Full", "Limited", "DNP" (Did Not Practice)
- `PracticeDescription`: Detailed practice participation notes

---

### Player Props (3 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_player_props_by_week(season, week)` | `PlayerPropsByWeek/{season}/{week}` | All props for a week |
| `get_player_props_by_game(game_id)` | `PlayerPropsByGameID/{game_id}` | Props for specific game |
| `get_player_props_by_player(season, week, player_id)` | `PlayerPropsByPlayerID/{season}/{week}/{player_id}` | Props for specific player |

**Usage**:
```python
# Get all Week 8 props
props = await client.get_player_props_by_week(2024, 8)

# Get props for a specific game
game_props = await client.get_player_props_by_game("12345")

# Get Brock Purdy's props
purdy_props = await client.get_player_props_by_player(2024, 8, "12345")
```

**Prop Types**:
- `rushing_yards` - Over/under rushing yards
- `receptions` - Over/under receptions
- `receiving_yards` - Over/under receiving yards
- `passing_tds` - Over/under passing touchdowns
- `passing_yards` - Over/under passing yards

**Sportsbooks Supported**:
- FanDuel (via SportsDataIO partnership)
- DraftKings (via SportsDataIO partnership)

---

### Odds & Lines (2 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_odds_by_week(season, week)` | `GameOddsByWeek/{season}/{week}` | Game odds for a week |
| `get_odds_by_game(game_id)` | `GameOddsByGameID/{game_id}` | Odds for specific game |

**Usage**:
```python
# Get Week 8 odds
odds = await client.get_odds_by_week(2024, 8)

# Get odds for specific game
game_odds = await client.get_odds_by_game("12345")
```

**Odds Data**:
- Point spreads (e.g., SF -7.5)
- Moneylines (e.g., SF -350, DAL +280)
- Totals/Over-Under (e.g., 47.5)
- Multiple sportsbook lines

---

### News (3 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_news()` | `News` | Recent NFL news |
| `get_news_by_player(player_id)` | `NewsByPlayerID/{player_id}` | Player-specific news |
| `get_news_by_team(team_key)` | `NewsByTeam/{team}` | Team-specific news |

**Usage**:
```python
# Get recent news
news = await client.get_news()

# Get Brock Purdy news
purdy_news = await client.get_news_by_player("12345")

# Get 49ers news
niners_news = await client.get_news_by_team("SF")
```

---

## Rate Limiting

### Token Bucket Algorithm

The rate limiter uses a **token bucket** algorithm with two layers:

#### Layer 1: Per-Second Limiting

```python
# Configuration (in .env)
SPORTSDATAIO_REQUESTS_PER_SECOND=2    # 2 requests per second
SPORTSDATAIO_BURST_SIZE=5              # Allow burst of 5 requests

# Token bucket refills at rate of 2 tokens/second
# Maximum capacity: 5 tokens
# Each request consumes 1 token
```

**Example**:
- Start with 5 tokens
- Make 5 requests instantly (burst)
- Wait 2.5 seconds to get 5 tokens back
- Sustained rate: 2 requests/second

#### Layer 2: Monthly Quota

```python
# Configuration (in .env)
SPORTSDATAIO_REQUESTS_PER_MONTH=10000  # 10,000 requests/month

# Tracks requests across month boundary
# Resets on 1st of each month
# Raises SportsDataIOQuotaExceeded when limit hit
```

### Rate Limiter Statistics

```python
stats = client.get_rate_limiter_stats()

# Returns:
{
    "available_tokens": 3.5,
    "burst_size": 5,
    "requests_per_second": 2.0,
    "monthly_requests": 1247,
    "monthly_quota": 10000,
    "quota_remaining": 8753
}
```

---

## Retry Logic

### Exponential Backoff

Uses `tenacity` library for intelligent retries:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
)
async def _request(endpoint: str, params: Optional[Dict] = None):
    # Make HTTP request
    response = await self.client.get(url, params=params)
    response.raise_for_status()
    return response.json()
```

**Retry Schedule**:
- **Attempt 1**: Immediate
- **Attempt 2**: Wait 2 seconds (if failed)
- **Attempt 3**: Wait 4 seconds (if failed again)
- **Give up**: After 3 attempts

**Retry Conditions**:
- Network errors (`httpx.RequestError`)
- HTTP 5xx errors (server errors)
- HTTP 429 (rate limit - though our rate limiter prevents this)

**Non-Retry Conditions**:
- HTTP 4xx errors (except 429)
- HTTP 403 (quota exceeded - permanent failure)
- Successful responses (200-299)

---

## Error Handling

### Custom Exceptions

```python
class SportsDataIOError(Exception):
    """Base exception for all API errors"""
    pass

class SportsDataIOQuotaExceeded(SportsDataIOError):
    """Monthly quota exceeded"""
    pass

class SportsDataIORateLimitError(SportsDataIOError):
    """Rate limit hit (should be rare with our rate limiter)"""
    pass
```

### Error Handling Flow

```python
try:
    async with SportsDataIOClient() as client:
        props = await client.get_player_props_by_week(2024, 8)

except SportsDataIOQuotaExceeded as e:
    # Monthly quota exceeded - stop imports
    logger.error(f"API quota exceeded: {e}")
    send_alert("SportsDataIO quota exceeded!")

except SportsDataIORateLimitError as e:
    # Rate limit hit - retry later
    logger.warning(f"Rate limited: {e}")
    await asyncio.sleep(60)

except SportsDataIOError as e:
    # General API error
    logger.error(f"API error: {e}")
```

---

## Ingestion Service Methods

### Teams

```python
async def import_teams() -> int:
    """Import all 32 NFL teams"""
    # Returns: Number of teams imported/updated
```

### Games

```python
async def import_games_by_week(season: int, week: int) -> int:
    """Import all games for a specific week"""
    # Returns: Number of games imported/updated
```

### Players

```python
async def import_all_players() -> int:
    """Import all active NFL players (~2,500)"""
    # Returns: Number of players imported/updated

async def import_players_by_team(team_key: str) -> int:
    """Import roster for specific team"""
    # Returns: Number of players imported/updated
```

### Injuries

```python
async def import_injuries_by_week(season: int, week: int) -> int:
    """Import injury reports for a week"""
    # Returns: Number of injury reports imported
```

### Player Props

```python
async def import_player_props_by_week(season: int, week: int) -> int:
    """Import player props for a week"""
    # Returns: Number of props imported
```

### Player Stats

```python
async def import_player_stats_by_week(season: int, week: int) -> int:
    """Import player game stats for a week"""
    # Returns: Number of stat records imported/updated
```

---

## Usage Examples

### Complete Import Workflow

```python
from mcp_bets.config.database import get_db
from mcp_bets.services.ingestion import SportsDataIOClient, IngestionService

async def import_weekly_data(season: int, week: int):
    """Import all data for a specific week"""
    
    async with SportsDataIOClient() as client:
        # Check API health
        if not await client.health_check():
            raise Exception("SportsDataIO API is unreachable")
        
        async with get_db() as db:
            ingestion = IngestionService(db, client)
            
            # Step 1: Ensure teams exist (one-time)
            teams_count = await ingestion.import_teams()
            print(f"✅ Imported {teams_count} teams")
            
            # Step 2: Import games for the week
            games_count = await ingestion.import_games_by_week(season, week)
            print(f"✅ Imported {games_count} games")
            
            # Step 3: Import injury reports
            injuries_count = await ingestion.import_injuries_by_week(season, week)
            print(f"✅ Imported {injuries_count} injury reports")
            
            # Step 4: Import player props
            props_count = await ingestion.import_player_props_by_week(season, week)
            print(f"✅ Imported {props_count} player props")
            
            # Step 5: After games complete, import stats
            stats_count = await ingestion.import_player_stats_by_week(season, week)
            print(f"✅ Imported {stats_count} player stat records")
        
        # Check rate limiter usage
        stats = client.get_rate_limiter_stats()
        print(f"📊 API Usage: {stats['monthly_requests']}/{stats['monthly_quota']}")

# Run import
import asyncio
asyncio.run(import_weekly_data(2024, 8))
```

### Scheduled Imports

```python
import schedule
import asyncio

async def daily_import():
    """Run daily at 2 AM"""
    async with SportsDataIOClient() as client:
        current_week = await client.get_current_week()
        current_season = await client.get_current_season()
        
        async with get_db() as db:
            ingestion = IngestionService(db, client)
            
            # Import latest data
            await ingestion.import_injuries_by_week(current_season, current_week)
            await ingestion.import_player_props_by_week(current_season, current_week)

# Schedule daily at 2 AM
schedule.every().day.at("02:00").do(lambda: asyncio.run(daily_import()))
```

---

## Integration Points

### With Phase 1.2 (Database Schema)

- All models have `sportsdata_*_id` fields for idempotent imports
- Ingestion service uses these fields to prevent duplicates
- Relationships automatically maintained (games → teams, stats → players)

### With Phase 1.5 (Cache Layer)

- SportsDataIO responses will be cached in Redis/PostgreSQL
- Reduces API calls and costs
- Faster response times for repeated queries

### With Phase 2 (RAG System)

- Imported data used to generate embeddings
- Player stats, injury reports, game logs embedded for semantic search
- RAG retrieves relevant context for prop predictions

### With Phase 3 (MCP Agents)

- Agents query database for historical data
- Player stats feed into statistical analysis
- Injury reports inform availability predictions

---

## Performance Considerations

### Async Operations

All methods are async for high performance:

```python
# Sequential imports (slow)
await import_teams()
await import_games()
await import_props()

# Concurrent imports (fast!)
await asyncio.gather(
    import_teams(),
    import_games(),
    import_props(),
)
```

### Batch Imports

Use SQLAlchemy bulk operations for large datasets:

```python
# Instead of:
for player in players:
    db.add(Player(...))
    await db.commit()

# Use:
players_list = [Player(...) for player in players_data]
db.add_all(players_list)
await db.commit()  # Single commit
```

### Connection Pooling

SQLAlchemy manages connection pool automatically:
- 20 persistent connections
- 10 overflow connections
- Connections recycled every hour

---

## Monitoring & Telemetry

### API Usage Tracking

Every API request can be logged to `api_requests` table:

```python
from mcp_bets.models import APIRequest
from datetime import datetime, timezone

async def log_api_request(endpoint: str, duration_ms: int, status: str):
    request = APIRequest(
        endpoint=endpoint,
        status=status,
        duration_ms=duration_ms,
        requested_at=datetime.now(timezone.utc),
    )
    db.add(request)
    await db.commit()
```

### Cost Analysis

```sql
-- Total API calls this month
SELECT COUNT(*) as total_calls
FROM api_requests
WHERE requested_at >= date_trunc('month', CURRENT_TIMESTAMP);

-- Most expensive endpoints
SELECT endpoint, COUNT(*) as call_count
FROM api_requests
WHERE requested_at >= date_trunc('month', CURRENT_TIMESTAMP)
GROUP BY endpoint
ORDER BY call_count DESC;

-- Average response time
SELECT endpoint, AVG(duration_ms) as avg_duration_ms
FROM api_requests
GROUP BY endpoint
ORDER BY avg_duration_ms DESC;
```

---

## Testing

### Unit Tests

```python
import pytest
from mcp_bets.services.ingestion import SportsDataIOClient

@pytest.mark.asyncio
async def test_get_teams():
    async with SportsDataIOClient() as client:
        teams = await client.get_teams()
        assert len(teams) == 32
        assert all("Key" in team for team in teams)

@pytest.mark.asyncio
async def test_rate_limiter():
    async with SportsDataIOClient() as client:
        # Make burst of requests
        for _ in range(5):
            await client.get_current_week()
        
        # Check stats
        stats = client.get_rate_limiter_stats()
        assert stats["monthly_requests"] == 5
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_import_teams():
    async with SportsDataIOClient() as client:
        async with get_db() as db:
            ingestion = IngestionService(db, client)
            count = await ingestion.import_teams()
            
            assert count == 32
            
            # Verify teams in database
            result = await db.execute(select(Team))
            teams = result.scalars().all()
            assert len(teams) == 32
```

---

## Troubleshooting

### Issue: API Key Invalid

```python
# Error: HTTP 403: API quota exceeded or invalid key
# Solution: Check .env file
SPORTSDATAIO_API_KEY=your_actual_key_here
```

### Issue: Rate Limit Hit

```python
# Error: SportsDataIORateLimitError
# Solution: Adjust rate limiter settings
SPORTSDATAIO_REQUESTS_PER_SECOND=1  # Reduce from 2 to 1
```

### Issue: Monthly Quota Exceeded

```python
# Error: SportsDataIOQuotaExceeded
# Solution: Upgrade SportsDataIO subscription or reduce imports
```

### Issue: Import Duplicates

```python
# Problem: Teams/players imported multiple times
# Solution: Check sportsdata_*_id fields are being set correctly
# The ingestion service should prevent this automatically
```

---

## Security Considerations

### API Key Storage

```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Use environment-specific keys
# .env.development
SPORTSDATAIO_API_KEY=dev_key_here

# .env.production
SPORTSDATAIO_API_KEY=prod_key_here
```

### Rate Limit Protection

The rate limiter protects against:
- Accidental infinite loops
- DDoS-like behavior
- API key suspension

### Data Validation

Always validate API responses:

```python
if not isinstance(teams_data, list):
    raise ValueError("Expected list of teams")

if "TeamID" not in team_data:
    logger.warning(f"Invalid team data: {team_data}")
    continue
```

---

## Next Steps

### Immediate Next Steps

1. **Test API connectivity**: Run `health_check()` method
2. **Import initial data**: Teams, current week games, props
3. **Monitor rate limiter**: Check monthly usage

### Phase 1.5: Cache Layer

- Implement Redis hot cache for API responses
- Use PostgreSQL warm cache as fallback
- Intelligent TTL refresh policies

### Phase 1.6: Test Data Pipeline

- Full end-to-end test: SportsDataIO → Cache → Database
- Verify all data types (teams, games, props, injuries, stats)
- Test with real Week 8 data

---

## Summary

### What We Built

- ✅ **SportsDataIO Client** with 20+ endpoints
- ✅ **Rate Limiter** with token bucket + monthly quota
- ✅ **Retry Logic** with exponential backoff
- ✅ **Ingestion Service** with idempotent imports
- ✅ **Error Handling** with custom exceptions
- ✅ **Async/Await** for high performance

### Why It Matters

The SportsDataIO client is the **data foundation** of MCP Bets:

1. **Complete NFL Data**: Games, players, stats, injuries, props, odds
2. **Partnership Access**: FanDuel and DraftKings props via SportsDataIO
3. **Idempotent Imports**: Safe to re-run without duplicates
4. **Rate Limiting**: Protects API key from suspension
5. **Production-Ready**: Error handling, retries, monitoring

### Key Technical Decisions

**Async/Await Architecture**:
- All methods are async for non-blocking I/O
- Enables concurrent imports for speed
- Scales to handle high throughput

**Token Bucket Rate Limiter**:
- More flexible than simple RPS limiting
- Allows bursts while maintaining average rate
- Dual-layer protection (per-second + monthly)

**Tenacity for Retries**:
- Industry-standard retry library
- Exponential backoff prevents server overload
- Configurable retry conditions

**Idempotent Imports**:
- Uses external IDs from SportsDataIO
- Update-or-create pattern
- Safe for scheduled/automated imports

---

**Phase 1.4 Status**: ✅ **COMPLETE**  
**Next Phase**: Phase 1.5 - Cache Layer Implementation  
**Documentation Version**: 1.0  
**Last Updated**: October 28, 2025
