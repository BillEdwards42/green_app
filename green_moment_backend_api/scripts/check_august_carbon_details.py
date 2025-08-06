#!/usr/bin/env python3
"""
Check all carbon details for August - chores and daily progress
"""
import asyncio
import sys
import os
from datetime import datetime, date

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, and_, func
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.chore import Chore
from app.models.daily_carbon_progress import DailyCarbonProgress


async def check_august_carbon(username: str):
    """Check all carbon data for August"""
    async with AsyncSessionLocal() as db:
        # Get user
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User '{username}' not found")
            return
            
        print(f"\n📊 User: {user.username}")
        print(f"Current League: {user.current_league}")
        print(f"Total Carbon Saved (lifetime): {user.total_carbon_saved:.2f}g CO2e")
        print(f"Current Month Carbon (in user record): {user.current_month_carbon_saved:.2f}g CO2e")
        
        # Get August date range
        aug_start = date(2025, 8, 1)
        aug_end = date(2025, 8, 31)
        
        # Check chores for August
        print(f"\n📋 August Chores:")
        result = await db.execute(
            select(Chore).where(
                and_(
                    Chore.user_id == user.id,
                    Chore.start_time >= aug_start,
                    Chore.start_time <= aug_end
                )
            ).order_by(Chore.start_time)
        )
        chores = result.scalars().all()
        
        print(f"  Total chores found: {len(chores)}")
        for chore in chores:
            print(f"  - {chore.start_time.date()}: {chore.appliance_type} "
                  f"({chore.duration_minutes} minutes)")
            
        if not chores:
            print("  No chores found for August!")
        
        # Check daily carbon progress for August
        print(f"\n📈 August Daily Carbon Progress:")
        result = await db.execute(
            select(DailyCarbonProgress).where(
                and_(
                    DailyCarbonProgress.user_id == user.id,
                    DailyCarbonProgress.date >= aug_start,
                    DailyCarbonProgress.date <= aug_end
                )
            ).order_by(DailyCarbonProgress.date)
        )
        daily_progress = result.scalars().all()
        
        total_daily_carbon = 0.0
        for progress in daily_progress:
            print(f"  - {progress.date}: {progress.daily_carbon_saved:.2f}g "
                  f"(cumulative: {progress.cumulative_carbon_saved:.2f}g)")
            total_daily_carbon += progress.daily_carbon_saved
            
        print(f"  Total from daily progress: {total_daily_carbon:.2f}g CO2e")
        
        # Summary
        print(f"\n📊 Summary:")
        print(f"  - Total chores logged: {len(chores)}")
        print(f"  - Daily progress records: {len(daily_progress)}")
        print(f"  - Daily progress total: {total_daily_carbon:.2f}g CO2e")
        print(f"  - User record shows: {user.current_month_carbon_saved:.2f}g")
        
        if len(chores) > 0 and len(daily_progress) == 0:
            print(f"\n⚠️  WARNING: Chores exist but no daily carbon calculations!")
            print(f"    Daily carbon calculation needs to run")
            
        # Check if daily carbon has been calculated for all days with chores
        chore_dates = set(chore.start_time.date() for chore in chores)
        progress_dates = set(progress.date for progress in daily_progress)
        missing_dates = chore_dates - progress_dates
        
        if missing_dates:
            print(f"\n🔴 Missing daily calculations for: {sorted(missing_dates)}")
            print(f"   Run: python scripts/carbon_daily_scheduler.py")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_august_carbon_details.py <username>")
        sys.exit(1)
        
    username = sys.argv[1]
    asyncio.run(check_august_carbon(username))