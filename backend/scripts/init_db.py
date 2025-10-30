#!/usr/bin/env python3
"""
Database Initialization Script

This script:
1. Enables the pgvector extension in PostgreSQL
2. Creates all database tables from SQLAlchemy models
3. Verifies the schema was created successfully
4. Prints detailed information about the created tables

Usage:
    python scripts/init_db.py
"""

import sys
from pathlib import Path

# Add parent directory to path to import mcp_bets package
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import inspect, text
from mcp_bets.config.database import engine, init_database
from mcp_bets.models import (
    Base,
    Season,
    Team,
    Player,
    Game,
    Injury,
    PlayerGameStats,
    PlayerProp,
    Embedding,
    JudgePerformance,
    CacheEntry,
    APIRequest,
    APIKey,
)


def check_pgvector_extension():
    """Check if pgvector extension is enabled"""
    print("Checking pgvector extension...")
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM pg_extension WHERE extname = 'vector'")
        )
        if result.fetchone():
            print("✅ pgvector extension is enabled")
            return True
        else:
            print("❌ pgvector extension is NOT enabled")
            return False


def enable_pgvector():
    """Enable pgvector extension"""
    print("\nEnabling pgvector extension...")
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        print("✅ pgvector extension enabled successfully")
        return True
    except Exception as e:
        print(f"⚠️  pgvector extension not available: {e}")
        print("⚠️  Phase 2 (RAG) will require pgvector, but Phase 1 will work without it")
        print("⚠️  Continuing with database initialization...")
        return False  # Return False but don't fail the whole init


def create_all_tables(pgvector_enabled=False):
    """Create all tables defined in models"""
    print("\nCreating database tables...")
    try:
        if not pgvector_enabled:
            # Skip embeddings table if pgvector not available (Phase 2 only)
            print("⚠️  Skipping 'embeddings' table (pgvector required, Phase 2 only)")
            tables_to_create = [
                table for table in Base.metadata.sorted_tables 
                if table.name != "embeddings"
            ]
            for table in tables_to_create:
                table.create(bind=engine, checkfirst=True)
        else:
            Base.metadata.create_all(bind=engine)
        
        print("✅ All Phase 1 tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False


def verify_tables(pgvector_enabled=False):
    """Verify all expected tables exist"""
    print("\nVerifying database schema...")
    
    expected_tables = [
        "seasons",
        "teams",
        "players",
        "games",
        "injuries",
        "player_game_stats",
        "player_props",
        "judges_performance",
        "cache_entries",
        "api_requests",
        "api_keys",
    ]
    
    # Only expect embeddings table if pgvector is enabled
    if pgvector_enabled:
        expected_tables.append("embeddings")
    else:
        print("⚠️  Not expecting 'embeddings' table (pgvector disabled, Phase 2 only)")
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    print(f"\nFound {len(existing_tables)} tables in database:")
    for table in sorted(existing_tables):
        status = "✅" if table in expected_tables else "⚠️"
        print(f"  {status} {table}")
    
    missing_tables = set(expected_tables) - set(existing_tables)
    if missing_tables:
        print(f"\n❌ Missing tables: {', '.join(missing_tables)}")
        return False
    
    print(f"\n✅ All expected Phase 1 tables exist ({len(expected_tables)} tables)")
    return True


def print_table_details():
    """Print detailed information about each table"""
    print("\n" + "="*80)
    print("DATABASE SCHEMA DETAILS")
    print("="*80)
    
    inspector = inspect(engine)
    
    for table_name in sorted(inspector.get_table_names()):
        print(f"\n📋 Table: {table_name}")
        print("-" * 80)
        
        # Get columns
        columns = inspector.get_columns(table_name)
        print(f"Columns ({len(columns)}):")
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            col_type = str(col['type'])
            default = f" DEFAULT {col['default']}" if col.get('default') else ""
            print(f"  • {col['name']}: {col_type} {nullable}{default}")
        
        # Get foreign keys
        foreign_keys = inspector.get_foreign_keys(table_name)
        if foreign_keys:
            print(f"\nForeign Keys ({len(foreign_keys)}):")
            for fk in foreign_keys:
                print(f"  • {fk['constrained_columns']} → {fk['referred_table']}.{fk['referred_columns']}")
        
        # Get indexes
        indexes = inspector.get_indexes(table_name)
        if indexes:
            print(f"\nIndexes ({len(indexes)}):")
            for idx in indexes:
                unique = "UNIQUE" if idx['unique'] else "INDEX"
                print(f"  • {unique}: {idx['name']} on {idx['column_names']}")


def main():
    """Main initialization function"""
    print("="*80)
    print("MCP BETS - DATABASE INITIALIZATION")
    print("="*80)
    
    # Step 1: Check/Enable pgvector (optional for Phase 1)
    pgvector_enabled = False
    if not check_pgvector_extension():
        pgvector_enabled = enable_pgvector()
        # Don't fail if pgvector isn't available - it's only needed for Phase 2
    else:
        pgvector_enabled = True
    
    # Step 2: Create tables (pass pgvector flag)
    if not create_all_tables(pgvector_enabled=pgvector_enabled):
        print("\n❌ Database initialization FAILED")
        return False
    
    # Step 3: Verify tables (pass pgvector flag)
    if not verify_tables(pgvector_enabled=pgvector_enabled):
        print("\n❌ Database initialization FAILED")
        return False
    
    # Step 4: Print details
    print_table_details()
    
    print("\n" + "="*80)
    print("✅ DATABASE INITIALIZATION COMPLETE!")
    print("="*80)
    print("\nYou can now:")
    print("  1. Run the FastAPI application")
    print("  2. Import data from SportsDataIO")
    print("  3. Generate embeddings for RAG system")
    print("  4. Start making predictions!\n")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
