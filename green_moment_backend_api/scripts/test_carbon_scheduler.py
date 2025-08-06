#!/usr/bin/env python3
"""
Test Carbon Scheduler Logic
Allows testing the scheduler behavior for specific dates
"""

import asyncio
import sys
import os
from datetime import date, datetime, timedelta
from unittest.mock import patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.services.carbon_calculator_grams import DailyCarbonCalculator
from scripts.carbon_league_promotion import CarbonLeaguePromotion


async def test_scheduler_for_date(test_date: date):
    """Test scheduler logic for a specific date"""
    print(f"\n{'='*60}")
    print(f"Testing scheduler logic for date: {test_date}")
    print(f"Day of month: {test_date.day}")
    print(f"{'='*60}\n")
    
    # Calculate yesterday relative to test date
    yesterday = test_date - timedelta(days=1)
    print(f"Would calculate carbon for: {yesterday}")
    
    # Check if promotion would run
    if test_date.day == 1:
        print("✅ Would run promotion check (1st of month)")
        
        # Show what month would be checked
        last_month = test_date - timedelta(days=1)
        print(f"   Checking promotions for: {last_month.strftime('%B %Y')}")
    else:
        print("⏭️  Would skip promotion check (not 1st of month)")
    
    # Optionally run actual calculation for testing
    if input("\nRun actual calculation? (y/n): ").lower() == 'y':
        calculator = DailyCarbonCalculator()
        async with AsyncSessionLocal() as db:
            await calculator.calculate_daily_carbon_for_all_users(db, yesterday)
            print("✅ Daily calculation completed")
            
            if test_date.day == 1:
                promotion_service = CarbonLeaguePromotion()
                await promotion_service.check_and_promote_all_users(db, test_mode=False)
                print("✅ Promotion check completed")


async def test_month_boundary():
    """Test month boundary behavior"""
    print("\n" + "="*60)
    print("Testing Month Boundary Behavior")
    print("="*60)
    
    # Test end of month
    test_dates = [
        date(2025, 8, 31),  # Last day of month
        date(2025, 9, 1),   # First day of next month
        date(2025, 9, 2),   # Second day of month
    ]
    
    for test_date in test_dates:
        await test_scheduler_for_date(test_date)


async def test_specific_date():
    """Test a specific date provided by user"""
    date_str = input("Enter date to test (YYYY-MM-DD): ")
    try:
        test_date = date.fromisoformat(date_str)
        await test_scheduler_for_date(test_date)
    except ValueError:
        print("Invalid date format. Use YYYY-MM-DD")


async def simulate_full_month():
    """Simulate running the scheduler for a full month"""
    print("\n" + "="*60)
    print("Simulating Full Month")
    print("="*60)
    
    month = int(input("Enter month (1-12): "))
    year = int(input("Enter year: "))
    
    # Get all dates in the month
    current_date = date(year, month, 1)
    
    while current_date.month == month:
        print(f"\n--- Day {current_date.day} ---")
        yesterday = current_date - timedelta(days=1)
        print(f"Would calculate carbon for: {yesterday}")
        
        if current_date.day == 1:
            print("✅ Would run promotion check")
        
        current_date += timedelta(days=1)


def main():
    print("Carbon Scheduler Test Utility")
    print("1. Test month boundary behavior")
    print("2. Test specific date")
    print("3. Simulate full month")
    print("4. Test today's date")
    
    choice = input("\nSelect option (1-4): ")
    
    if choice == "1":
        asyncio.run(test_month_boundary())
    elif choice == "2":
        asyncio.run(test_specific_date())
    elif choice == "3":
        asyncio.run(simulate_full_month())
    elif choice == "4":
        asyncio.run(test_scheduler_for_date(date.today()))
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()