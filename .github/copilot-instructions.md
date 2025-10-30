# GitHub Copilot Instructions for MCP Bets

## Project Overview

MCP Bets is a production-grade, multi-LLM sports betting intelligence system built on the Model Context Protocol (MCP). The system combines:

- **Backend**: FastAPI + SQLAlchemy 2.0 (async) with PostgreSQL 14 + pgvector for NFL data ingestion, caching, and vector embeddings
- **Data Sources**: SportsDataIO Partnership API (20+ endpoints: props, injuries, stats, odds)
- **Caching**: Multi-tier system (Redis + PostgreSQL) with 95%+ hit rate
- **LLM Integration**: Parallel judges (Claude 4.5, GPT-4o, Gemini 2.5 Pro) with consensus-based predictions (Phase 2+)
- **Frontend**: Next.js 14 + Auth0 authentication (Phase 5)

**Current Status**: Phase 1 (Data Foundation) complete. Phases 2-5 not yet implemented.

## Code Style & Standards

### Python/Backend Guidelines

#### Async/Await Conventions
- **ALWAYS use async/await** for database operations, API calls, and I/O
- Use `async def` for all service methods and data access
- Prefer `asyncio.gather()` for parallel operations
- Use `async for` with SQLAlchemy async sessions

```python
# ✅ Correct: Async database query
async def get_player_by_id(self, player_id: int) -> Optional[Player]:
    async with self.session() as session:
        result = await session.execute(
            select(Player).where(Player.id == player_id)
        )
        return result.scalar_one_or_none()

# ✅ Correct: Parallel API calls
props, injuries = await asyncio.gather(
    client.get_player_props_by_week(2024, 18),
    client.get_injuries_by_week(2024, 18)
)

# ❌ Wrong: Blocking synchronous calls
def get_player_by_id(self, player_id: int):  # No async
    result = session.execute(...)  # No await
```

#### SQLAlchemy 2.0 Best Practices
- Use **SQLAlchemy 2.0 syntax** (not 1.x)
- Prefer `select()` over `session.query()` (deprecated)
- Use `scalar()`, `scalars()`, `scalar_one_or_none()` for result extraction
- Always define relationships with `Mapped[T]` type hints
- Use `relationship(back_populates=...)` for bidirectional relationships

```python
# ✅ Correct: SQLAlchemy 2.0 syntax
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import select

class Player(Base):
    __tablename__ = "players"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    
    # Relationship with type hints
    team: Mapped["Team"] = relationship(back_populates="players")
    stats: Mapped[List["PlayerGameStats"]] = relationship(back_populates="player")

# ✅ Correct: Query with select()
query = select(Player).where(Player.team_id == team_id).order_by(Player.name)
result = await session.execute(query)
players = result.scalars().all()

# ❌ Wrong: Old SQLAlchemy 1.x syntax
players = session.query(Player).filter(Player.team_id == team_id).all()
```

#### FastAPI Patterns
- Use **Pydantic models** for request/response validation
- Implement **dependency injection** for database sessions and services
- Use **path and query parameters** with proper type hints
- Return **structured responses** (not raw dicts)
- Implement **exception handlers** for API errors

```python
# ✅ Correct: FastAPI endpoint with dependency injection
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

class PlayerPropResponse(BaseModel):
    player_id: int
    prop_type: str
    line: float
    over_odds: int
    under_odds: int

@router.get("/props/{week}", response_model=List[PlayerPropResponse])
async def get_props_by_week(
    week: int,
    season: int = Query(2024, ge=2024, le=2030),
    client: CachedSportsDataIOClient = Depends(get_cached_client)
) -> List[PlayerPropResponse]:
    """Get player props for specific week with caching"""
    try:
        props = await client.get_player_props_by_week(season, week)
        return [PlayerPropResponse(**prop) for prop in props]
    except Exception as e:
        logger.error(f"Failed to fetch props: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

#### SportsDataIO Integration Patterns
- **ALWAYS use cached client** (`CachedSportsDataIOClient`) instead of direct API client
- Check cache before making API calls
- Respect rate limits (2 req/sec, 10K/month quota)
- Use **header-based authentication** (never put API keys in URLs)
- Implement **secure logging** (filter API keys from all logs)

```python
# ✅ Correct: Use cached client
from mcp_bets.services.cache.cached_client import CachedSportsDataIOClient

client = CachedSportsDataIOClient(settings)
props = await client.get_player_props_by_week(2024, 18)
# Automatically cached with appropriate TTL

# ✅ Correct: Header-based authentication
headers = {"Ocp-Apim-Subscription-Key": settings.sportsdataio_api_key}
response = await httpx_client.get(url, headers=headers)

# ❌ Wrong: Direct API client (bypasses cache)
from mcp_bets.services.ingestion.sportsdataio_client import SportsDataIOClient
client = SportsDataIOClient(settings)  # Don't use directly!

# ❌ Wrong: API key in URL
url = f"https://api.com/data?api_key={api_key}"  # SECURITY VIOLATION
```

#### Cache Usage Patterns
- Use **cache-first reads** (check cache before API)
- Implement **write-through caching** (update cache on successful API calls)
- Apply **appropriate TTL** based on data volatility:
  - Static data (teams): 7 days
  - Daily data (schedules, players): 24 hours
  - Hourly data (stats): 1 hour
  - Volatile data (props, odds): 5 minutes
  - Real-time data (play-by-play): 1 minute
- Use **pattern-based invalidation** for bulk cache clears

```python
# ✅ Correct: Cache-first read
cache_key = self._build_cache_key("player_props", season=season, week=week)
cached_data = self.cache_manager.get(cache_key, CacheDataType.PLAYER_PROPS)
if cached_data:
    return cached_data

# Fetch from API and write-through to cache
data = await self.client.get_player_props_by_week(season, week)
self.cache_manager.set(cache_key, data, CacheDataType.PLAYER_PROPS)
return data

# ✅ Correct: Bulk invalidation
await client.invalidate_week_data(season=2024, week=18)
```

#### Security Rules (CRITICAL)
- **NEVER** hardcode API keys, passwords, or tokens in source code
- **ALWAYS** use environment variables via `Settings` class
- **NEVER** log sensitive data (API keys, passwords, auth tokens)
- **ALWAYS** use `SecureLogger` wrapper to sanitize logs
- **NEVER** put API keys in URLs (use headers instead)
- **ALWAYS** run `scripts/security_check.py` before commits

```python
# ✅ Correct: Environment-based configuration
from mcp_bets.core.settings import Settings

settings = Settings()  # Loads from .env file
api_key = settings.sportsdataio_api_key

# ✅ Correct: Secure logging
from mcp_bets.utils.secure_logging import SecureLogger

logger = SecureLogger(__name__)
logger.info(f"API response: {response}")  # API keys automatically filtered

# ❌ Wrong: Hardcoded secrets
api_key = "your-secret-key-here"  # SECURITY VIOLATION

# ❌ Wrong: Logging sensitive data
logger.info(f"Using API key: {api_key}")  # SECURITY VIOLATION
```

#### Error Handling
- Use **try/except blocks** for all external calls (API, database)
- Raise **specific exceptions** (not generic `Exception`)
- Log errors with **context** (not just error message)
- Return **user-friendly error messages** (not internal details)

```python
# ✅ Correct: Comprehensive error handling
from mcp_bets.exceptions import SportsDataIOError, CacheError

async def import_player_props(self, season: int, week: int):
    try:
        props = await self.client.get_player_props_by_week(season, week)
    except httpx.HTTPStatusError as e:
        logger.error(f"SportsDataIO API error: {e.response.status_code}")
        raise SportsDataIOError(f"Failed to fetch props for week {week}")
    except CacheError as e:
        logger.warning(f"Cache error (continuing): {e}")
        # Continue without cache
    except Exception as e:
        logger.exception(f"Unexpected error importing props for week {week}")
        raise
```

#### Testing Approaches
- Write **async tests** with `pytest-asyncio`
- Use **fixtures** for database sessions and test data
- Mock **external API calls** (don't hit real APIs in tests)
- Test **error cases** (not just happy paths)
- Use **test database** (not production)

```python
# ✅ Correct: Async test with fixtures
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_import_player_props(db_session, mock_api_client):
    """Test player props import with mocked API"""
    # Arrange
    mock_api_client.get_player_props_by_week = AsyncMock(
        return_value=[{"player_id": "123", "prop_type": "PassingYards"}]
    )
    service = DataIngestionService(db_session, settings)
    
    # Act
    await service.import_player_props_by_week(2024, 18)
    
    # Assert
    result = await db_session.execute(select(PlayerProp))
    props = result.scalars().all()
    assert len(props) == 1
    assert props[0].player_id == "123"
```

#### Type Hints
- Use **type hints for all function signatures**
- Import types from `typing` for Python 3.9 compatibility
- Use `Optional[T]` for nullable values
- Use `List[T]`, `Dict[K, V]` for collections (not `list`, `dict`)
- Use `Union[A, B]` for multiple types

```python
# ✅ Correct: Complete type hints (Python 3.9 compatible)
from typing import List, Dict, Optional, Union

async def get_players_by_team(
    self,
    team: str,
    active_only: bool = True
) -> List[Player]:
    """Get players for a team"""
    ...

async def get_player_prop(
    self,
    player_id: str
) -> Optional[Dict[str, Union[str, int, float]]]:
    """Get player prop (returns None if not found)"""
    ...
```

#### Naming Conventions
- **Classes**: `PascalCase` (e.g., `SportsDataIOClient`, `CacheManager`)
- **Functions/Methods**: `snake_case` (e.g., `get_player_props_by_week`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `API_BASE_URL`, `MAX_RETRIES`)
- **Private methods**: `_leading_underscore` (e.g., `_build_cache_key`)
- **Database models**: Singular noun (e.g., `Player`, not `Players`)
- **Database tables**: Plural noun (e.g., `players`, `teams`)

### TypeScript/React Guidelines
- Use functional components with hooks (no class components)
- Implement proper TypeScript interfaces - avoid `any` types
- Use explicit return types for functions
- Follow React best practices for state management
- Implement proper error boundaries and loading states

### Authentication System
- **CRITICAL**: Never modify the authentication flow without understanding the hybrid Auth0 approach
- Use existing interfaces from `/src/types/auth.ts`
- Leverage utility functions from `/src/utils/auth.ts` for auth operations
- Maintain compatibility with Auth0 React SDK while supporting custom UI

### File Structure Conventions
```
frontend/src/
├── components/          # Reusable UI components
├── pages/              # Page-level components (future)
├── services/           # API integration layers
├── types/              # TypeScript interfaces and types
├── utils/              # Utility functions and helpers
├── hooks/              # Custom React hooks (future)
└── styles/             # Global styles and themes (future)
```

## Authentication System Architecture

### Critical Implementation Details
The authentication system uses a **hybrid approach**:

1. **Custom UI**: `CustomLogin.tsx` provides branded login experience
2. **Direct API**: Uses Auth0's Resource Owner Password Grant for authentication
3. **Token Management**: Stores tokens in Auth0 SDK-compatible localStorage format
4. **State Management**: Combines Auth0 SDK state with custom authentication state

### Key Components to Understand
- `CustomLogin.tsx`: Main authentication interface
- `App.tsx`: Authentication state management
- `/types/auth.ts`: TypeScript interfaces for auth data
- `/utils/auth.ts`: Authentication utility functions

### Authentication Flow Preservation
- **DO NOT** change token storage keys or format
- **MAINTAIN** compatibility with Auth0 React SDK
- **PRESERVE** multi-connection fallback logic
- **KEEP** expiration time tracking in token storage

## Development Guidelines

### When Working on Authentication
1. **Read Documentation First**: Review `/docs/authentication-system.md`
2. **Test Thoroughly**: Authentication changes require extensive testing
3. **Maintain Backward Compatibility**: Don't break existing auth flow
4. **Use Existing Utilities**: Leverage functions from `/utils/auth.ts`

### Error Handling Standards
- Provide user-friendly error messages
- Implement proper loading states
- Use TypeScript for compile-time error prevention
- Log errors appropriately (avoid sensitive data in logs)

### Code Quality Requirements
- All new code must include proper TypeScript types
- Components should be properly documented with JSDoc
- Implement proper error boundaries for new features
- Follow existing naming conventions and patterns

## API Integration Patterns

### Frontend-Backend Communication
- Use `/services/` directory for API integration
- Implement proper error handling for API calls
- Use TypeScript interfaces for API responses
- Include loading states for async operations

### OpenAI Integration
- Backend handles OpenAI API calls for security
- Frontend sends prompts via backend API
- Implement proper response formatting and error handling

## Security Considerations

### Authentication Security
- Never expose Auth0 client secrets in frontend
- Validate tokens on both frontend and backend
- Implement proper token expiration handling
- Use HTTPS in production environments

### Data Protection
- Sanitize user inputs
- Implement proper CORS configuration
- Avoid storing sensitive data in localStorage
- Use environment variables for configuration

## Testing Strategy

### Authentication Testing
- Test login/logout flows thoroughly
- Verify token persistence across page reloads
- Test password reset functionality
- Validate error handling for various scenarios

### Component Testing
- Write unit tests for utility functions
- Test component rendering and user interactions
- Mock API calls in tests
- Test error states and edge cases

## Common Patterns

### State Management
```typescript
// Preferred state pattern
const [data, setData] = useState<TypeName | null>(null);
const [loading, setLoading] = useState<boolean>(false);
const [error, setError] = useState<string | null>(null);
```

### API Call Pattern
```typescript
// Preferred async pattern
const handleApiCall = async (): Promise<void> => {
  setLoading(true);
  setError(null);
  
  try {
    const result = await apiFunction();
    setData(result);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    setError(errorMessage);
  } finally {
    setLoading(false);
  }
};
```

### Component Structure
```typescript
// Preferred component pattern
interface ComponentProps {
  // Define props with proper types
}

const Component: React.FC<ComponentProps> = ({ prop1, prop2 }) => {
  // State and hooks
  // Event handlers
  // Render logic
  
  return (
    // JSX with proper TypeScript
  );
};

export default Component;
```

## Debugging Guidelines

### Authentication Issues
1. Check browser localStorage for token data
2. Verify Auth0 application configuration
3. Test API endpoints independently
4. Review network tab for failed requests
5. Check console for TypeScript/JavaScript errors

### Common Debug Points
- Token expiration and refresh logic
- Auth0 SDK state vs custom auth state
- API response parsing and error handling
- Component re-rendering and state updates

## Environment Setup

### Required Environment Variables
```bash
# Frontend (.env.local)
REACT_APP_AUTH0_DOMAIN=your-domain.auth0.com
REACT_APP_AUTH0_CLIENT_ID=your-client-id

# Backend (configure as needed)
OPENAI_API_KEY=your-openai-key
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_CLIENT_SECRET=your-client-secret
```

## Documentation Maintenance

### When Adding New Features
1. Update relevant documentation in `/docs/`
2. Add TypeScript interfaces to appropriate files
3. Update this copilot-instructions.md if patterns change
4. Include JSDoc comments for complex functions

### Documentation Standards
- Keep documentation current with code changes
- Use clear, concise language
- Include code examples for complex patterns
- Document breaking changes and migration paths

## Migration Considerations

### Future Auth0 Updates
- Monitor Auth0 SDK updates for breaking changes
- Test authentication flow after any Auth0 library updates
- Consider migrating to PKCE flow for enhanced security
- Plan for deprecation of Resource Owner Password Grant

### React/TypeScript Updates
- Keep dependencies updated regularly
- Test thoroughly after major version updates
- Update TypeScript types as needed
- Maintain backward compatibility where possible

---

**Note**: This document should be updated as the project evolves. Always refer to the latest version in the repository and update it when implementing significant changes or new patterns.

**Last Updated**: January 2025 (Phase 1 Complete)