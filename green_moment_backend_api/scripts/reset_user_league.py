#!/usr/bin/env python3
"""Reset a user to bronze league"""

import asyncio
import sys
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Add parent directory to path
sys.path.insert(0, '/home/bill/StudioProjects/green_moment_backend_api')

from app.core.database import AsyncSessionLocal
from app.models.user import User


async def reset_user_to_bronze(username: str):
    """Reset user to bronze league"""
    async with AsyncSessionLocal() as db:
        # Find user
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User '{username}' not found")
            return
        
        print(f"Found user: {user.username} (current league: {user.current_league})")
        
        # Reset to bronze
        user.current_league = 'bronze'
        user.current_month_carbon_saved = 0.0
        user.last_month_co2e_saved_g = 0.0
        
        await db.commit()
        print(f"✅ User '{username}' reset to bronze league")
        print(f"   - League: bronze")
        print(f"   - Current month carbon: 0.0g")
        print(f"   - Last month carbon: 0.0g")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python reset_user_league.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    asyncio.run(reset_user_to_bronze(username))