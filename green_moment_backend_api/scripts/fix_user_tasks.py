#!/usr/bin/env python3
"""
Fix user tasks - removes tasks from wrong leagues
Ensures users only have tasks from their current league
"""

import asyncio
import sys
import os
from datetime import datetime
from sqlalchemy import select, and_, delete

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.task import Task, UserTask


async def fix_user_tasks(username: str = None):
    """Fix user tasks to only show current league tasks"""
    async with AsyncSessionLocal() as db:
        # Get users to fix
        if username:
            result = await db.execute(
                select(User).where(User.username == username)
            )
            users = result.scalars().all()
        else:
            # Fix all users
            result = await db.execute(
                select(User).where(User.deleted_at.is_(None))
            )
            users = result.scalars().all()
        
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        for user in users:
            print(f"\n👤 Fixing tasks for: {user.username}")
            print(f"   Current League: {user.current_league}")
            
            # Get all user tasks for current month
            result = await db.execute(
                select(UserTask, Task).join(Task).where(
                    and_(
                        UserTask.user_id == user.id,
                        UserTask.month == current_month,
                        UserTask.year == current_year
                    )
                )
            )
            all_tasks = result.all()
            
            # Separate tasks by league
            correct_tasks = []
            wrong_tasks = []
            
            for user_task, task in all_tasks:
                if task.league == user.current_league:
                    correct_tasks.append((user_task, task))
                else:
                    wrong_tasks.append((user_task, task))
            
            if wrong_tasks:
                print(f"   ❌ Found {len(wrong_tasks)} tasks from wrong leagues:")
                for user_task, task in wrong_tasks:
                    print(f"      - {task.name} (from {task.league} league)")
                
                # Delete wrong league tasks
                wrong_task_ids = [ut.id for ut, _ in wrong_tasks]
                await db.execute(
                    delete(UserTask).where(UserTask.id.in_(wrong_task_ids))
                )
                print(f"   🗑️  Removed {len(wrong_tasks)} incorrect tasks")
            
            # Check if user has all tasks from current league
            result = await db.execute(
                select(Task).where(
                    and_(
                        Task.league == user.current_league,
                        Task.is_active == True
                    )
                )
            )
            league_tasks = result.scalars().all()
            
            existing_task_ids = [task.id for _, task in correct_tasks]
            missing_tasks = [t for t in league_tasks if t.id not in existing_task_ids]
            
            if missing_tasks:
                print(f"   ➕ Adding {len(missing_tasks)} missing {user.current_league} tasks:")
                for task in missing_tasks:
                    user_task = UserTask(
                        user_id=user.id,
                        task_id=task.id,
                        month=current_month,
                        year=current_year,
                        completed=False,
                        points_earned=0
                    )
                    db.add(user_task)
                    print(f"      + {task.name}")
            
            print(f"   ✅ User now has {len(correct_tasks) + len(missing_tasks)} {user.current_league} tasks")
        
        await db.commit()
        print(f"\n✅ Fixed tasks for {len(users)} user(s)")


async def main():
    if len(sys.argv) > 1:
        username = sys.argv[1]
        print(f"🔧 Fixing tasks for user: {username}")
    else:
        username = None
        print("🔧 Fixing tasks for all users")
    
    await fix_user_tasks(username)


if __name__ == "__main__":
    asyncio.run(main())