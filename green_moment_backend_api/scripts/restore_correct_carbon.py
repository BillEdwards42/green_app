#!/usr/bin/env python3
"""
Restore correct carbon value from daily progress records
"""
import asyncio
import sys
import os
from datetime import datetime, date

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.daily_carbon_progress import DailyCarbonProgress


async def restore_carbon_from_daily_progress(username: str):
    """Restore user's current month carbon from daily progress records"""
    async with AsyncSessionLocal() as db:
        # Get user
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User '{username}' not found")
            return
            
        print(f"\n📊 Current Status:")
        print(f"  - Username: {user.username}")
        print(f"  - Current League: {user.current_league}")
        print(f"  - Current Month Carbon (incorrect): {user.current_month_carbon_saved:.2f}g")
        
        # Calculate actual carbon from daily progress
        month_start = date(datetime.now().year, datetime.now().month, 1)
        
        result = await db.execute(
            select(func.sum(DailyCarbonProgress.daily_carbon_saved)).where(
                DailyCarbonProgress.user_id == user.id,
                DailyCarbonProgress.date >= month_start
            )
        )
        actual_carbon = result.scalar() or 0.0
        
        print(f"  - Actual Carbon (from daily progress): {actual_carbon:.2f}g")
        
        # Update user record
        user.current_month_carbon_saved = actual_carbon
        await db.commit()
        
        print(f"\n✅ Carbon value restored!")
        print(f"  - Current Month Carbon: {actual_carbon:.2f}g")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python restore_correct_carbon.py <username>")
        sys.exit(1)
        
    username = sys.argv[1]
    asyncio.run(restore_carbon_from_daily_progress(username))