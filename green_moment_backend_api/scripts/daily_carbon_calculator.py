#!/usr/bin/env python3
"""
Daily Carbon Calculator Script
Runs daily to calculate carbon savings for all users
"""

import asyncio
import sys
import os
from datetime import date, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.services.carbon_calculator_grams import DailyCarbonCalculator


async def run_daily_calculation(target_date: date = None):
    """Run daily carbon calculation for all users"""
    calculator = DailyCarbonCalculator()
    
    async with AsyncSessionLocal() as db:
        await calculator.calculate_daily_carbon_for_all_users(db, target_date)


def main():
    # Parse command line arguments
    if len(sys.argv) > 1:
        # Specific date provided
        try:
            target_date = date.fromisoformat(sys.argv[1])
            print(f"Calculating carbon for specific date: {target_date}")
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD")
            sys.exit(1)
    else:
        # Default to yesterday
        target_date = date.today() - timedelta(days=1)
        print(f"Calculating carbon for yesterday: {target_date}")
    
    asyncio.run(run_daily_calculation(target_date))


if __name__ == "__main__":
    main()