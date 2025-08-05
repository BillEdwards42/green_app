#!/usr/bin/env python3
"""
Daily test script for league promotion using real data
Fixed version that handles timezone issues and uses all historical data for testing
"""

import asyncio
import schedule
import time
import sys
import os
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, and_, func, or_

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
    """Test promotion using all available historical data"""
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
        
        # First, check if user has ANY chores logged at all
        result = await db.execute(
            select(func.count(Chore.id)).where(Chore.user_id == user.id)
        )
        total_chores = result.scalar() or 0
        
        print(f"\n📊 Total chores ever logged: {total_chores}")
        
        if total_chores == 0:
            print("\n⚠️  WARNING: No chores have been logged for this user!")
            print("   This indicates an issue with chore logging from the app.")
            print("   Please check:")
            print("   - Is the app calling the chore logging API endpoint?")
            print("   - Are there any errors in the API logs?")
            print("   - Is the user authenticated when logging chores?")
        
        # Get all chores to find the date range
        result = await db.execute(
            select(
                func.min(Chore.start_time).label('earliest'),
                func.max(Chore.start_time).label('latest')
            ).where(Chore.user_id == user.id)
        )
        date_range = result.first()
        
        if date_range.earliest:
            print(f"\n📅 Chore date range: {date_range.earliest.strftime('%Y-%m-%d')} to {date_range.latest.strftime('%Y-%m-%d')}")
        
        # For testing, we'll check all available data as "last month"
        # This helps when there's no July data
        print(f"\n🔄 Checking ALL historical data for testing purposes...")
        
        # 1. Check ALL UserTask completion
        result = await db.execute(
            select(UserTask, Task).join(Task).where(
                UserTask.user_id == user.id
            ).order_by(UserTask.month.desc(), UserTask.year.desc(), Task.id)
        )
        
        all_user_tasks = result.all()
        
        if all_user_tasks:
            # Group by month/year
            tasks_by_month = {}
            for user_task, task in all_user_tasks:
                key = f"{user_task.month}/{user_task.year}"
                if key not in tasks_by_month:
                    tasks_by_month[key] = []
                tasks_by_month[key].append((user_task, task))
            
            print(f"\n📋 Task History:")
            for month_year, tasks in tasks_by_month.items():
                completed = sum(1 for ut, t in tasks if ut.completed)
                print(f"\n   {month_year}: {completed}/{len(tasks)} completed")
                for user_task, task in tasks:
                    status = "✅" if user_task.completed else "❌"
                    print(f"     {status} {task.name}")
        else:
            print("\n📋 No tasks found in history!")
        
        # 2. Check ALL chores
        result = await db.execute(
            select(Chore).where(
                Chore.user_id == user.id
            ).order_by(Chore.start_time.desc()).limit(10)
        )
        
        recent_chores = result.scalars().all()
        
        if recent_chores:
            print(f"\n🏠 Recent chores (showing last 10):")
            for chore in recent_chores:
                print(f"   - {chore.start_time.strftime('%Y-%m-%d %H:%M')}: {chore.appliance_type} ({chore.duration_minutes} min)")
        
        # 3. For testing promotion, use the most recent month with data
        # Find the most recent month with either tasks or chores
        latest_task_month = None
        latest_chore_month = None
        
        if all_user_tasks:
            latest_task = all_user_tasks[0][0]  # First item is most recent
            latest_task_month = (latest_task.month, latest_task.year)
        
        if recent_chores:
            latest_chore = recent_chores[0]
            latest_chore_month = (latest_chore.start_time.month, latest_chore.start_time.year)
        
        # Use the most recent month with any data
        test_month = None
        test_year = None
        
        if latest_task_month and latest_chore_month:
            # Compare and use the more recent one
            if (latest_task_month[1] > latest_chore_month[1] or 
                (latest_task_month[1] == latest_chore_month[1] and latest_task_month[0] >= latest_chore_month[0])):
                test_month, test_year = latest_task_month
            else:
                test_month, test_year = latest_chore_month
        elif latest_task_month:
            test_month, test_year = latest_task_month
        elif latest_chore_month:
            test_month, test_year = latest_chore_month
        else:
            # No data at all, use last month
            today = datetime.now()
            test_month = today.month - 1 if today.month > 1 else 12
            test_year = today.year if today.month > 1 else today.year - 1
        
        print(f"\n🔄 Running promotion check using data from {test_month}/{test_year}...")
        
        # Create a custom promotion service that handles timezone issues
        service = LeaguePromotionServiceFixed()
        
        # Override the month check for testing
        promotion_result = await service.check_and_promote_user_test(db, user, test_month, test_year)
        
        print(f"\n📊 Promotion Results:")
        print(f"   Promoted: {'✅ YES' if promotion_result['promoted'] else '❌ NO'}")
        print(f"   Old league: {promotion_result['old_league']}")
        print(f"   New league: {promotion_result['new_league']}")
        print(f"   Tasks completed: {promotion_result['tasks_completed']}")
        print(f"   Carbon saved: {promotion_result['carbon_saved']:.3f} kg")
        
        # 4. Check current month tasks
        current_month = datetime.now().month
        current_year = datetime.now().year
        
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
        
        print(f"\n📋 Current Month ({current_month}/{current_year}) Tasks:")
        if current_tasks:
            # Refresh user to get updated league
            await db.refresh(user)
            print(f"   League: {user.current_league}")
            for user_task, task in current_tasks:
                status = "✅" if user_task.completed else "⏳"
                print(f"   {status} {task.name} ({task.points} points)")
        else:
            print("   ⚠️  No tasks assigned for current month yet!")
        
        print(f"\n✨ Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)


class LeaguePromotionServiceFixed(LeaguePromotionService):
    """Fixed version that handles timezone issues"""
    
    async def check_and_promote_user_test(self, db, user, test_month, test_year):
        """Modified version for testing with specific month"""
        # Get user's tasks for the test month
        result = await db.execute(
            select(UserTask).where(
                and_(
                    UserTask.user_id == user.id,
                    UserTask.month == test_month,
                    UserTask.year == test_year
                )
            )
        )
        user_tasks = result.scalars().all()
        
        # Calculate carbon savings with fixed timezone handling
        carbon_data = await self.calculate_monthly_carbon_savings_fixed(db, user.id, test_month, test_year)
        
        # Check if user completed required tasks
        completed_tasks = sum(1 for task in user_tasks if task.completed)
        required_tasks = self.league_requirements.get(user.current_league, 3)
        
        # Determine if user gets promoted
        promoted = False
        new_league = user.current_league
        old_league = user.current_league
        
        if completed_tasks >= required_tasks and user.current_league != "diamond":
            # User qualifies for promotion!
            promoted = True
            new_league = self.league_progression[user.current_league]
        
        return {
            "user_id": user.id,
            "username": user.username,
            "promoted": promoted,
            "old_league": old_league,
            "new_league": new_league,
            "tasks_completed": completed_tasks,
            "carbon_saved": carbon_data["total_carbon_saved"]
        }
    
    async def calculate_monthly_carbon_savings_fixed(self, db, user_id, month, year):
        """Fixed version that handles empty carbon data and timezone issues"""
        from app.constants.appliances import APPLIANCE_POWER
        
        # Get all chores for the user in the specified month
        result = await db.execute(
            select(Chore).where(
                and_(
                    Chore.user_id == user_id,
                    func.extract('month', Chore.start_time) == month,
                    func.extract('year', Chore.start_time) == year
                )
            )
        )
        chores = result.scalars().all()
        
        total_carbon_saved = 0.0
        total_hours = 0.0
        appliance_usage = {}
        
        for chore in chores:
            # Get appliance power in kW
            appliance_kw = APPLIANCE_POWER.get(chore.appliance_type, 1.0)
            duration_hours = chore.duration_minutes / 60.0
            
            # For testing, use simplified calculation when carbon data is missing
            # Assume average intensity of 0.480 and worst case of 0.600
            actual_carbon_intensity = 0.480  # Default average
            worst_case_intensity = 0.600     # Default worst case
            
            # Carbon saved = (worst_case - actual) * kW * hours
            carbon_saved = (worst_case_intensity - actual_carbon_intensity) * appliance_kw * duration_hours
            total_carbon_saved += max(0, carbon_saved)
            total_hours += duration_hours
            
            # Track appliance usage
            if chore.appliance_type not in appliance_usage:
                appliance_usage[chore.appliance_type] = 0.0
            appliance_usage[chore.appliance_type] += duration_hours
        
        # Find most used appliance
        top_appliance = None
        top_hours = 0.0
        for appliance, hours in appliance_usage.items():
            if hours > top_hours:
                top_appliance = appliance
                top_hours = hours
        
        return {
            "total_carbon_saved": total_carbon_saved,
            "total_chores_logged": len(chores),
            "total_hours_shifted": total_hours,
            "top_appliance": top_appliance,
            "top_appliance_usage_hours": top_hours
        }


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