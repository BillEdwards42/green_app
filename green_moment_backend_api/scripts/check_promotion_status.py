#!/usr/bin/env python3
"""
Check user's promotion status and monthly summaries
"""
import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, and_
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.monthly_summary import MonthlySummary


async def check_promotion_status(username: str):
    """Check if user should see promotion animation"""
    async with AsyncSessionLocal() as db:
        # Get user
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User '{username}' not found")
            return
            
        print(f"\n📊 User Information:")
        print(f"  - Username: {user.username}")
        print(f"  - Current League: {user.current_league}")
        print(f"  - Total Carbon Saved: {user.total_carbon_saved}g CO2e")
        print(f"  - Current Month Carbon: {user.current_month_carbon_saved}g CO2e")
        
        # Get last month's summary
        last_month = datetime.now().month - 1 if datetime.now().month > 1 else 12
        last_year = datetime.now().year if datetime.now().month > 1 else datetime.now().year - 1
        
        result = await db.execute(
            select(MonthlySummary).where(
                and_(
                    MonthlySummary.user_id == user.id,
                    MonthlySummary.month == last_month,
                    MonthlySummary.year == last_year
                )
            )
        )
        last_month_summary = result.scalar_one_or_none()
        
        print(f"\n📅 Last Month Summary (Month {last_month}, Year {last_year}):")
        if last_month_summary:
            print(f"  - League at end: {last_month_summary.league_at_month_end}")
            print(f"  - Total carbon saved: {last_month_summary.total_carbon_saved}g CO2e")
            print(f"  - Tasks completed: {last_month_summary.tasks_completed}")
            print(f"  - League upgraded: {last_month_summary.league_upgraded}")
            print(f"  - Should show animation: {last_month_summary.league_upgraded}")
        else:
            print("  - No summary found for last month")
            
        # Check all monthly summaries
        result = await db.execute(
            select(MonthlySummary)
            .where(MonthlySummary.user_id == user.id)
            .order_by(MonthlySummary.year.desc(), MonthlySummary.month.desc())
        )
        all_summaries = result.scalars().all()
        
        print(f"\n📆 All Monthly Summaries:")
        for summary in all_summaries:
            print(f"  - {summary.year}-{summary.month:02d}: "
                  f"League: {summary.league_at_month_end}, "
                  f"Upgraded: {summary.league_upgraded}, "
                  f"Carbon: {summary.total_carbon_saved}g")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_promotion_status.py <username>")
        sys.exit(1)
        
    username = sys.argv[1]
    asyncio.run(check_promotion_status(username))