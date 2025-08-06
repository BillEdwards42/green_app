#!/usr/bin/env python3
"""Check if carbon tracking tables exist"""

import asyncio
import sys
import os
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal


async def check_tables():
    async with AsyncSessionLocal() as db:
        # Check if daily_carbon_progress exists
        result = await db.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'daily_carbon_progress'
                );
            """)
        )
        table_exists = result.scalar()
        print(f"daily_carbon_progress table exists: {table_exists}")
        
        # Check if users table has new columns
        result = await db.execute(
            text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name IN ('current_month_carbon_saved', 'last_carbon_calculation_date');
            """)
        )
        columns = result.fetchall()
        print(f"\nUser table carbon columns:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]}")
        
        if table_exists:
            # Drop the table so migration can run
            print("\nDropping existing daily_carbon_progress table...")
            await db.execute(text("DROP TABLE IF EXISTS daily_carbon_progress CASCADE;"))
            await db.commit()
            print("Table dropped successfully")


if __name__ == "__main__":
    asyncio.run(check_tables())