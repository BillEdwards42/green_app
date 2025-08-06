#!/usr/bin/env python3
"""
Test script to verify carbon calculation handles month boundaries correctly
"""

import asyncio
import sys
import os
from datetime import date, datetime, timedelta
from sqlalchemy import select, and_

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.daily_carbon_progress import DailyCarbonProgress
from app.services.carbon_calculator import DailyCarbonCalculator


async def test_month_boundary(username: str = None):
    """Test carbon calculation across month boundaries"""
    
    async with AsyncSessionLocal() as db:
        # Get user
        if username:
            result = await db.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()
            if not user:
                print(f"User '{username}' not found")
                return
        else:
            # Get first user
            result = await db.execute(
                select(User).limit(1)
            )
            user = result.scalar_one()
        
        print(f"\n🧪 Testing month boundary for user: {user.username}")
        print("=" * 60)
        
        # Show last few days of previous month and first few days of current month
        today = date.today()
        
        # Get entries around month boundary
        if today.day <= 5:
            # Early in month - show transition from last month
            start_date = date(today.year, today.month, 1) - timedelta(days=3)
            end_date = today
        else:
            # Show next month transition
            if today.month == 12:
                next_month_date = date(today.year + 1, 1, 1)
            else:
                next_month_date = date(today.year, today.month + 1, 1)
            start_date = next_month_date - timedelta(days=3)
            end_date = next_month_date + timedelta(days=2)
        
        print(f"\nChecking entries from {start_date} to {end_date}:")
        print("-" * 60)
        
        result = await db.execute(
            select(DailyCarbonProgress)
            .where(
                and_(
                    DailyCarbonProgress.user_id == user.id,
                    DailyCarbonProgress.date >= start_date,
                    DailyCarbonProgress.date <= end_date
                )
            )
            .order_by(DailyCarbonProgress.date)
        )
        entries = result.scalars().all()
        
        prev_month = None
        for entry in entries:
            month_marker = ""
            if prev_month and prev_month != entry.date.month:
                print("\n--- MONTH BOUNDARY ---\n")
            
            print(f"{entry.date}: Daily={entry.daily_carbon_saved:.3f}kg, "
                  f"Cumulative={entry.cumulative_carbon_saved:.3f}kg")
            
            # Verify cumulative resets on month boundary
            if entry.date.day == 1 and entry.cumulative_carbon_saved != entry.daily_carbon_saved:
                print("  ⚠️  WARNING: Cumulative should equal daily on day 1!")
            
            prev_month = entry.date.month
        
        if not entries:
            print("No entries found in this date range")
        
        # Show user's current month total
        print(f"\n📊 User's current_month_carbon_saved: {user.current_month_carbon_saved:.3f} kg")
        print(f"📅 Last calculation date: {user.last_carbon_calculation_date}")
        
        # Test running calculation for specific dates
        print("\n\n🔄 Testing calculation for specific dates...")
        
        calculator = DailyCarbonCalculator()
        
        # Test last day of month
        if today.day != 1:
            last_day_prev_month = date(today.year, today.month, 1) - timedelta(days=1)
            print(f"\nCalculating for {last_day_prev_month}...")
            await calculator.calculate_user_daily_carbon(db, user, last_day_prev_month)
        
        # Test first day of month
        first_day_month = date(today.year, today.month, 1)
        print(f"\nCalculating for {first_day_month}...")
        await calculator.calculate_user_daily_carbon(db, user, first_day_month)
        
        await db.commit()
        
        # Show updated entries
        print("\n📈 After recalculation:")
        print("-" * 60)
        
        result = await db.execute(
            select(DailyCarbonProgress)
            .where(
                and_(
                    DailyCarbonProgress.user_id == user.id,
                    DailyCarbonProgress.date >= start_date,
                    DailyCarbonProgress.date <= end_date
                )
            )
            .order_by(DailyCarbonProgress.date)
        )
        entries = result.scalars().all()
        
        prev_month = None
        for entry in entries:
            if prev_month and prev_month != entry.date.month:
                print("\n--- MONTH BOUNDARY ---\n")
            
            print(f"{entry.date}: Daily={entry.daily_carbon_saved:.3f}kg, "
                  f"Cumulative={entry.cumulative_carbon_saved:.3f}kg")
            
            prev_month = entry.date.month


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(test_month_boundary(username))


if __name__ == "__main__":
    main()