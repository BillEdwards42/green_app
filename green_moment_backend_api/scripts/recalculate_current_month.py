#!/usr/bin/env python3
"""Recalculate current month carbon for a user"""

import asyncio
import sys
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

# Add parent directory to path
sys.path.insert(0, '/home/bill/StudioProjects/green_moment_backend_api')

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.daily_carbon_progress import DailyCarbonProgress


async def recalculate_current_month(username: str):
    """Recalculate current month carbon total"""
    async with AsyncSessionLocal() as db:
        # Find user
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User '{username}' not found")
            return
        
        # Get current month's start
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1).date()
        
        # Sum all daily carbon for current month
        result = await db.execute(
            select(func.sum(DailyCarbonProgress.daily_carbon_saved)).where(
                DailyCarbonProgress.user_id == user.id,
                DailyCarbonProgress.date >= month_start
            )
        )
        month_total = result.scalar() or 0.0
        
        print(f"Current month carbon for {username}: {month_total:.1f}g")
        
        # Update user
        user.current_month_carbon_saved = month_total
        await db.commit()
        
        print(f"✅ Updated current month carbon to {month_total:.1f}g")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python recalculate_current_month.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    asyncio.run(recalculate_current_month(username))