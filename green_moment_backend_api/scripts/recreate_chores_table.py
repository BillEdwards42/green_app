#!/usr/bin/env python3
"""
Recreate chores table with new schema (for test environments only)
"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.database import Base, engine
from app.models.chore import Chore


async def recreate_chores_table():
    """Drop and recreate chores table with new schema"""
    
    async with engine.begin() as conn:
        # Drop the table if it exists
        await conn.execute(text("DROP TABLE IF EXISTS chores CASCADE"))
        print("✅ Dropped old chores table")
        
        # Create the table with new schema
        await conn.run_sync(Base.metadata.create_all, tables=[Chore.__table__])
        print("✅ Created new chores table with updated schema")
        
        # Show the new structure
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'chores'
            ORDER BY ordinal_position
        """))
        
        print("\n📋 New chores table structure:")
        for row in result:
            print(f"  - {row[0]}: {row[1]} (nullable: {row[2]})")


if __name__ == "__main__":
    print("🔄 Recreating chores table...")
    asyncio.run(recreate_chores_table())
    print("\n✨ Done! The chores table has been recreated with the new schema.")