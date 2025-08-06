#!/usr/bin/env python3
"""
Test script for league promotion and carbon calculation
This script simulates a month's worth of activity and triggers promotion
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import select, and_, update

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.task import Task, UserTask
from app.models.chore import Chore
from app.constants.appliances import APPLIANCE_POWER
from scripts.league_promotion_scheduler import LeaguePromotionService


async def setup_test_user():
    """Create or get a test user"""
    async with AsyncSessionLocal() as db:
        # Get or create test user
        result = await db.execute(
            select(User).where(User.username == "league_test_user")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                username="league_test_user",
                email="league_test@example.com",
                is_anonymous=False,
                current_league="bronze"
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"✅ Created test user: {user.username}")
        else:
            print(f"✅ Found existing test user: {user.username} (League: {user.current_league})")
        
        return user.id


async def simulate_last_month_activity(user_id: int, complete_all_tasks: bool = True):
    """Simulate activity for the previous month"""
    async with AsyncSessionLocal() as db:
        # Calculate last month
        today = datetime.now()
        if today.month == 1:
            last_month = 12
            last_year = today.year - 1
        else:
            last_month = today.month - 1
            last_year = today.year
        
        print(f"\n📅 Simulating activity for {last_month}/{last_year}")
        
        # 1. Create chores for last month to generate carbon savings
        chores_data = [
            {
                "appliance": "washing_machine",
                "duration": 60,
                "carbon_intensity": 0.450,  # kg CO2e/kWh
                "day": 5
            },
            {
                "appliance": "air_conditioner",
                "duration": 120,
                "carbon_intensity": 0.480,
                "day": 10
            },
            {
                "appliance": "dishwasher",
                "duration": 90,
                "carbon_intensity": 0.470,
                "day": 15
            },
            {
                "appliance": "electric_heater",
                "duration": 180,
                "carbon_intensity": 0.490,
                "day": 20
            },
            {
                "appliance": "washing_machine",
                "duration": 45,
                "carbon_intensity": 0.460,
                "day": 25
            }
        ]
        
        total_carbon_saved = 0.0
        
        for chore_data in chores_data:
            # Create chore with timestamp in last month
            start_time = datetime(last_year, last_month, chore_data["day"], 14, 0)
            end_time = start_time + timedelta(minutes=chore_data["duration"])
            
            chore = Chore(
                user_id=user_id,
                appliance_type=chore_data["appliance"],
                start_time=start_time,
                end_time=end_time,
                duration_minutes=chore_data["duration"],
                carbon_intensity_at_start=chore_data["carbon_intensity"]
            )
            db.add(chore)
            
            # Calculate carbon saved (simplified)
            # Assume worst case is 0.600 kg CO2e/kWh
            worst_case = 0.600
            actual = chore_data["carbon_intensity"]
            appliance_kw = APPLIANCE_POWER.get(chore_data["appliance"], 1.0)
            hours = chore_data["duration"] / 60.0
            
            carbon_saved = (worst_case - actual) * appliance_kw * hours
            total_carbon_saved += carbon_saved
            
            print(f"  📊 Logged {chore_data['appliance']} for {chore_data['duration']} min")
            print(f"     Carbon saved: {carbon_saved:.3f} kg")
        
        await db.commit()
        print(f"\n  💚 Total carbon saved last month: {total_carbon_saved:.3f} kg")
        
        # 2. Create and complete tasks for last month if requested
        if complete_all_tasks:
            # Get user's current league to assign appropriate tasks
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one()
            
            # Get tasks for user's league
            result = await db.execute(
                select(Task).where(
                    and_(
                        Task.league == user.current_league,
                        Task.is_active == True
                    )
                )
            )
            tasks = result.scalars().all()
            
            print(f"\n  📋 Creating and completing {len(tasks)} tasks for {user.current_league} league:")
            
            for task in tasks:
                # Create UserTask for last month
                user_task = UserTask(
                    user_id=user_id,
                    task_id=task.id,
                    month=last_month,
                    year=last_year,
                    completed=True,
                    completed_at=datetime(last_year, last_month, 28, 12, 0),
                    points_earned=task.points
                )
                db.add(user_task)
                print(f"     ✅ {task.name}")
            
            await db.commit()
            print(f"\n  🎯 All tasks completed for promotion!")
        else:
            print(f"\n  ⚠️  Tasks NOT completed - user should stay in same league")


async def run_promotion_check(user_id: int):
    """Run the promotion check for a specific user"""
    async with AsyncSessionLocal() as db:
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one()
        
        print(f"\n🔄 Running promotion check for {user.username}")
        print(f"   Current league: {user.current_league}")
        
        # Run promotion service
        service = LeaguePromotionService()
        result = await service.check_and_promote_user(db, user)
        
        print(f"\n📊 Results:")
        print(f"   Promoted: {'✅ YES' if result['promoted'] else '❌ NO'}")
        print(f"   New league: {result['new_league']}")
        print(f"   Tasks completed: {result['tasks_completed']}")
        print(f"   Carbon saved: {result['carbon_saved']:.3f} kg")
        
        # Check if user can see last month's carbon saved
        await db.refresh(user)
        print(f"\n💾 User data updated:")
        print(f"   Total carbon saved: {user.total_carbon_saved:.3f} kg")
        print(f"   Current league: {user.current_league}")


async def check_current_month_tasks(user_id: int):
    """Check tasks for current month"""
    async with AsyncSessionLocal() as db:
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one()
        
        # Get current month tasks
        result = await db.execute(
            select(UserTask, Task).join(Task).where(
                and_(
                    UserTask.user_id == user_id,
                    UserTask.month == current_month,
                    UserTask.year == current_year
                )
            )
        )
        
        print(f"\n📅 Current month ({current_month}/{current_year}) tasks for {user.username}:")
        print(f"   League: {user.current_league}")
        
        for user_task, task in result:
            status = "✅" if user_task.completed else "❌"
            print(f"   {status} {task.name} ({task.points} points)")


async def main():
    print("=== League Promotion Test Script ===\n")
    
    print("This script will:")
    print("1. Create a test user (or use existing)")
    print("2. Simulate last month's activity")
    print("3. Run the league promotion check")
    print("4. Show the results\n")
    
    # Setup test user
    user_id = await setup_test_user()
    
    # Ask if we should complete all tasks
    if "--complete-tasks" in sys.argv:
        complete_tasks = True
    elif "--skip-tasks" in sys.argv:
        complete_tasks = False
    else:
        response = input("\nComplete all tasks for promotion? (y/n): ")
        complete_tasks = response.lower() == 'y'
    
    # Simulate last month activity
    await simulate_last_month_activity(user_id, complete_tasks)
    
    # Run promotion check
    await run_promotion_check(user_id)
    
    # Show current month tasks
    await check_current_month_tasks(user_id)
    
    print("\n✨ Test completed!")
    print("\nTo test different scenarios:")
    print("- Run with --complete-tasks to auto-complete tasks")
    print("- Run with --skip-tasks to skip task completion")
    print("- Change user's league in database and run again")


if __name__ == "__main__":
    asyncio.run(main())