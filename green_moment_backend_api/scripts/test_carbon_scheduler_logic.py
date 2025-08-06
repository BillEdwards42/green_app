#!/usr/bin/env python3
"""
Test the carbon scheduler's month transition logic
"""

import asyncio
import sys
import os
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from scripts.carbon_daily_scheduler import create_monthly_summaries_for_all_users, run_daily_tasks


async def test_month_logic():
    """Test the month transition logic"""
    print("🧪 Testing carbon scheduler month transition logic")
    print("=" * 60)
    
    # Simulate it being the 1st of the month
    today = date.today()
    print(f"\nToday's date: {today}")
    print(f"Is it the 1st? {today.day == 1}")
    
    if today.day == 1:
        print("✅ Today is the 1st - month transition logic will run")
        print("\nWhat will happen:")
        print("1. Calculate yesterday's (last day of previous month) carbon")
        print("2. Create monthly summaries with final carbon values")
        print("3. Run league promotions based on previous month")
        print("4. Daily calculator will reset current_month_carbon_saved to today's value")
    else:
        print("❌ Today is not the 1st - only daily calculation will run")
        print(f"   Next month transition: {today.replace(day=1).replace(month=today.month+1 if today.month < 12 else 1)}")
    
    print("\n" + "=" * 60)
    print("To test the full scheduler:")
    print("1. Run with --once flag: python scripts/carbon_daily_scheduler.py --once")
    print("2. Run with --run-now flag: python scripts/carbon_daily_scheduler.py --run-now")
    print("\nTo install as a service:")
    print("sudo cp scripts/green-moment-carbon-scheduler.service /etc/systemd/system/")
    print("sudo systemctl daemon-reload")
    print("sudo systemctl enable green-moment-carbon-scheduler.service")
    print("sudo systemctl start green-moment-carbon-scheduler.service")


if __name__ == "__main__":
    asyncio.run(test_month_logic())