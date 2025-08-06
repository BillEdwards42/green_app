#!/usr/bin/env python3
"""
Carbon Daily Scheduler
Runs daily at 12:00AM (midnight) to:
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

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.services.carbon_calculator_grams import DailyCarbonCalculator
from scripts.carbon_league_promotion import CarbonLeaguePromotion
from app.models.user import User
from app.models.monthly_summary import MonthlySummary

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


async def create_monthly_summaries_for_all_users(db: AsyncSession, last_day_of_month: date):
    """Create monthly summaries for all users for the previous month"""
    month = last_day_of_month.month
    year = last_day_of_month.year
    
    logger.info(f"Creating monthly summaries for {month}/{year}")
    
    # Get all active users
    result = await db.execute(
        select(User).where(User.deleted_at.is_(None))
    )
    users = result.scalars().all()
    
    for user in users:
        # Check if summary already exists
        result = await db.execute(
            select(MonthlySummary).where(
                and_(
                    MonthlySummary.user_id == user.id,
                    MonthlySummary.month == month,
                    MonthlySummary.year == year
                )
            )
        )
        existing_summary = result.scalar_one_or_none()
        
        if not existing_summary:
            # Get the final carbon saved for the month
            # Since this runs on the 1st, yesterday was the last day of the previous month
            # The user's current_month_carbon_saved still has the previous month's total
            carbon_saved = user.current_month_carbon_saved
            
            # Create new summary
            summary = MonthlySummary(
                user_id=user.id,
                month=month,
                year=year,
                total_carbon_saved=carbon_saved,
                league_at_month_start=user.current_league,  # Will be updated by promotion
                league_at_month_end=user.current_league,    # Will be updated by promotion
                league_upgraded=False,  # Will be updated by promotion
                total_chores_logged=0,  # Would need separate calculation
                total_hours_shifted=0,  # Would need separate calculation
                tasks_completed=0,
                total_points_earned=0
            )
            db.add(summary)
            logger.info(f"Created monthly summary for {user.username}: {carbon_saved:.1f}g CO2e")
        else:
            # Update existing summary with final carbon value
            existing_summary.total_carbon_saved = user.current_month_carbon_saved
            logger.info(f"Updated monthly summary for {user.username}: {user.current_month_carbon_saved:.1f}g CO2e")
    
    await db.commit()
    logger.info("Monthly summaries creation completed")


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
        logger.info("First of the month - handling month transition")
        
        # Create monthly summaries for the previous month
        async with AsyncSessionLocal() as db:
            try:
                await create_monthly_summaries_for_all_users(db, yesterday)
                logger.info("✅ Monthly summaries created for previous month")
            except Exception as e:
                logger.error(f"❌ Error creating monthly summaries: {e}")
                raise
        
        # Run promotion checks
        logger.info("Running promotion checks")
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
    """Run the scheduler with daily execution at midnight"""
    logger.info("Carbon Daily Scheduler started")
    logger.info("Scheduled to run daily at 12:00 AM (midnight)")
    
    # Schedule daily at midnight
    schedule.every().day.at("00:00").do(lambda: asyncio.run(run_daily_tasks()))
    
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