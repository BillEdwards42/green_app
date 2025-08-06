#!/usr/bin/env python3
"""
Check daily carbon progress data
"""

import asyncio
import sys
import os
from datetime import date, timedelta
from sqlalchemy import select, and_, desc

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.daily_carbon_progress import DailyCarbonProgress
from app.models.user import User


async def check_progress():
    """Check daily carbon progress for all users"""
    
    async with AsyncSessionLocal() as db:
        # Get recent progress entries
        result = await db.execute(
            select(DailyCarbonProgress, User)
            .join(User)
            .order_by(desc(DailyCarbonProgress.date), DailyCarbonProgress.user_id)
            .limit(20)
        )
        entries = result.all()
        
        if not entries:
            print("No daily carbon progress entries found")
            return
        
        print("\n" + "="*80)
        print("Recent Daily Carbon Progress")
        print("="*80)
        print(f"{'Date':<12} {'Username':<15} {'Daily (g)':<12} {'Cumulative (g)':<15} {'League':<10}")
        print("-"*80)
        
        current_user = None
        for progress, user in entries:
            # Add separator between users
            if current_user != user.username:
                if current_user is not None:
                    print("-"*80)
                current_user = user.username
            
            print(f"{progress.date!s:<12} {user.username:<15} "
                  f"{progress.daily_carbon_saved:>10.1f}  "
                  f"{progress.cumulative_carbon_saved:>13.1f}  "
                  f"{user.current_league:<10}")
        
        # Show monthly totals for active users
        print("\n" + "="*80)
        print("Current Month Totals")
        print("="*80)
        
        # Get users with carbon saved this month
        result = await db.execute(
            select(User)
            .where(User.current_month_carbon_saved > 0)
            .order_by(desc(User.current_month_carbon_saved))
        )
        users = result.scalars().all()
        
        if users:
            print(f"{'Username':<15} {'Month Total (g)':<15} {'League':<10} {'Total Lifetime (g)'}")
            print("-"*65)
            for user in users:
                print(f"{user.username:<15} {user.current_month_carbon_saved:>13.1f}  "
                      f"{user.current_league:<10} {user.total_carbon_saved:>15.1f}")
        else:
            print("No users with carbon saved this month")


def main():
    asyncio.run(check_progress())


if __name__ == "__main__":
    main()