#!/usr/bin/env python3
"""
Fix platform enum values in database from lowercase to uppercase
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def fix_enum_values():
    async with AsyncSessionLocal() as db:
        print("🔧 Fixing platform enum values in device_tokens table...")
        
        # First, check current values
        result = await db.execute(text("""
            SELECT DISTINCT platform FROM device_tokens
        """))
        
        print("\nCurrent platform values:")
        for row in result:
            print(f"  - {row.platform}")
        
        # Update lowercase values to uppercase
        print("\n🔄 Updating 'android' to 'ANDROID'...")
        await db.execute(text("""
            UPDATE device_tokens 
            SET platform = 'ANDROID'::platform_type 
            WHERE platform = 'android'::platform_type
        """))
        
        print("🔄 Updating 'ios' to 'IOS'...")
        await db.execute(text("""
            UPDATE device_tokens 
            SET platform = 'IOS'::platform_type 
            WHERE platform = 'ios'::platform_type
        """))
        
        await db.commit()
        
        # Verify the fix
        result = await db.execute(text("""
            SELECT DISTINCT platform FROM device_tokens
        """))
        
        print("\n✅ Updated platform values:")
        for row in result:
            print(f"  - {row.platform}")
        
        print("\n✅ Platform enum values fixed!")


if __name__ == "__main__":
    asyncio.run(fix_enum_values())