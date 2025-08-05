#!/usr/bin/env python3
"""
Apply soft delete migration to users table
"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings


async def apply_migration():
    """Apply soft delete migration"""
    
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.begin() as conn:
        try:
            # Add deleted_at column
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE
            """))
            print("✅ Added deleted_at column")
            
            # Drop unique constraint on google_id if it exists
            await conn.execute(text("""
                ALTER TABLE users 
                DROP CONSTRAINT IF EXISTS users_google_id_key
            """))
            print("✅ Dropped unique constraint on google_id")
            
            # Create index on google_id for performance
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_users_google_id 
                ON users(google_id)
            """))
            print("✅ Created index on google_id")
            
            # Show current table structure
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """))
            
            print("\n📋 Updated users table structure:")
            for row in result:
                print(f"  - {row[0]}: {row[1]} (nullable: {row[2]})")
                
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            raise
    
    await engine.dispose()


if __name__ == "__main__":
    print("🔄 Applying soft delete migration...")
    asyncio.run(apply_migration())
    print("\n✨ Migration completed successfully!")