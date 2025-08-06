#!/usr/bin/env python3
"""
Fix platform values in device_tokens table
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal


async def fix_platform_values():
    async with AsyncSessionLocal() as db:
        print("🔧 Fixing platform values in device_tokens table...")
        
        # First, check current values
        result = await db.execute(text("SELECT DISTINCT platform FROM device_tokens"))
        
        print("\nCurrent platform values:")
        for row in result:
            print(f"  - {row.platform}")
        
        # Update values - The model expects lowercase values
        print("\n🔄 Updating uppercase values to lowercase...")
        
        # Update ANDROID to android
        result = await db.execute(text("""
            UPDATE device_tokens 
            SET platform = 'android'
            WHERE platform = 'ANDROID'
        """))
        print(f"  - Updated {result.rowcount} ANDROID -> android")
        
        # Update IOS to ios
        result = await db.execute(text("""
            UPDATE device_tokens 
            SET platform = 'ios'
            WHERE platform = 'IOS'
        """))
        print(f"  - Updated {result.rowcount} IOS -> ios")
        
        # Also handle any mixed case
        result = await db.execute(text("""
            UPDATE device_tokens 
            SET platform = LOWER(platform)
            WHERE platform != LOWER(platform)
        """))
        print(f"  - Updated {result.rowcount} mixed case values")
        
        await db.commit()
        
        # Verify the fix
        result = await db.execute(text("SELECT DISTINCT platform FROM device_tokens"))
        
        print("\n✅ Updated platform values:")
        for row in result:
            print(f"  - {row.platform}")
        
        print("\n✅ Platform values fixed!")


if __name__ == "__main__":
    asyncio.run(fix_platform_values())