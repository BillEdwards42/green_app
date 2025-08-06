#!/usr/bin/env python3
"""
Carbon Daily Scheduler
Runs daily at 5:50PM to:
1. Calculate yesterday's carbon savings for all users
2. On the 1st of each month: check for promotions based on previous month's savings
"""

import asyncio
import sys
import os
import schedule
import time
import argparse
from datetime import date, datetime, timedelta
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.services.carbon_calculator_grams import DailyCarbonCalculator
from scripts.carbon_league_promotion import CarbonLeaguePromotion

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/carbon_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def run_daily_tasks():
    """Run daily carbon calculation and monthly promotion check if needed"""
    logger.info("=" * 60)
    logger.info("Starting daily carbon scheduler tasks")
    
    # Always calculate yesterday's carbon savings
    yesterday = date.today() - timedelta(days=1)
    logger.info(f"Calculating carbon savings for {yesterday}")
    
    calculator = DailyCarbonCalculator()
    async with AsyncSessionLocal() as db:
        try:
            await calculator.calculate_daily_carbon_for_all_users(db, yesterday)
            logger.info("✅ Daily carbon calculation completed")
        except Exception as e:
            logger.error(f"❌ Error in daily carbon calculation: {e}")
            raise
    
    # Check if today is the 1st of the month
    today = date.today()
    if today.day == 1:
        logger.info("First of the month - running promotion checks")
        
        promotion_service = CarbonLeaguePromotion()
        async with AsyncSessionLocal() as db:
            try:
                await promotion_service.check_and_promote_all_users(db, test_mode=False)
                logger.info("✅ Monthly promotion check completed")
            except Exception as e:
                logger.error(f"❌ Error in promotion check: {e}")
                raise
    else:
        logger.info(f"Not the 1st of month (day={today.day}) - skipping promotion check")
    
    logger.info("Daily scheduler tasks completed")
    logger.info("=" * 60)


def run_scheduled():
    """Run the scheduler with daily execution at 5:50PM"""
    logger.info("Carbon Daily Scheduler started")
    logger.info("Scheduled to run daily at 5:50 PM")
    
    # Schedule daily at 5:50 PM
    schedule.every().day.at("17:50").do(lambda: asyncio.run(run_daily_tasks()))
    
    # Run once immediately if requested
    if "--run-now" in sys.argv:
        logger.info("Running immediately as requested")
        asyncio.run(run_daily_tasks())
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(30)  # Check every 30 seconds


def main():
    parser = argparse.ArgumentParser(description='Carbon Daily Scheduler')
    parser.add_argument('--run-now', action='store_true', 
                        help='Run immediately in addition to scheduled time')
    parser.add_argument('--once', action='store_true',
                        help='Run once and exit (for testing)')
    args = parser.parse_args()
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    if args.once:
        logger.info("Running once and exiting")
        asyncio.run(run_daily_tasks())
    else:
        try:
            run_scheduled()
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            raise


if __name__ == "__main__":
    main()