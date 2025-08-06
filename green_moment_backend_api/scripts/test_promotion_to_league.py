#!/usr/bin/env python3
"""
Test promotion to a specific league
"""
import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, and_
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.monthly_summary import MonthlySummary


# League progression and thresholds
LEAGUE_PROGRESSION = {
    'bronze': {'next': 'silver', 'threshold': 30.0},
    'silver': {'next': 'gold', 'threshold': 300.0},
    'gold': {'next': 'emerald', 'threshold': 500.0},
    'emerald': {'next': 'diamond', 'threshold': 1000.0},
    'diamond': {'next': None, 'threshold': None}
}


async def promote_to_league(username: str, target_league: str):
    """Promote user to specific league for testing"""
    async with AsyncSessionLocal() as db:
        # Get user
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User '{username}' not found")
            return
            
        if target_league not in LEAGUE_PROGRESSION:
            print(f"❌ Invalid league: {target_league}")
            print(f"   Valid leagues: bronze, silver, gold, emerald, diamond")
            return
            
        print(f"\n📊 Current State:")
        print(f"  - Username: {user.username}")
        print(f"  - Current League: {user.current_league}")
        
        if user.current_league == target_league:
            print(f"⚠️  User is already in {target_league} league!")
            return
            
        # Update user league
        old_league = user.current_league
        user.current_league = target_league
        
        # DO NOT modify carbon values - keep the actual data!
        # This is just a test promotion
        
        # Create or update current month summary with promotion flag
        result = await db.execute(
            select(MonthlySummary).where(
                and_(
                    MonthlySummary.user_id == user.id,
                    MonthlySummary.month == datetime.now().month,
                    MonthlySummary.year == datetime.now().year
                )
            )
        )
        summary = result.scalar_one_or_none()
        
        if not summary:
            summary = MonthlySummary(
                user_id=user.id,
                month=datetime.now().month,
                year=datetime.now().year,
                total_carbon_saved=user.current_month_carbon_saved,
                total_chores_logged=0,
                total_hours_shifted=0.0,
                tasks_completed=0,
                total_points_earned=0,
                league_at_month_start=old_league,
                league_at_month_end=target_league,
                league_upgraded=True  # This triggers the animation!
            )
            db.add(summary)
        else:
            summary.league_at_month_end = target_league
            summary.league_upgraded = True
            # Keep the existing carbon value, don't modify it
        
        await db.commit()
        
        print(f"\n🎉 PROMOTED to {target_league} league!")
        print(f"  - From: {old_league}")
        print(f"  - To: {target_league}")
        print(f"  - Animation flag: Set to True")
        print(f"\n📱 Now close and reopen the app to see the animation!")


async def list_leagues():
    """List all available leagues and their thresholds"""
    print("\n🏆 League Progression:")
    print("  bronze → silver: 30g CO2e")
    print("  silver → gold: 300g CO2e")
    print("  gold → emerald: 500g CO2e")
    print("  emerald → diamond: 1000g CO2e")
    print("  diamond: MAX (no further promotion)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test_promotion_to_league.py <username> <target_league>")
        print("Example: python test_promotion_to_league.py edwards_test1 silver")
        asyncio.run(list_leagues())
        sys.exit(1)
        
    username = sys.argv[1]
    target_league = sys.argv[2].lower()
    asyncio.run(promote_to_league(username, target_league))