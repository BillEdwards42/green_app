#!/usr/bin/env python3
"""
Reset user to bronze league for testing promotions
"""
import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, delete
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.monthly_summary import MonthlySummary
from app.models.task import UserTask


async def reset_to_bronze(username: str):
    """Reset user to bronze league and clear progress"""
    async with AsyncSessionLocal() as db:
        # Get user
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User '{username}' not found")
            return
            
        print(f"\n📊 Current State:")
        print(f"  - Username: {user.username}")
        print(f"  - Current League: {user.current_league}")
        print(f"  - Total Carbon Saved: {user.total_carbon_saved}g CO2e")
        print(f"  - Current Month Carbon: {user.current_month_carbon_saved}g CO2e")
        
        # Reset user to bronze
        user.current_league = 'bronze'
        user.current_month_carbon_saved = 0.0
        user.current_month_tasks_completed = 0
        
        # Delete all monthly summaries
        await db.execute(
            delete(MonthlySummary).where(MonthlySummary.user_id == user.id)
        )
        
        # Delete all user tasks for fresh start
        await db.execute(
            delete(UserTask).where(UserTask.user_id == user.id)
        )
        
        await db.commit()
        
        print(f"\n✅ Reset complete!")
        print(f"  - League: bronze")
        print(f"  - Monthly summaries: Cleared")
        print(f"  - User tasks: Cleared")
        print(f"  - Current month carbon: 0g")
        
        print(f"\n📝 Next steps:")
        print(f"  1. Close and reopen the app to get bronze tasks")
        print(f"  2. Use test_promotion_to_league.py to test each promotion")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python reset_user_to_bronze.py <username>")
        sys.exit(1)
        
    username = sys.argv[1]
    asyncio.run(reset_to_bronze(username))