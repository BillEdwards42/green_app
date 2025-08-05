#!/usr/bin/env python3
"""
Daily test script for league promotion using real data
Runs every day at a configurable time to test promotion logic
Uses actual July data since it's now August
"""

import asyncio
import schedule
import time
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.task import Task, UserTask
from app.models.chore import Chore
from app.models.monthly_summary import MonthlySummary
from scripts.league_promotion_scheduler import LeaguePromotionService

# CONFIGURE TEST TIME HERE
TEST_TIME = "17:30"  # Change this to any time you want (24-hour format)
TEST_USERNAME = "edwards_test1"  # Change to your test username


async def test_promotion_with_real_data():
    """Test promotion using real data from last month (July)"""
    print(f"\n{'='*60}")
    print(f"[{datetime.now()}] Starting Daily Promotion Test")
    print(f"{'='*60}\n")
    
    async with AsyncSessionLocal() as db:
        # Get the test user
        result = await db.execute(
            select(User).where(User.username == TEST_USERNAME)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User '{TEST_USERNAME}' not found!")
            return
        
        print(f"👤 Testing user: {user.username}")
        print(f"   Current league: {user.current_league}")
        print(f"   Total carbon saved: {user.total_carbon_saved:.3f} kg")
        
        # Since it's August, we'll check July data
        last_month = 7  # July
        last_year = 2025
        
        print(f"\n📅 Checking data for {last_month}/{last_year} (last month)")
        
        # 1. Check UserTask completion for July
        result = await db.execute(
            select(UserTask, Task).join(Task).where(
                and_(
                    UserTask.user_id == user.id,
                    UserTask.month == last_month,
                    UserTask.year == last_year
                )
            ).order_by(Task.id)
        )
        
        user_tasks = result.all()
        completed_count = 0
        total_tasks = len(user_tasks)
        
        print(f"\n📋 Task Status for July:")
        if user_tasks:
            for user_task, task in user_tasks:
                status = "✅" if user_task.completed else "❌"
                if user_task.completed:
                    completed_count += 1
                print(f"   {status} {task.name} ({task.points} points)")
            print(f"\n   Summary: {completed_count}/{total_tasks} tasks completed")
        else:
            print("   ⚠️  No tasks found for July!")
        
        # 2. Check chores logged in July
        result = await db.execute(
            select(Chore).where(
                and_(
                    Chore.user_id == user.id,
                    func.extract('month', Chore.start_time) == last_month,
                    func.extract('year', Chore.start_time) == last_year
                )
            ).order_by(Chore.start_time)
        )
        
        chores = result.scalars().all()
        
        print(f"\n🏠 Chores logged in July: {len(chores)}")
        if chores:
            appliance_usage = {}
            for chore in chores[:5]:  # Show first 5
                print(f"   - {chore.start_time.strftime('%Y-%m-%d %H:%M')}: {chore.appliance_type} ({chore.duration_minutes} min)")
                appliance_usage[chore.appliance_type] = appliance_usage.get(chore.appliance_type, 0) + 1
            
            if len(chores) > 5:
                print(f"   ... and {len(chores) - 5} more")
            
            print(f"\n   Appliance variety: {len(appliance_usage)} different appliances")
            for appliance, count in appliance_usage.items():
                print(f"     - {appliance}: {count} times")
        
        # 3. Run the actual promotion check
        print(f"\n🔄 Running promotion check...")
        
        service = LeaguePromotionService()
        
        # Create a temporary override for testing
        # The service will check July data since we're in August
        promotion_result = await service.check_and_promote_user(db, user)
        
        print(f"\n📊 Promotion Results:")
        print(f"   Promoted: {'✅ YES' if promotion_result['promoted'] else '❌ NO'}")
        print(f"   Old league: {promotion_result['old_league']}")
        print(f"   New league: {promotion_result['new_league']}")
        print(f"   Tasks completed: {promotion_result['tasks_completed']}/3")
        print(f"   Carbon saved: {promotion_result['carbon_saved']:.3f} kg")
        
        # 4. Check if monthly summary was created
        result = await db.execute(
            select(MonthlySummary).where(
                and_(
                    MonthlySummary.user_id == user.id,
                    MonthlySummary.month == last_month,
                    MonthlySummary.year == last_year
                )
            )
        )
        summary = result.scalar_one_or_none()
        
        if summary:
            print(f"\n📈 Monthly Summary for July:")
            print(f"   Total carbon saved: {summary.total_carbon_saved:.3f} kg")
            print(f"   Total chores logged: {summary.total_chores_logged}")
            print(f"   Total hours shifted: {summary.total_hours_shifted:.1f}")
            print(f"   Top appliance: {summary.top_appliance}")
            print(f"   League progression: {summary.league_at_month_start} → {summary.league_at_month_end}")
        
        # 5. Check current month (August) tasks
        current_month = 8
        current_year = 2025
        
        result = await db.execute(
            select(UserTask, Task).join(Task).where(
                and_(
                    UserTask.user_id == user.id,
                    UserTask.month == current_month,
                    UserTask.year == current_year
                )
            ).order_by(Task.id)
        )
        
        current_tasks = result.all()
        
        print(f"\n📋 Current Month (August) Tasks:")
        if current_tasks:
            # Refresh user to get updated league
            await db.refresh(user)
            print(f"   League: {user.current_league}")
            for user_task, task in current_tasks:
                status = "✅" if user_task.completed else "⏳"
                print(f"   {status} {task.name} ({task.points} points)")
        else:
            print("   ⚠️  No tasks assigned for August yet!")
        
        print(f"\n✨ Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)


def run_scheduled_test():
    """Run the test on schedule"""
    print(f"[{datetime.now()}] Daily Promotion Test Scheduler Started")
    print(f"Scheduled to run daily at {TEST_TIME}")
    print(f"Testing user: {TEST_USERNAME}")
    print("Press Ctrl+C to stop\n")
    
    # Schedule the test
    schedule.every().day.at(TEST_TIME).do(lambda: asyncio.run(test_promotion_with_real_data()))
    
    # Also allow immediate test with --now flag
    if "--now" in sys.argv:
        print("Running test immediately...")
        asyncio.run(test_promotion_with_real_data())
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    try:
        if "--once" in sys.argv:
            # Run once and exit
            asyncio.run(test_promotion_with_real_data())
        else:
            # Run on schedule
            run_scheduled_test()
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] Scheduler stopped")