#!/usr/bin/env python3
"""
Test promotion simulation script
Simulates promotion without actually changing the database
Shows what would happen if we promoted based on current month data
"""

import asyncio
import sys
import os
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.monthly_summary import MonthlySummary
from app.models.daily_carbon_progress import DailyCarbonProgress


class PromotionSimulator:
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
    
    async def simulate_promotion(self, username: str, use_current_month: bool = False):
        """Simulate promotion without changing the database"""
        async with AsyncSessionLocal() as db:
            # Get user
            result = await db.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ User '{username}' not found!")
                return
            
            # Store original values
            original_league = user.current_league
            original_total_carbon = user.total_carbon_saved
            original_month_carbon = user.current_month_carbon_saved
            
            print(f"\n{'='*60}")
            print(f"🧪 PROMOTION SIMULATION for {user.username}")
            print(f"{'='*60}")
            
            print(f"\n📊 Current State:")
            print(f"  League: {original_league}")
            print(f"  Total Lifetime Carbon: {original_total_carbon:.2f} g")
            print(f"  Current Month Carbon: {original_month_carbon:.2f} g")
            
            # Determine which month to check
            if use_current_month:
                # For testing: use current month data
                check_month = date.today()
                carbon_amount = original_month_carbon
                print(f"\n⚠️  TESTING MODE: Using current month (August) data")
                print(f"📅 Checking: {check_month.strftime('%B %Y')}")
                print(f"🌿 Carbon Saved: {carbon_amount:.2f} g")
            else:
                # Normal: use last completed month
                today = date.today()
                last_month_end = date(today.year, today.month, 1) - relativedelta(days=1)
                last_month_start = date(last_month_end.year, last_month_end.month, 1)
                
                # Calculate last month's carbon
                result = await db.execute(
                    select(func.sum(DailyCarbonProgress.daily_carbon_saved)).where(
                        and_(
                            DailyCarbonProgress.user_id == user.id,
                            DailyCarbonProgress.date >= last_month_start,
                            DailyCarbonProgress.date <= last_month_end
                        )
                    )
                )
                carbon_amount = result.scalar() or 0
                check_month = last_month_end
                print(f"\n📅 Checking: {check_month.strftime('%B %Y')}")
                print(f"🌿 Carbon Saved: {carbon_amount:.2f} g")
            
            # Check promotion eligibility
            print(f"\n🎯 Promotion Analysis:")
            
            if user.current_league == "diamond":
                print(f"  💎 Already at maximum league (Diamond)")
                promoted = False
                new_league = "diamond"
            else:
                threshold = self.promotion_thresholds[user.current_league]
                print(f"  Threshold for {self.league_progression[user.current_league]}: {threshold:,} g")
                
                if carbon_amount >= threshold:
                    new_league = self.league_progression[user.current_league]
                    promoted = True
                    print(f"  ✅ ELIGIBLE for promotion to {new_league}!")
                    print(f"     {carbon_amount:.0f} >= {threshold} ✓")
                else:
                    deficit = threshold - carbon_amount
                    promoted = False
                    new_league = user.current_league
                    print(f"  ❌ NOT ELIGIBLE for promotion")
                    print(f"     {carbon_amount:.0f} < {threshold}")
                    print(f"     Need {deficit:,.0f} more grams ({deficit/1000:.1f} kg)")
            
            # Show what would happen
            print(f"\n📋 What Would Happen:")
            if promoted:
                print(f"  1. League: {original_league} → {new_league} 🎉")
                print(f"  2. Monthly Summary would be created/updated:")
                print(f"     - Month: {check_month.strftime('%B %Y')}")
                print(f"     - Carbon Saved: {carbon_amount:.2f} g")
                print(f"     - League Start: {original_league}")
                print(f"     - League End: {new_league}")
                print(f"     - Promoted: Yes")
                if not use_current_month:
                    print(f"  3. Current month carbon would reset to 0")
            else:
                print(f"  1. League remains: {original_league}")
                print(f"  2. No changes to database")
            
            # Rollback any changes (just in case)
            await db.rollback()
            
            print(f"\n✅ Simulation complete - NO CHANGES MADE TO DATABASE")
            
            return {
                "user": username,
                "current_league": original_league,
                "would_promote": promoted,
                "new_league": new_league if promoted else original_league,
                "carbon_checked": carbon_amount,
                "threshold": self.promotion_thresholds.get(original_league, 0),
                "testing_mode": use_current_month
            }


async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_promotion_simulation.py <username> [--use-current-month]")
        print("\nOptions:")
        print("  --use-current-month  Use current month data for testing (default: use last month)")
        print("\nExamples:")
        print("  python test_promotion_simulation.py edwards_test1")
        print("  python test_promotion_simulation.py edwards_test1 --use-current-month")
        sys.exit(1)
    
    username = sys.argv[1]
    use_current = "--use-current-month" in sys.argv
    
    simulator = PromotionSimulator()
    result = await simulator.simulate_promotion(username, use_current)
    
    if result:
        print("\n" + "="*60)
        print("📊 SIMULATION SUMMARY")
        print("="*60)
        print(f"User: {result['user']}")
        print(f"Current League: {result['current_league']}")
        print(f"Carbon Amount: {result['carbon_checked']:,.0f} g")
        print(f"Threshold: {result['threshold']:,} g")
        print(f"Would Promote: {'YES' if result['would_promote'] else 'NO'}")
        if result['would_promote']:
            print(f"New League: {result['new_league']}")
        if result['testing_mode']:
            print(f"\n⚠️  This was a TEST using current month data")
            print(f"   In production, promotion uses completed month data")


if __name__ == "__main__":
    asyncio.run(main())