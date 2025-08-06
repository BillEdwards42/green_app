#!/usr/bin/env python3
"""
Remove outdated onboarding tasks from the database
"""

import asyncio
import sys
import os
from sqlalchemy import select, delete

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.task import Task, UserTask


async def remove_outdated_tasks():
    """Remove outdated onboarding tasks"""
    
    outdated_task_names = [
        "第一次打開app",
        "第一次登入", 
        "第一次紀錄家電使用"
    ]
    
    async with AsyncSessionLocal() as db:
        # Find these tasks
        result = await db.execute(
            select(Task).where(Task.name.in_(outdated_task_names))
        )
        tasks = result.scalars().all()
        
        if not tasks:
            print("No outdated tasks found")
            return
        
        print(f"\n🗑️ Found {len(tasks)} outdated tasks to remove:")
        
        for task in tasks:
            print(f"  - {task.name} (ID: {task.id}, League: {task.league})")
            
            # Delete user_tasks first (foreign key constraint)
            result = await db.execute(
                delete(UserTask).where(UserTask.task_id == task.id)
            )
            print(f"    Deleted {result.rowcount} user task assignments")
            
            # Delete the task itself
            await db.delete(task)
            print(f"    Deleted task")
        
        await db.commit()
        print(f"\n✅ Successfully removed {len(tasks)} outdated tasks")


async def main():
    print("🧹 Removing outdated onboarding tasks...")
    await remove_outdated_tasks()


if __name__ == "__main__":
    asyncio.run(main())