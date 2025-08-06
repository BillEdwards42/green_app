#!/usr/bin/env python3
"""
Debug July carbon calculation issue
"""

import asyncio
import sys
import os
from datetime import datetime, date
from sqlalchemy import select, and_, func

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.chore import Chore
from app.models.daily_carbon_progress import DailyCarbonProgress


async def debug_july():
    """Debug July carbon calculation"""
    
    async with AsyncSessionLocal() as db:
        # Get edwards_test1
        result = await db.execute(
            select(User).where(User.username == "edwards_test1")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("User not found")
            return
        
        print(f"\n👤 User: {user.username} (ID: {user.id})")
        print(f"📊 Created: {user.created_at}")
        
        # Check July chores
        july_start = datetime(2025, 7, 1)
        july_end = datetime(2025, 7, 31, 23, 59, 59)
        
        result = await db.execute(
            select(Chore).where(
                and_(
                    Chore.user_id == user.id,
                    Chore.start_time >= july_start,
                    Chore.start_time <= july_end
                )
            ).order_by(Chore.start_time)
        )
        july_chores = result.scalars().all()
        
        print(f"\n📅 July Chores: {len(july_chores)}")
        for chore in july_chores[:5]:  # Show first 5
            print(f"  {chore.start_time.strftime('%Y-%m-%d %H:%M')} - {chore.appliance_type} ({chore.duration_minutes} min)")
        
        # Check daily carbon progress for July
        result = await db.execute(
            select(DailyCarbonProgress).where(
                and_(
                    DailyCarbonProgress.user_id == user.id,
                    DailyCarbonProgress.date >= date(2025, 7, 1),
                    DailyCarbonProgress.date <= date(2025, 7, 31)
                )
            ).order_by(DailyCarbonProgress.date)
        )
        july_progress = result.scalars().all()
        
        print(f"\n📈 July Daily Progress Entries: {len(july_progress)}")
        total_july = 0
        for progress in july_progress:
            print(f"  {progress.date}: {progress.daily_carbon_saved:.2f} g")
            total_july += progress.daily_carbon_saved
        
        print(f"\n💰 Total July Carbon: {total_july:.2f} g")
        
        # Check when chores were actually created
        print(f"\n🕰️ Chore Creation Times:")
        for chore in july_chores[:5]:
            print(f"  Start: {chore.start_time}, Created: {chore.created_at}")
            if chore.created_at.date() > chore.start_time.date():
                print(f"    ⚠️ Created AFTER the chore date!")


async def main():
    await debug_july()


if __name__ == "__main__":
    asyncio.run(main())