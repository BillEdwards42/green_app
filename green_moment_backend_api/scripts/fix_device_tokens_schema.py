#!/usr/bin/env python3
"""
Fix device_tokens table schema - change user_id from integer to varchar
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def fix_schema():
    """Fix the device_tokens table schema"""
    
    async with AsyncSessionLocal() as db:
        try:
            print("🔧 Fixing device_tokens table schema...")
            
            # First, backup existing data
            print("\n📦 Backing up existing device tokens...")
            result = await db.execute(text("""
                SELECT * FROM device_tokens
            """))
            existing_tokens = result.fetchall()
            print(f"Found {len(existing_tokens)} existing tokens")
            
            # Drop the foreign key constraint first
            print("\n🔓 Dropping foreign key constraint...")
            await db.execute(text("""
                ALTER TABLE device_tokens 
                DROP CONSTRAINT IF EXISTS device_tokens_user_id_fkey
            """))
            
            # Change user_id column type to varchar
            print("\n🔄 Changing user_id column type to varchar...")
            await db.execute(text("""
                ALTER TABLE device_tokens 
                ALTER COLUMN user_id TYPE VARCHAR USING user_id::VARCHAR
            """))
            
            # Re-add the foreign key constraint (to users.id::varchar)
            print("\n🔒 Re-adding foreign key constraint...")
            await db.execute(text("""
                ALTER TABLE device_tokens 
                ADD CONSTRAINT device_tokens_user_id_fkey 
                FOREIGN KEY (user_id) REFERENCES users(id::varchar) ON DELETE CASCADE
            """))
            
            await db.commit()
            print("\n✅ Schema fixed successfully!")
            
            # Verify the change
            print("\n🔍 Verifying schema change...")
            result = await db.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'device_tokens' AND column_name = 'user_id'
            """))
            
            col_info = result.fetchone()
            if col_info:
                print(f"user_id column is now: {col_info.data_type}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            await db.rollback()
            
            # Try alternative approach
            print("\n🔄 Trying alternative approach...")
            try:
                # Create new table with correct schema
                print("Creating new table with correct schema...")
                await db.execute(text("""
                    CREATE TABLE device_tokens_new (
                        id VARCHAR PRIMARY KEY,
                        user_id VARCHAR NOT NULL,
                        token TEXT NOT NULL UNIQUE,
                        platform VARCHAR NOT NULL,
                        device_id VARCHAR NOT NULL,
                        app_version VARCHAR,
                        is_active BOOLEAN DEFAULT true,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),
                        last_used_at TIMESTAMP DEFAULT NOW()
                    )
                """))
                
                # Copy data if any exists
                if existing_tokens:
                    print("Copying existing data...")
                    for token in existing_tokens:
                        await db.execute(text("""
                            INSERT INTO device_tokens_new 
                            (id, user_id, token, platform, device_id, app_version, is_active, created_at, updated_at, last_used_at)
                            VALUES 
                            (:id, :user_id::varchar, :token, :platform, :device_id, :app_version, :is_active, :created_at, :updated_at, :last_used_at)
                        """), {
                            "id": token.id,
                            "user_id": str(token.user_id),
                            "token": token.token,
                            "platform": token.platform,
                            "device_id": token.device_id,
                            "app_version": token.app_version,
                            "is_active": token.is_active,
                            "created_at": token.created_at,
                            "updated_at": token.updated_at,
                            "last_used_at": token.last_used_at
                        })
                
                # Drop old table and rename new one
                print("Swapping tables...")
                await db.execute(text("DROP TABLE device_tokens"))
                await db.execute(text("ALTER TABLE device_tokens_new RENAME TO device_tokens"))
                
                # Add foreign key
                print("Adding foreign key...")
                await db.execute(text("""
                    ALTER TABLE device_tokens 
                    ADD CONSTRAINT device_tokens_user_id_fkey 
                    FOREIGN KEY (user_id) REFERENCES users(id::varchar) ON DELETE CASCADE
                """))
                
                await db.commit()
                print("\n✅ Schema fixed using alternative approach!")
                
            except Exception as e2:
                print(f"\n❌ Alternative approach also failed: {e2}")
                await db.rollback()


async def main():
    print("🔧 Device Tokens Schema Fixer")
    print("=" * 50)
    print("\nThis script will fix the device_tokens table schema")
    print("by changing user_id from integer to varchar to match the model.")
    
    confirm = input("\nProceed? (y/n): ").strip().lower()
    
    if confirm == 'y':
        await fix_schema()
    else:
        print("Cancelled.")


if __name__ == "__main__":
    asyncio.run(main())