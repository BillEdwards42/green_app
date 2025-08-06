#!/usr/bin/env python3
"""
Test promotion based on carbon threshold achievement
Can promote up based on thresholds or reset to bronze without data loss
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


# League progression and thresholds (in grams)
LEAGUE_THRESHOLDS = {
    'bronze': 30.0,     # Need 30g to reach silver
    'silver': 300.0,    # Need 300g to reach gold
    'gold': 500.0,      # Need 500g to reach emerald
    'emerald': 1000.0,  # Need 1000g to reach diamond
    'diamond': None     # Max level
}

LEAGUE_ORDER = ['bronze', 'silver', 'gold', 'emerald', 'diamond']


async def check_and_promote_based_on_threshold(username: str, reset_to_bronze: bool = False):
    """Check user's carbon and promote based on thresholds, or reset to bronze"""
    async with AsyncSessionLocal() as db:
        # Get user
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User '{username}' not found")
            return
            
        print(f"\n📊 User Status:")
        print(f"  - Username: {user.username}")
        print(f"  - Current League: {user.current_league}")
        print(f"  - Current Month Carbon: {user.current_month_carbon_saved:.1f}g CO2e")
        print(f"  - Total Carbon Saved: {user.total_carbon_saved:.1f}g CO2e")
        
        if reset_to_bronze:
            # Reset to bronze without clearing data
            print(f"\n🔄 Resetting to bronze league...")
            user.current_league = 'bronze'
            await db.commit()
            print(f"✅ Reset to bronze (carbon data preserved)")
            return
        
        # Check what league user should be in based on current month carbon
        current_carbon = user.current_month_carbon_saved
        current_league_index = LEAGUE_ORDER.index(user.current_league)
        
        # Find highest league user qualifies for
        qualified_league = 'bronze'
        for i, league in enumerate(LEAGUE_ORDER[:-1]):  # Skip diamond
            threshold = LEAGUE_THRESHOLDS[league]
            if current_carbon >= threshold:
                qualified_league = LEAGUE_ORDER[i + 1]
            else:
                break
                
        qualified_league_index = LEAGUE_ORDER.index(qualified_league)
        
        print(f"\n🎯 Threshold Analysis:")
        print(f"  - Current carbon: {current_carbon:.1f}g")
        print(f"  - Qualifies for: {qualified_league}")
        
        if qualified_league_index > current_league_index:
            # User qualifies for promotion
            print(f"\n🎉 PROMOTING from {user.current_league} to {qualified_league}!")
            
            old_league = user.current_league
            user.current_league = qualified_league
            
            # Create or update monthly summary with promotion flag
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
                    league_at_month_end=qualified_league,
                    league_upgraded=True  # This triggers the animation!
                )
                db.add(summary)
            else:
                summary.league_at_month_end = qualified_league
                summary.league_upgraded = True
                summary.total_carbon_saved = user.current_month_carbon_saved
            
            await db.commit()
            print(f"✅ Promotion complete! Close and reopen app to see animation.")
            
        elif qualified_league_index == current_league_index:
            print(f"\n✓ User is already in the correct league ({user.current_league})")
            
            # Show progress to next league
            if user.current_league != 'diamond':
                threshold = LEAGUE_THRESHOLDS[user.current_league]
                progress = (current_carbon / threshold * 100) if threshold else 100
                remaining = threshold - current_carbon if threshold else 0
                print(f"  - Progress to next league: {progress:.1f}%")
                print(f"  - Need {remaining:.1f}g more to reach {LEAGUE_ORDER[current_league_index + 1]}")
                
        else:
            print(f"\n⚠️  User is in a higher league than qualified")
            print(f"   (This is normal - leagues don't demote)")


async def show_all_thresholds():
    """Display all league thresholds"""
    print("\n🏆 League Promotion Thresholds:")
    print("  Bronze → Silver: 30g CO2e")
    print("  Silver → Gold: 300g CO2e")
    print("  Gold → Emerald: 500g CO2e")
    print("  Emerald → Diamond: 1,000g CO2e")
    print("  Diamond: MAX (no further promotion)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_threshold_promotion.py <username> [--reset-to-bronze]")
        print("Example: python test_threshold_promotion.py edwards_test1")
        print("         python test_threshold_promotion.py edwards_test1 --reset-to-bronze")
        asyncio.run(show_all_thresholds())
        sys.exit(1)
        
    username = sys.argv[1]
    reset = len(sys.argv) > 2 and sys.argv[2] == '--reset-to-bronze'
    
    asyncio.run(check_and_promote_based_on_threshold(username, reset))