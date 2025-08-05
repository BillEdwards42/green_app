#!/usr/bin/env python3
"""
Check all notification-related table schemas
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
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def check_schemas():
    """Check all table schemas"""
    
    async with AsyncSessionLocal() as db:
        print("🔍 Checking all notification-related table schemas...")
        
        # Check users table
        print("\n👤 users table:")
        result = await db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'id'
        """))
        for row in result:
            print(f"  - {row.column_name}: {row.data_type}")
        
        # Check device_tokens table
        print("\n📱 device_tokens table:")
        result = await db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'device_tokens' AND column_name IN ('id', 'user_id')
            ORDER BY ordinal_position
        """))
        for row in result:
            print(f"  - {row.column_name}: {row.data_type}")
            
        # Check notification_settings table
        print("\n🔔 notification_settings table:")
        result = await db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'notification_settings' AND column_name IN ('id', 'user_id')
            ORDER BY ordinal_position
        """))
        for row in result:
            print(f"  - {row.column_name}: {row.data_type}")
            
        # Check if notification_settings exists
        result = await db.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'notification_settings'
        """))
        count = result.scalar()
        if count == 0:
            print("  ❌ Table does not exist!")
            
        # Check foreign key constraints
        print("\n🔗 Foreign key constraints:")
        result = await db.execute(text("""
            SELECT 
                tc.constraint_name, 
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name IN ('device_tokens', 'notification_settings')
        """))
        for row in result:
            print(f"  - {row.table_name}.{row.column_name} -> {row.foreign_table_name}.{row.foreign_column_name}")


if __name__ == "__main__":
    asyncio.run(check_schemas())