#!/usr/bin/env python3
"""
Recalculate all August carbon savings for a specific user
"""
import asyncio
import sys
import os
from datetime import date, timedelta

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, and_
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.chore import Chore
from app.services.carbon_calculator_grams import DailyCarbonCalculator


async def recalculate_august_for_user(username: str):
    """Recalculate all August days for a specific user"""
    async with AsyncSessionLocal() as db:
        # Get user
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User '{username}' not found")
            return
            
        print(f"\n📊 Recalculating August carbon for: {user.username}")
        print(f"Current Month Carbon (before): {user.current_month_carbon_saved:.2f}g CO2e")
        
        # Get all August dates (up to today)
        aug_start = date(2025, 8, 1)
        today = date.today()
        aug_end = min(date(2025, 8, 31), today)
        
        # Check which days have chores
        result = await db.execute(
            select(Chore.start_time).where(
                and_(
                    Chore.user_id == user.id,
                    Chore.start_time >= aug_start,
                    Chore.start_time <= aug_end
                )
            ).distinct()
        )
        chore_dates = set(chore.date() for chore, in result)
        
        print(f"\n📅 Found chores on {len(chore_dates)} days in August")
        
        # Calculate carbon for each day in August
        calculator = DailyCarbonCalculator()
        current_date = aug_start
        total_calculated = 0.0
        
        print("\n🔄 Calculating daily carbon:")
        while current_date <= aug_end:
            if current_date in chore_dates:
                print(f"  - {current_date}: ", end='', flush=True)
                try:
                    # Calculate for this specific user and date
                    daily_carbon = await calculator.calculate_daily_carbon_for_user(
                        db, user.id, current_date
                    )
                    total_calculated += daily_carbon
                    print(f"{daily_carbon:.2f}g CO2e")
                except Exception as e:
                    print(f"ERROR: {e}")
            else:
                # No chores on this day
                print(f"  - {current_date}: No chores")
                
            current_date += timedelta(days=1)
        
        # Refresh user data
        await db.refresh(user)
        
        print(f"\n✅ Recalculation complete!")
        print(f"  - Total calculated: {total_calculated:.2f}g CO2e")
        print(f"  - Current Month Carbon (after): {user.current_month_carbon_saved:.2f}g CO2e")
        
        # Run the recalculate current month script to ensure consistency
        from scripts.recalculate_current_month import recalculate_current_month
        await recalculate_current_month(username)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python recalculate_august_carbon.py <username>")
        sys.exit(1)
        
    username = sys.argv[1]
    asyncio.run(recalculate_august_for_user(username))