#!/usr/bin/env python3
"""Manually apply carbon system migration"""

import asyncio
import sys
import os
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal


async def apply_migration():
    async with AsyncSessionLocal() as db:
        try:
            # First drop the table if it exists
            print("Dropping existing daily_carbon_progress table if exists...")
            await db.execute(text("DROP TABLE IF EXISTS daily_carbon_progress CASCADE;"))
            await db.commit()
            
            # Add columns to users table
            print("Adding carbon tracking columns to users table...")
            
            # Check if columns already exist
            result = await db.execute(
                text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    AND column_name IN ('current_month_carbon_saved', 'last_carbon_calculation_date');
                """)
            )
            existing_columns = [row[0] for row in result.fetchall()]
            
            if 'current_month_carbon_saved' not in existing_columns:
                await db.execute(
                    text("ALTER TABLE users ADD COLUMN current_month_carbon_saved FLOAT NOT NULL DEFAULT 0.0;")
                )
                print("  - Added current_month_carbon_saved")
            else:
                print("  - current_month_carbon_saved already exists")
            
            if 'last_carbon_calculation_date' not in existing_columns:
                await db.execute(
                    text("ALTER TABLE users ADD COLUMN last_carbon_calculation_date DATE;")
                )
                print("  - Added last_carbon_calculation_date")
            else:
                print("  - last_carbon_calculation_date already exists")
            
            # Create daily_carbon_progress table
            print("\nCreating daily_carbon_progress table...")
            await db.execute(text("""
                CREATE TABLE daily_carbon_progress (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    date DATE NOT NULL,
                    daily_carbon_saved FLOAT NOT NULL DEFAULT 0.0,
                    cumulative_carbon_saved FLOAT NOT NULL DEFAULT 0.0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                    CONSTRAINT unique_user_date UNIQUE (user_id, date)
                );
            """))
            
            # Create indexes
            print("Creating indexes...")
            await db.execute(text("CREATE INDEX ix_daily_carbon_progress_user_id ON daily_carbon_progress(user_id);"))
            await db.execute(text("CREATE INDEX ix_daily_carbon_progress_date ON daily_carbon_progress(date);"))
            
            # Update alembic version
            print("\nUpdating alembic version to 007...")
            await db.execute(text("UPDATE alembic_version SET version_num = '007' WHERE version_num = '006';"))
            
            await db.commit()
            print("\n✅ Migration applied successfully!")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error applying migration: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(apply_migration())