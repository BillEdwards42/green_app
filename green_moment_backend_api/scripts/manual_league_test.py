#!/usr/bin/env python3
"""
Manual testing script for league promotion
Allows you to set specific dates and trigger promotion manually
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
from app.models.monthly_summary import MonthlySummary
from scripts.league_promotion_scheduler import LeaguePromotionService


async def show_user_status(username: str):
    """Show current status of a user"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User '{username}' not found")
            return None
            
        print(f"\n👤 User: {user.username}")
        print(f"   ID: {user.id}")
        print(f"   League: {user.current_league}")
        print(f"   Total carbon saved: {user.total_carbon_saved:.3f} kg")
        print(f"   Current month tasks completed: {user.current_month_tasks_completed}")
        
        # Check monthly summaries
        result = await db.execute(
            select(MonthlySummary)
            .where(MonthlySummary.user_id == user.id)
            .order_by(MonthlySummary.year.desc(), MonthlySummary.month.desc())
            .limit(3)
        )
        summaries = result.scalars().all()
        
        if summaries:
            print(f"\n📊 Recent monthly summaries:")
            for summary in summaries:
                print(f"   {summary.month}/{summary.year}:")
                print(f"     - Carbon saved: {summary.total_carbon_saved:.3f} kg")
                print(f"     - Tasks completed: {summary.tasks_completed}")
                print(f"     - League: {summary.league_at_month_start} → {summary.league_at_month_end}")
                print(f"     - Promoted: {'✅' if summary.league_upgraded else '❌'}")
        
        return user.id


async def force_complete_current_tasks(user_id: int):
    """Force complete all current month tasks for testing"""
    async with AsyncSessionLocal() as db:
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Get all user tasks for current month
        result = await db.execute(
            select(UserTask).where(
                and_(
                    UserTask.user_id == user_id,
                    UserTask.month == current_month,
                    UserTask.year == current_year
                )
            )
        )
        user_tasks = result.scalars().all()
        
        if not user_tasks:
            print("❌ No tasks found for current month. Creating them...")
            
            # Get user's league
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one()
            
            # Get tasks for league
            result = await db.execute(
                select(Task).where(
                    and_(
                        Task.league == user.current_league,
                        Task.is_active == True
                    )
                )
            )
            tasks = result.scalars().all()
            
            # Create tasks
            for task in tasks:
                user_task = UserTask(
                    user_id=user_id,
                    task_id=task.id,
                    month=current_month,
                    year=current_year,
                    completed=False,
                    points_earned=0
                )
                db.add(user_task)
            
            await db.commit()
            
            # Re-fetch
            result = await db.execute(
                select(UserTask).where(
                    and_(
                        UserTask.user_id == user_id,
                        UserTask.month == current_month,
                        UserTask.year == current_year
                    )
                )
            )
            user_tasks = result.scalars().all()
        
        # Complete all tasks
        completed_count = 0
        for task in user_tasks:
            if not task.completed:
                task.completed = True
                task.completed_at = datetime.now()
                task.points_earned = 100  # Default points
                completed_count += 1
        
        # Update user's task counter
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(current_month_tasks_completed=len(user_tasks))
        )
        
        await db.commit()
        print(f"✅ Completed {completed_count} tasks")


async def run_promotion_for_user(username: str):
    """Run promotion check for a specific user"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User '{username}' not found")
            return
        
        print(f"\n🔄 Running promotion check for {user.username}...")
        
        service = LeaguePromotionService()
        
        # Override to check current month instead of last month for testing
        # You can modify the service temporarily for testing
        result = await service.check_and_promote_user(db, user)
        
        print(f"\n📊 Promotion Results:")
        print(f"   Promoted: {'✅ YES' if result['promoted'] else '❌ NO'}")
        print(f"   Old league: {result['old_league']}")
        print(f"   New league: {result['new_league']}")
        print(f"   Tasks completed: {result['tasks_completed']}")
        print(f"   Carbon saved: {result['carbon_saved']:.3f} kg")


async def set_user_league(username: str, league: str):
    """Manually set a user's league"""
    valid_leagues = ['bronze', 'silver', 'gold', 'emerald', 'diamond']
    
    if league not in valid_leagues:
        print(f"❌ Invalid league. Must be one of: {', '.join(valid_leagues)}")
        return
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User '{username}' not found")
            return
        
        old_league = user.current_league
        user.current_league = league
        await db.commit()
        
        print(f"✅ Changed {username}'s league: {old_league} → {league}")


async def main():
    print("=== Manual League Promotion Test ===\n")
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 manual_league_test.py <username> [command]")
        print("\nCommands:")
        print("  status              - Show user status (default)")
        print("  complete-tasks      - Complete all current month tasks")
        print("  run-promotion       - Run promotion check now")
        print("  set-league <league> - Set user's league manually")
        print("\nExamples:")
        print("  python3 manual_league_test.py edwards_test1")
        print("  python3 manual_league_test.py edwards_test1 complete-tasks")
        print("  python3 manual_league_test.py edwards_test1 set-league silver")
        return
    
    username = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else "status"
    
    if command == "status":
        await show_user_status(username)
    
    elif command == "complete-tasks":
        user_id = await show_user_status(username)
        if user_id:
            await force_complete_current_tasks(user_id)
            await show_user_status(username)
    
    elif command == "run-promotion":
        await show_user_status(username)
        await run_promotion_for_user(username)
        await show_user_status(username)
    
    elif command == "set-league" and len(sys.argv) > 3:
        league = sys.argv[3]
        await set_user_league(username, league)
        await show_user_status(username)
    
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    asyncio.run(main())