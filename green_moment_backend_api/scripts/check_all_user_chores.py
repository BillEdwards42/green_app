#!/usr/bin/env python3
"""
Check ALL chores for a user
"""

import asyncio
import sys
import os
from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.chore import Chore


async def check_all_chores(username: str):
    """Check all chores for a user"""
    
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
        
        # Get ALL chores
        result = await db.execute(
            select(Chore).where(
                Chore.user_id == user.id
            ).order_by(Chore.start_time)
        )
        all_chores = result.scalars().all()
        
        print(f"\n📋 ALL Chores ({len(all_chores)} total):")
        print("-" * 100)
        print(f"{'ID':<6} {'Start Date':<12} {'Start Time':<8} {'Appliance':<20} {'Duration':<10} {'Created At'}")
        print("-" * 100)
        
        for chore in all_chores:
            date = chore.start_time.strftime('%Y-%m-%d')
            time = chore.start_time.strftime('%H:%M:%S')
            created = chore.created_at.strftime('%Y-%m-%d %H:%M:%S')
            print(f"{chore.id:<6} {date:<12} {time:<8} {chore.appliance_type:<20} {chore.duration_minutes:<10} {created}")


async def main():
    if len(sys.argv) < 2:
        print("Usage: python check_all_user_chores.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    await check_all_chores(username)


if __name__ == "__main__":
    asyncio.run(main())