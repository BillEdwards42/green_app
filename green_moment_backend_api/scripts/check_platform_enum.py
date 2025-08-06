#!/usr/bin/env python3
"""
Check the platform enum definition in the database
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal


async def check_enum():
    async with AsyncSessionLocal() as db:
        print("🔍 Checking platform enum definition...")
        
        # Get enum values from PostgreSQL
        result = await db.execute(text("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (
                SELECT oid 
                FROM pg_type 
                WHERE typname = 'platformtype'
            )
            ORDER BY enumsortorder
        """))
        
        print("\nEnum 'platformtype' values:")
        for row in result:
            print(f"  - {row.enumlabel}")
        
        # Check column definition
        result = await db.execute(text("""
            SELECT column_name, data_type, udt_name
            FROM information_schema.columns
            WHERE table_name = 'device_tokens' AND column_name = 'platform'
        """))
        
        print("\nColumn definition:")
        for row in result:
            print(f"  - Column: {row.column_name}")
            print(f"  - Data type: {row.data_type}")
            print(f"  - UDT name: {row.udt_name}")
        
        # Check actual values
        result = await db.execute(text("""
            SELECT DISTINCT platform, COUNT(*) as count
            FROM device_tokens
            GROUP BY platform
        """))
        
        print("\nActual values in database:")
        for row in result:
            print(f"  - {row.platform}: {row.count} records")


if __name__ == "__main__":
    asyncio.run(check_enum())