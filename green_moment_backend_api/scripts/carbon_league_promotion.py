#!/usr/bin/env python3
"""
Carbon-based League Promotion System
Promotes users based on monthly carbon (CO2e) savings thresholds
"""

import asyncio
import sys
import os
from datetime import datetime, date, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.monthly_summary import MonthlySummary


class CarbonLeaguePromotion:
    """Service for carbon-based league promotions"""
    
    def __init__(self):
        # Carbon (CO2e) thresholds in grams for promotion
        self.promotion_thresholds = {
            "bronze": 100,    # 100g to advance to silver
            "silver": 500,    # 500g to advance to gold  
            "gold": 700,      # 700g to advance to emerald
            "emerald": 1000,  # 1000g to advance to diamond
            "diamond": float('inf'),  # No promotion from diamond
        }
        
        self.league_progression = {
            "bronze": "silver",
            "silver": "gold",
            "gold": "emerald",
            "emerald": "diamond",
            "diamond": "diamond",
        }
    
    async def check_and_promote_all_users(self, db: AsyncSession, test_mode: bool = False):
        """Check all users for promotion based on carbon savings"""
        # Determine which month to check
        if test_mode or datetime.now().day > 1:
            # Test mode or not the first of month - check current month
            check_month = datetime.now().month
            check_year = datetime.now().year
        else:
            # First of month - check previous month
            last_month = datetime.now() - timedelta(days=1)
            check_month = last_month.month
            check_year = last_month.year
        
        print(f"\n🌟 League Promotion Check - {check_month}/{check_year}")
        print("=" * 50)
        
        # Get all active users
        result = await db.execute(
            select(User).where(User.deleted_at.is_(None))
        )
        users = result.scalars().all()
        
        promoted_count = 0
        
        for user in users:
            promoted = await self.check_and_promote_user(
                db, user, check_month, check_year
            )
            if promoted:
                promoted_count += 1
        
        await db.commit()
        
        print(f"\n✅ Promotion check completed")
        print(f"📊 Total users: {len(users)}")
        print(f"⬆️  Promoted: {promoted_count}")
    
    async def check_and_promote_user(
        self, 
        db: AsyncSession, 
        user: User, 
        month: int, 
        year: int
    ) -> bool:
        """Check if a user qualifies for promotion"""
        current_league = user.current_league
        threshold = self.promotion_thresholds.get(current_league, float('inf'))
        
        # Get user's carbon (CO2e) savings for the month
        if month == datetime.now().month and year == datetime.now().year:
            # Current month - use the field
            carbon_saved = user.current_month_carbon_saved
        else:
            # Previous month - check monthly summary
            result = await db.execute(
                select(MonthlySummary).where(
                    and_(
                        MonthlySummary.user_id == user.id,
                        MonthlySummary.month == month,
                        MonthlySummary.year == year
                    )
                )
            )
            summary = result.scalar_one_or_none()
            carbon_saved = summary.total_carbon_saved if summary else 0
        
        print(f"\n👤 {user.username}")
        print(f"   League: {current_league}")
        print(f"   Carbon (CO2e) saved: {carbon_saved:.0f}g")
        print(f"   Threshold: {threshold:.0f}g")
        
        # Check if eligible for promotion
        if carbon_saved >= threshold and current_league != "diamond":
            new_league = self.league_progression[current_league]
            user.current_league = new_league
            
            # Create or update monthly summary
            await self._update_monthly_summary(
                db, user, month, year, carbon_saved, 
                league_upgraded=True, 
                old_league=current_league,
                new_league=new_league
            )
            
            print(f"   ✅ PROMOTED to {new_league}!")
            return True
        else:
            # Not promoted, but still update summary
            await self._update_monthly_summary(
                db, user, month, year, carbon_saved, 
                league_upgraded=False,
                old_league=current_league,
                new_league=current_league
            )
            
            if current_league == "diamond":
                print(f"   💎 Already at maximum league")
            else:
                needed = threshold - carbon_saved
                print(f"   ❌ Not promoted (need {needed:.0f}g more)")
            return False
    
    async def _update_monthly_summary(
        self, 
        db: AsyncSession, 
        user: User,
        month: int,
        year: int,
        carbon_saved: float,
        league_upgraded: bool,
        old_league: str,
        new_league: str
    ):
        """Create or update monthly summary"""
        result = await db.execute(
            select(MonthlySummary).where(
                and_(
                    MonthlySummary.user_id == user.id,
                    MonthlySummary.month == month,
                    MonthlySummary.year == year
                )
            )
        )
        summary = result.scalar_one_or_none()
        
        if not summary:
            summary = MonthlySummary(
                user_id=user.id,
                month=month,
                year=year,
                total_carbon_saved=carbon_saved,
                league_at_month_start=old_league,
                league_at_month_end=new_league,
                league_upgraded=league_upgraded,
                total_chores_logged=0,  # Will be calculated separately
                total_hours_shifted=0,
                tasks_completed=0,  # No longer used
                total_points_earned=0  # No longer used
            )
            db.add(summary)
        else:
            summary.total_carbon_saved = carbon_saved
            summary.league_at_month_end = new_league
            summary.league_upgraded = league_upgraded
    
    async def reset_monthly_carbon(self, db: AsyncSession):
        """Reset monthly carbon (CO2e) counters for all users"""
        print("\n🔄 Resetting monthly carbon (CO2e) counters...")
        
        result = await db.execute(
            select(User).where(User.deleted_at.is_(None))
        )
        users = result.scalars().all()
        
        for user in users:
            user.current_month_carbon_saved = 0.0
        
        await db.commit()
        print(f"✅ Reset carbon (CO2e) counters for {len(users)} users")


async def main():
    """Run the carbon-based promotion check"""
    promotion_service = CarbonLeaguePromotion()
    
    # Check for test mode
    test_mode = "--test" in sys.argv
    
    async with AsyncSessionLocal() as db:
        await promotion_service.check_and_promote_all_users(db, test_mode)
        
        # If it's the first of the month and not test mode, reset counters
        if datetime.now().day == 1 and not test_mode:
            await promotion_service.reset_monthly_carbon(db)


if __name__ == "__main__":
    asyncio.run(main())