#!/usr/bin/env python3
"""
Manual test runner for carbon scheduler
Allows testing the scheduler without waiting for 5:50PM
"""

import asyncio
import sys
import os
from datetime import date, datetime, timedelta
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.services.carbon_calculator_grams import DailyCarbonCalculator
from scripts.carbon_league_promotion import CarbonLeaguePromotion


async def run_for_date(target_date: date = None, force_promotion: bool = False):
    """Run carbon calculation for a specific date with optional promotion check"""
    
    if target_date is None:
        # Default to yesterday
        target_date = date.today() - timedelta(days=1)
    
    print(f"\n{'='*60}")
    print(f"Running Carbon Scheduler Manually")
    print(f"Target date for calculation: {target_date}")
    print(f"{'='*60}\n")
    
    # Run daily carbon calculation
    print(f"📊 Calculating carbon savings for {target_date}...")
    calculator = DailyCarbonCalculator()
    
    async with AsyncSessionLocal() as db:
        await calculator.calculate_daily_carbon_for_all_users(db, target_date)
        print("✅ Daily carbon calculation completed\n")
    
    # Check if we should run promotion
    tomorrow = target_date + timedelta(days=1)
    should_run_promotion = tomorrow.day == 1 or force_promotion
    
    if should_run_promotion:
        print("🏆 Running promotion check...")
        
        if force_promotion:
            print("   (Forced promotion check)")
        else:
            print(f"   (Tomorrow is the 1st of {tomorrow.strftime('%B')})")
        
        promotion_service = CarbonLeaguePromotion()
        async with AsyncSessionLocal() as db:
            # Use test_mode=True if forcing promotion
            await promotion_service.check_and_promote_all_users(db, test_mode=force_promotion)
            print("✅ Promotion check completed\n")
    else:
        print(f"⏭️  Skipping promotion check (tomorrow is day {tomorrow.day})\n")


def main():
    parser = argparse.ArgumentParser(description='Manually run carbon scheduler')
    parser.add_argument('--date', type=str, help='Date to calculate for (YYYY-MM-DD)')
    parser.add_argument('--yesterday', action='store_true', help='Calculate for yesterday (default)')
    parser.add_argument('--today', action='store_true', help='Calculate for today')
    parser.add_argument('--force-promotion', action='store_true', help='Force promotion check even if not 1st of month')
    
    args = parser.parse_args()
    
    # Determine target date
    if args.date:
        try:
            target_date = date.fromisoformat(args.date)
        except ValueError:
            print("Error: Invalid date format. Use YYYY-MM-DD")
            sys.exit(1)
    elif args.today:
        target_date = date.today()
    else:
        # Default to yesterday
        target_date = date.today() - timedelta(days=1)
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Run the calculation
    asyncio.run(run_for_date(target_date, args.force_promotion))


if __name__ == "__main__":
    main()