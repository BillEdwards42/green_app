#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.migrate_historical_carbon import HistoricalCarbonMigration
from app.core.database import AsyncSessionLocal

async def run():
    migration = HistoricalCarbonMigration()
    async with AsyncSessionLocal() as db:
        await migration.migrate_all_users(db)

if __name__ == "__main__":
    asyncio.run(run())