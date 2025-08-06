#!/usr/bin/env python3
"""
Check user's monthly carbon savings
"""

import asyncio
import sys
import os
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from sqlalchemy import select, and_, func

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.monthly_summary import MonthlySummary
from app.models.daily_carbon_progress import DailyCarbonProgress


async def check_monthly_carbon(username: str):
    """Check monthly carbon savings for a user"""
    
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
        print(f"📊 Current League: {user.current_league}")
        print(f"🌱 Total Lifetime Carbon Saved: {user.total_carbon_saved:.2f} g")
        print(f"📅 Current Month Carbon Saved: {user.current_month_carbon_saved:.2f} g")
        
        # Get last month's dates
        today = date.today()
        last_month_end = date(today.year, today.month, 1) - relativedelta(days=1)
        last_month_start = date(last_month_end.year, last_month_end.month, 1)
        
        print(f"\n📆 Last Month: {last_month_start} to {last_month_end}")
        
        # Check monthly summary for last month
        result = await db.execute(
            select(MonthlySummary).where(
                and_(
                    MonthlySummary.user_id == user.id,
                    MonthlySummary.month == last_month_end.month,
                    MonthlySummary.year == last_month_end.year
                )
            )
        )
        summary = result.scalar_one_or_none()
        
        if summary:
            print(f"\n📊 Last Month Summary:")
            print(f"  Total Carbon Saved: {summary.total_carbon_saved:.2f} g")
            print(f"  League Start: {summary.league_at_month_start}")
            print(f"  League End: {summary.league_at_month_end}")
            print(f"  Promoted: {'Yes' if summary.league_upgraded else 'No'}")
        
        # Calculate from daily progress
        result = await db.execute(
            select(func.sum(DailyCarbonProgress.daily_carbon_saved)).where(
                and_(
                    DailyCarbonProgress.user_id == user.id,
                    DailyCarbonProgress.date >= last_month_start,
                    DailyCarbonProgress.date <= last_month_end
                )
            )
        )
        daily_sum = result.scalar() or 0
        
        print(f"\n📈 Last Month from Daily Progress: {daily_sum:.2f} g")
        
        # Show promotion thresholds
        print(f"\n🎯 Promotion Thresholds:")
        print(f"  Bronze → Silver: 30 g CO2e")
        print(f"  Silver → Gold: 300 g CO2e")
        print(f"  Gold → Emerald: 500 g CO2e")
        print(f"  Emerald → Diamond: 1,000 g CO2e (1 kg)")
        
        # Check if eligible
        thresholds = {
            "bronze": 30,
            "silver": 300,
            "gold": 500,
            "emerald": 1000
        }
        
        if user.current_league in thresholds:
            threshold = thresholds[user.current_league]
            if daily_sum >= threshold:
                print(f"\n✅ ELIGIBLE for promotion! ({daily_sum:.0f} >= {threshold})")
            else:
                print(f"\n❌ Not eligible ({daily_sum:.0f} < {threshold})")
                print(f"   Need {threshold - daily_sum:.0f} more grams")


async def main():
    if len(sys.argv) < 2:
        print("Usage: python check_user_monthly_carbon.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    await check_monthly_carbon(username)


if __name__ == "__main__":
    asyncio.run(main())