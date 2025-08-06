#!/usr/bin/env python3
"""
Check user's chores by month
"""

import asyncio
import sys
import os
from datetime import datetime
from sqlalchemy import select, and_, func

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.chore import Chore


async def check_chores(username: str):
    """Check chores for a user grouped by month"""
    
    async with AsyncSessionLocal() as db:
        # Get user
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"User {username} not found")
            return
        
        print(f"\n👤 User: {user.username}")
        print(f"📊 Created: {user.created_at.date()}")
        
        # Get all chores grouped by month
        result = await db.execute(
            select(
                func.date_trunc('month', Chore.start_time).label('month'),
                func.count(Chore.id).label('count'),
                func.sum(Chore.duration_minutes).label('total_minutes')
            ).where(
                Chore.user_id == user.id
            ).group_by(
                'month'
            ).order_by('month')
        )
        
        monthly_stats = result.all()
        
        print(f"\n📅 Chores by Month:")
        print("-" * 50)
        for month, count, total_minutes in monthly_stats:
            print(f"{month.strftime('%Y-%m')}: {count} chores, {total_minutes} minutes")
        
        # Get recent chores
        result = await db.execute(
            select(Chore).where(
                Chore.user_id == user.id
            ).order_by(Chore.start_time.desc()).limit(10)
        )
        chores = result.scalars().all()
        
        print(f"\n📋 Recent 10 Chores:")
        print("-" * 80)
        print(f"{'Date':<12} {'Time':<8} {'Appliance':<20} {'Duration':<10} {'Created'}")
        print("-" * 80)
        
        for chore in chores:
            date = chore.start_time.strftime('%Y-%m-%d')
            time = chore.start_time.strftime('%H:%M')
            created = chore.created_at.strftime('%Y-%m-%d %H:%M')
            print(f"{date:<12} {time:<8} {chore.appliance_type:<20} {chore.duration_minutes:<10} {created}")


async def main():
    if len(sys.argv) < 2:
        print("Usage: python check_user_chores_by_month.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    await check_chores(username)


if __name__ == "__main__":
    asyncio.run(main())