#!/usr/bin/env python3
"""
Carbon-based promotion script
Promotes users based on last month's carbon savings, not task completion
"""

import asyncio
import sys
import os
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from sqlalchemy import select, and_, func

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.monthly_summary import MonthlySummary
from app.models.daily_carbon_progress import DailyCarbonProgress


class CarbonBasedPromotion:
    def __init__(self):
        # Carbon thresholds for promotion (in grams CO2e)
        self.promotion_thresholds = {
            "bronze": 30,      # 30g to reach Silver
            "silver": 300,     # 300g to reach Gold
            "gold": 500,       # 500g to reach Emerald
            "emerald": 1000,   # 1kg to reach Diamond
            "diamond": None    # Max level
        }
        
        self.league_progression = {
            "bronze": "silver",
            "silver": "gold",
            "gold": "emerald",
            "emerald": "diamond",
            "diamond": "diamond"
        }
    
    async def check_and_promote_user(self, username: str):
        """Check if user should be promoted based on carbon savings"""
        async with AsyncSessionLocal() as db:
            # Get user
            result = await db.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ User '{username}' not found!")
                return
            
            print(f"\n👤 User: {user.username}")
            print(f"📊 Current League: {user.current_league}")
            print(f"🌱 Total Lifetime Carbon: {user.total_carbon_saved:.2f} g")
            
            # Get last month's dates
            today = date.today()
            last_month_end = date(today.year, today.month, 1) - relativedelta(days=1)
            last_month_start = date(last_month_end.year, last_month_end.month, 1)
            
            print(f"\n📆 Checking period: {last_month_start} to {last_month_end}")
            
            # Calculate last month's carbon from daily progress
            result = await db.execute(
                select(func.sum(DailyCarbonProgress.daily_carbon_saved)).where(
                    and_(
                        DailyCarbonProgress.user_id == user.id,
                        DailyCarbonProgress.date >= last_month_start,
                        DailyCarbonProgress.date <= last_month_end
                    )
                )
            )
            last_month_carbon = result.scalar() or 0
            
            print(f"🌿 Last Month Carbon Saved: {last_month_carbon:.2f} g")
            
            # Check promotion eligibility
            old_league = user.current_league
            promoted = False
            
            if user.current_league == "diamond":
                print(f"\n💎 Already at maximum league (Diamond)")
            else:
                threshold = self.promotion_thresholds[user.current_league]
                print(f"🎯 Promotion Threshold: {threshold:,} g")
                
                if last_month_carbon >= threshold:
                    # Promote!
                    new_league = self.league_progression[user.current_league]
                    user.current_league = new_league
                    promoted = True
                    print(f"\n🎉 PROMOTED to {new_league} league!")
                else:
                    deficit = threshold - last_month_carbon
                    print(f"\n📌 Not eligible for promotion")
                    print(f"   Need {deficit:,.0f} more grams ({deficit/1000:.1f} kg)")
            
            # Update or create monthly summary
            result = await db.execute(
                select(MonthlySummary).where(
                    and_(
                        MonthlySummary.user_id == user.id,
                        MonthlySummary.month == last_month_end.month,
                        MonthlySummary.year == last_month_end.year
                    )
                )
            )
            summary = result.scalar_one_or_none()
            
            if not summary:
                summary = MonthlySummary(
                    user_id=user.id,
                    month=last_month_end.month,
                    year=last_month_end.year,
                    total_carbon_saved=last_month_carbon,
                    league_at_month_start=old_league,
                    league_at_month_end=user.current_league,
                    league_upgraded=promoted
                )
                db.add(summary)
                print(f"\n📝 Created monthly summary for {last_month_end.strftime('%B %Y')}")
            else:
                summary.total_carbon_saved = last_month_carbon
                summary.league_at_month_end = user.current_league
                summary.league_upgraded = promoted
                print(f"\n📝 Updated monthly summary for {last_month_end.strftime('%B %Y')}")
            
            # Reset monthly counter for new month
            if today.month != last_month_end.month:
                user.current_month_carbon_saved = 0
                print(f"🔄 Reset current month carbon counter")
            
            # Commit changes
            await db.commit()
            
            print(f"\n✅ Process complete!")
            print(f"📊 Final League: {user.current_league}")
            
            return {
                "promoted": promoted,
                "old_league": old_league,
                "new_league": user.current_league,
                "last_month_carbon": last_month_carbon,
                "threshold": self.promotion_thresholds.get(old_league, 0)
            }


async def main():
    if len(sys.argv) < 2:
        print("Usage: python carbon_based_promotion.py <username>")
        print("Example: python carbon_based_promotion.py edwards_test1")
        sys.exit(1)
    
    username = sys.argv[1]
    promoter = CarbonBasedPromotion()
    
    print(f"🔄 Checking carbon-based promotion for: {username}")
    result = await promoter.check_and_promote_user(username)
    
    if result:
        print("\n" + "="*50)
        print("📊 Summary:")
        print(f"  Promoted: {'Yes' if result['promoted'] else 'No'}")
        print(f"  League: {result['old_league']} → {result['new_league']}")
        print(f"  Last Month Carbon: {result['last_month_carbon']:,.0f} g")
        if result['threshold']:
            print(f"  Threshold: {result['threshold']:,} g")
        print("="*50)


if __name__ == "__main__":
    asyncio.run(main())