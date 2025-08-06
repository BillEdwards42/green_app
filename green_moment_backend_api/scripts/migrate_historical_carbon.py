#!/usr/bin/env python3
"""
Historical Carbon (CO2e) Migration Script
Processes all historical chores and populates daily_carbon_progress table
"""

import asyncio
import sys
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple
from sqlalchemy import select, and_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.chore import Chore
from app.models.daily_carbon_progress import DailyCarbonProgress
from app.models.monthly_summary import MonthlySummary
from app.services.carbon_calculator import DailyCarbonCalculator


class HistoricalCarbonMigration:
    """Migrate all historical chores to carbon-based system"""
    
    def __init__(self):
        self.calculator = DailyCarbonCalculator()
        self.stats = {
            'users_processed': 0,
            'chores_processed': 0,
            'days_calculated': 0,
            'errors': 0
        }
    
    async def migrate_all_users(self, db: AsyncSession):
        """Process all users' historical data"""
        print("\n🌱 Starting Historical Carbon (CO2e) Migration")
        print("=" * 60)
        
        # Get all users (including soft-deleted for data integrity)
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        print(f"Found {len(users)} users to process\n")
        
        for user in users:
            try:
                await self.migrate_user_carbon(db, user)
                self.stats['users_processed'] += 1
            except Exception as e:
                print(f"❌ Error processing user {user.username}: {e}")
                self.stats['errors'] += 1
                continue
        
        await db.commit()
        self._print_summary()
    
    async def migrate_user_carbon(self, db: AsyncSession, user: User):
        """Migrate carbon (CO2e) data for a single user"""
        print(f"\n👤 Processing user: {user.username}")
        
        # Get all chores for this user
        result = await db.execute(
            select(Chore)
            .where(Chore.user_id == user.id)
            .order_by(Chore.start_time)
        )
        chores = result.scalars().all()
        
        if not chores:
            print(f"   No chores found")
            return
        
        print(f"   Found {len(chores)} chores")
        
        # Group chores by date
        chores_by_date: Dict[date, List[Chore]] = {}
        for chore in chores:
            chore_date = chore.start_time.date()
            if chore_date not in chores_by_date:
                chores_by_date[chore_date] = []
            chores_by_date[chore_date].append(chore)
        
        # Clear existing daily progress for this user (for re-runs)
        await db.execute(
            delete(DailyCarbonProgress).where(DailyCarbonProgress.user_id == user.id)
        )
        
        # Process each day
        total_carbon_saved = 0.0
        month_data: Dict[Tuple[int, int], float] = {}  # (year, month) -> total
        
        for chore_date in sorted(chores_by_date.keys()):
            daily_carbon = 0.0
            
            # Calculate carbon for each chore on this date
            for chore in chores_by_date[chore_date]:
                carbon_saved = self.calculator._calculate_chore_carbon_saved(chore)
                daily_carbon += carbon_saved
                self.stats['chores_processed'] += 1
            
            # Determine cumulative total based on month
            month_key = (chore_date.year, chore_date.month)
            
            if chore_date.day == 1:
                # First day of month - reset cumulative
                cumulative_total = daily_carbon
            else:
                # Find the cumulative total for this month so far
                # Look for the most recent entry in the same month
                result = await db.execute(
                    select(DailyCarbonProgress)
                    .where(
                        and_(
                            DailyCarbonProgress.user_id == user.id,
                            func.extract('year', DailyCarbonProgress.date) == chore_date.year,
                            func.extract('month', DailyCarbonProgress.date) == chore_date.month,
                            DailyCarbonProgress.date < chore_date
                        )
                    )
                    .order_by(DailyCarbonProgress.date.desc())
                    .limit(1)
                )
                previous_progress = result.scalar_one_or_none()
                
                if previous_progress:
                    # Add to previous cumulative in same month
                    cumulative_total = previous_progress.cumulative_carbon_saved + daily_carbon
                else:
                    # First entry of the month
                    cumulative_total = daily_carbon
            
            # Create daily progress entry
            progress = DailyCarbonProgress(
                user_id=user.id,
                date=chore_date,
                daily_carbon_saved=daily_carbon,
                cumulative_carbon_saved=cumulative_total
            )
            db.add(progress)
            
            # Track monthly totals
            month_key = (chore_date.year, chore_date.month)
            month_data[month_key] = cumulative_total  # Will be overwritten with latest
            
            total_carbon_saved += daily_carbon
            self.stats['days_calculated'] += 1
        
        # Update user's total carbon saved
        user.total_carbon_saved = total_carbon_saved
        
        # Update current month carbon if applicable
        current_month = date.today().month
        current_year = date.today().year
        if (current_year, current_month) in month_data:
            user.current_month_carbon_saved = month_data[(current_year, current_month)]
        
        print(f"   ✅ Calculated {len(chores_by_date)} days")
        print(f"   💚 Total carbon (CO2e) saved: {total_carbon_saved:.3f} kg")
        
        # Create historical monthly summaries
        await self._create_monthly_summaries(db, user, month_data)
    
    async def _create_monthly_summaries(
        self, 
        db: AsyncSession, 
        user: User, 
        month_data: Dict[Tuple[int, int], float]
    ):
        """Create monthly summaries for historical data"""
        # League thresholds for determining historical leagues
        thresholds = {
            "bronze": 0.1,
            "silver": 0.5,
            "gold": 0.7,
            "emerald": 1.0,
        }
        
        previous_league = "bronze"
        
        for (year, month), carbon_saved in sorted(month_data.items()):
            # Skip current month (will be handled by monthly promotion script)
            if year == date.today().year and month == date.today().month:
                continue
            
            # Determine league at month end based on carbon (CO2e) saved
            league_at_end = "bronze"
            for league, threshold in thresholds.items():
                if carbon_saved >= threshold:
                    league_at_end = league
            
            # Check if league was upgraded
            league_upgraded = league_at_end != previous_league
            
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
            
            if existing_summary:
                # Update existing summary
                existing_summary.total_carbon_saved = carbon_saved
                existing_summary.league_at_month_start = previous_league
                existing_summary.league_at_month_end = league_at_end
                existing_summary.league_upgraded = league_upgraded
                existing_summary.tasks_completed = 0  # No longer used
                existing_summary.total_points_earned = 0  # No longer used
            else:
                # Create new summary
                summary = MonthlySummary(
                    user_id=user.id,
                    month=month,
                    year=year,
                    total_carbon_saved=carbon_saved,
                    league_at_month_start=previous_league,
                    league_at_month_end=league_at_end,
                    league_upgraded=league_upgraded,
                    total_chores_logged=0,  # Will be calculated separately if needed
                    total_hours_shifted=0,
                    tasks_completed=0,
                    total_points_earned=0
                )
                db.add(summary)
            
            previous_league = league_at_end
        
        # Update user's current league based on best month's CO2e
        best_league = "bronze"
        for (year, month), carbon_saved in month_data.items():
            for league, threshold in thresholds.items():
                if carbon_saved >= threshold and self._is_higher_league(league, best_league):
                    best_league = league
        
        user.current_league = best_league
        print(f"   🏆 User league set to: {best_league}")
    
    def _is_higher_league(self, league1: str, league2: str) -> bool:
        """Check if league1 is higher than league2"""
        league_order = ["bronze", "silver", "gold", "emerald", "diamond"]
        return league_order.index(league1) > league_order.index(league2)
    
    def _print_summary(self):
        """Print migration summary"""
        print("\n" + "=" * 60)
        print("🎉 Migration Complete!")
        print(f"👥 Users processed: {self.stats['users_processed']}")
        print(f"📝 Chores processed: {self.stats['chores_processed']}")
        print(f"📅 Days calculated: {self.stats['days_calculated']}")
        print(f"❌ Errors: {self.stats['errors']}")


async def main():
    """Run the historical migration"""
    migration = HistoricalCarbonMigration()
    
    async with AsyncSessionLocal() as db:
        await migration.migrate_all_users(db)


if __name__ == "__main__":
    print("⚠️  This will recalculate ALL historical carbon data.")
    print("⚠️  Existing daily_carbon_progress entries will be replaced.")
    response = input("\nContinue? (yes/no): ")
    
    if response.lower() == 'yes':
        asyncio.run(main())
    else:
        print("Migration cancelled.")