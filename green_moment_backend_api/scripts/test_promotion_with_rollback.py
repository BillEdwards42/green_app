#!/usr/bin/env python3
"""
Test promotion with rollback capability
Actually promotes the user but saves state for easy reversion
"""

import asyncio
import sys
import os
import json
from datetime import datetime, date
from pathlib import Path
from sqlalchemy import select, and_

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.monthly_summary import MonthlySummary


class PromotionTester:
    def __init__(self):
        self.backup_file = Path("test_promotion_backup.json")
        self.league_progression = {
            "bronze": "silver",
            "silver": "gold",
            "gold": "emerald",
            "emerald": "diamond",
            "diamond": "diamond"
        }
        self.promotion_thresholds = {
            "bronze": 30,      # 30g to reach Silver
            "silver": 300,     # 300g to reach Gold
            "gold": 500,       # 500g to reach Emerald
            "emerald": 1000,   # 1kg to reach Diamond
            "diamond": None    # Max level
        }
    
    async def backup_user_state(self, username: str):
        """Backup user state before promotion"""
        async with AsyncSessionLocal() as db:
            # Get user
            result = await db.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ User '{username}' not found!")
                return False
            
            # Save current state
            backup_data = {
                "username": username,
                "user_id": user.id,
                "original_league": user.current_league,
                "original_total_carbon": float(user.total_carbon_saved),
                "original_month_carbon": float(user.current_month_carbon_saved),
                "backup_time": datetime.now().isoformat()
            }
            
            # Check if there's an existing monthly summary
            current_month = date.today().month
            current_year = date.today().year
            
            result = await db.execute(
                select(MonthlySummary).where(
                    and_(
                        MonthlySummary.user_id == user.id,
                        MonthlySummary.month == current_month,
                        MonthlySummary.year == current_year
                    )
                )
            )
            summary = result.scalar_one_or_none()
            
            if summary:
                backup_data["had_monthly_summary"] = True
                backup_data["summary_id"] = summary.id
                backup_data["summary_carbon"] = float(summary.total_carbon_saved)
                backup_data["summary_league_start"] = summary.league_at_month_start
                backup_data["summary_league_end"] = summary.league_at_month_end
                backup_data["summary_upgraded"] = summary.league_upgraded
            else:
                backup_data["had_monthly_summary"] = False
            
            # Write backup
            with open(self.backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            print(f"✅ Backed up state to {self.backup_file}")
            return True
    
    async def test_promote_user(self, username: str):
        """Test promote user based on current month carbon"""
        # First, backup the state
        if not await self.backup_user_state(username):
            return
        
        async with AsyncSessionLocal() as db:
            # Get user
            result = await db.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return
            
            print(f"\n🧪 TEST PROMOTION for {user.username}")
            print(f"📊 Current State:")
            print(f"  League: {user.current_league}")
            print(f"  Current Month Carbon: {user.current_month_carbon_saved:.2f} g")
            
            # Check if eligible based on current month
            old_league = user.current_league
            if old_league == "diamond":
                print(f"💎 Already at maximum league")
                return
            
            threshold = self.promotion_thresholds[old_league]
            print(f"🎯 Threshold for {self.league_progression[old_league]}: {threshold:,} g")
            
            if user.current_month_carbon_saved >= threshold:
                # Promote!
                new_league = self.league_progression[old_league]
                user.current_league = new_league
                
                # Create/update monthly summary
                current_month = date.today().month
                current_year = date.today().year
                
                result = await db.execute(
                    select(MonthlySummary).where(
                        and_(
                            MonthlySummary.user_id == user.id,
                            MonthlySummary.month == current_month,
                            MonthlySummary.year == current_year
                        )
                    )
                )
                summary = result.scalar_one_or_none()
                
                if not summary:
                    summary = MonthlySummary(
                        user_id=user.id,
                        month=current_month,
                        year=current_year,
                        total_carbon_saved=user.current_month_carbon_saved,
                        league_at_month_start=old_league,
                        league_at_month_end=new_league,
                        league_upgraded=True
                    )
                    db.add(summary)
                else:
                    summary.total_carbon_saved = user.current_month_carbon_saved
                    summary.league_at_month_end = new_league
                    summary.league_upgraded = True
                
                await db.commit()
                
                print(f"\n🎉 PROMOTED to {new_league} league!")
                print(f"✅ Changes committed to database")
                print(f"\n⚠️  To revert: python test_promotion_with_rollback.py --rollback")
            else:
                deficit = threshold - user.current_month_carbon_saved
                print(f"\n❌ Not eligible for promotion")
                print(f"   Need {deficit:,.0f} more grams")
    
    async def rollback_promotion(self):
        """Rollback the test promotion"""
        if not self.backup_file.exists():
            print("❌ No backup file found. Nothing to rollback.")
            return
        
        # Load backup
        with open(self.backup_file, 'r') as f:
            backup = json.load(f)
        
        print(f"\n🔄 Rolling back promotion for {backup['username']}")
        print(f"📅 Backup from: {backup['backup_time']}")
        
        async with AsyncSessionLocal() as db:
            # Get user
            result = await db.execute(
                select(User).where(User.username == backup['username'])
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ User not found!")
                return
            
            # Show current state
            print(f"\n📊 Current State:")
            print(f"  League: {user.current_league}")
            
            # Restore user state
            user.current_league = backup['original_league']
            
            # Handle monthly summary
            if backup.get('had_monthly_summary'):
                # Restore existing summary
                result = await db.execute(
                    select(MonthlySummary).where(
                        MonthlySummary.id == backup['summary_id']
                    )
                )
                summary = result.scalar_one_or_none()
                
                if summary:
                    summary.total_carbon_saved = backup['summary_carbon']
                    summary.league_at_month_start = backup['summary_league_start']
                    summary.league_at_month_end = backup['summary_league_end']
                    summary.league_upgraded = backup['summary_upgraded']
            else:
                # Delete any summary created during test
                current_month = date.today().month
                current_year = date.today().year
                
                result = await db.execute(
                    select(MonthlySummary).where(
                        and_(
                            MonthlySummary.user_id == user.id,
                            MonthlySummary.month == current_month,
                            MonthlySummary.year == current_year
                        )
                    )
                )
                summary = result.scalar_one_or_none()
                
                if summary:
                    await db.delete(summary)
            
            await db.commit()
            
            print(f"\n✅ Rolled back to:")
            print(f"  League: {user.current_league}")
            
            # Remove backup file
            self.backup_file.unlink()
            print(f"🗑️  Backup file removed")


async def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Test promotion:  python test_promotion_with_rollback.py <username>")
        print("  Rollback:        python test_promotion_with_rollback.py --rollback")
        print("\nExample:")
        print("  python test_promotion_with_rollback.py edwards_test1")
        print("  python test_promotion_with_rollback.py --rollback")
        sys.exit(1)
    
    tester = PromotionTester()
    
    if sys.argv[1] == "--rollback":
        await tester.rollback_promotion()
    else:
        username = sys.argv[1]
        await tester.test_promote_user(username)


if __name__ == "__main__":
    asyncio.run(main())