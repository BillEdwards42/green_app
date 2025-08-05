#!/usr/bin/env python3
"""
Database cleanup and migration script
This script:
1. Seeds initial tasks if they don't exist
2. Creates UserTask entries for all users for the current month
3. Resets task completion counters based on actual UserTask data
4. Provides a clean slate for cloud-only task storage
"""

import asyncio
import sys
import os
from datetime import datetime
from sqlalchemy import select, and_, func

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.task import Task, UserTask


# Standard tasks that should exist
STANDARD_TASKS = [
    {
        "name": "完成5次家電使用記錄",
        "description": "記錄5次在綠色時段使用家電的行為",
        "points": 100
    },
    {
        "name": "累積減碳1公斤",
        "description": "透過智慧用電累積減少1公斤的碳排放",
        "points": 150
    },
    {
        "name": "連續7天查看碳密度預報",
        "description": "連續7天開啟應用程式查看碳密度預報",
        "points": 100
    }
]


async def cleanup_and_migrate():
    """Main cleanup and migration function"""
    async with AsyncSessionLocal() as db:
        print("=== Database Cleanup and Migration ===\n")
        
        # Step 1: Ensure tasks exist
        print("Step 1: Checking and seeding tasks...")
        result = await db.execute(select(Task))
        existing_tasks = result.scalars().all()
        
        if not existing_tasks:
            print("   No tasks found. Creating standard tasks...")
            for task_data in STANDARD_TASKS:
                task = Task(
                    name=task_data["name"],
                    description=task_data["description"],
                    points=task_data["points"],
                    is_active=True
                )
                db.add(task)
            await db.commit()
            print(f"   ✅ Created {len(STANDARD_TASKS)} tasks")
        else:
            print(f"   ✅ Found {len(existing_tasks)} existing tasks")
        
        # Get fresh task list
        result = await db.execute(select(Task).where(Task.is_active == True))
        tasks = result.scalars().all()
        
        print("\n" + "="*50 + "\n")
        
        # Step 2: Get all users and create UserTask entries for current month
        print("Step 2: Creating UserTask entries for all users...")
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        result = await db.execute(select(User).where(User.deleted_at.is_(None)))
        users = result.scalars().all()
        
        print(f"   Found {len(users)} active users")
        
        created_count = 0
        for user in users:
            # Check if user already has tasks for this month
            result = await db.execute(
                select(UserTask).where(
                    and_(
                        UserTask.user_id == user.id,
                        UserTask.month == current_month,
                        UserTask.year == current_year
                    )
                )
            )
            existing_user_tasks = result.scalars().all()
            
            if not existing_user_tasks:
                # Create tasks for this user
                for task in tasks:
                    user_task = UserTask(
                        user_id=user.id,
                        task_id=task.id,
                        month=current_month,
                        year=current_year,
                        completed=False,
                        points_earned=0
                    )
                    db.add(user_task)
                    created_count += 1
                print(f"   ✅ Created {len(tasks)} tasks for {user.username}")
            else:
                print(f"   ⏭️  {user.username} already has {len(existing_user_tasks)} tasks for {current_month}/{current_year}")
        
        await db.commit()
        print(f"\n   Total UserTask entries created: {created_count}")
        
        print("\n" + "="*50 + "\n")
        
        # Step 3: Fix task completion counters
        print("Step 3: Fixing task completion counters...")
        
        for user in users:
            # Count actual completed tasks for current month
            result = await db.execute(
                select(func.count(UserTask.id)).where(
                    and_(
                        UserTask.user_id == user.id,
                        UserTask.month == current_month,
                        UserTask.year == current_year,
                        UserTask.completed == True
                    )
                )
            )
            completed_count = result.scalar() or 0
            
            # Update user's counter if different
            if user.current_month_tasks_completed != completed_count:
                print(f"   🔧 Fixing {user.username}: {user.current_month_tasks_completed} → {completed_count}")
                user.current_month_tasks_completed = completed_count
            else:
                print(f"   ✅ {user.username}: counter is correct ({completed_count})")
        
        await db.commit()
        
        print("\n" + "="*50 + "\n")
        
        # Step 4: Summary
        print("Step 4: Migration Summary")
        
        # Total tasks
        result = await db.execute(select(func.count(Task.id)))
        total_tasks = result.scalar()
        
        # Total UserTask entries
        result = await db.execute(select(func.count(UserTask.id)))
        total_user_tasks = result.scalar()
        
        # Total completed tasks this month
        result = await db.execute(
            select(func.count(UserTask.id)).where(
                and_(
                    UserTask.month == current_month,
                    UserTask.year == current_year,
                    UserTask.completed == True
                )
            )
        )
        completed_this_month = result.scalar()
        
        print(f"   📊 Database Status:")
        print(f"      - Total tasks available: {total_tasks}")
        print(f"      - Total UserTask entries: {total_user_tasks}")
        print(f"      - Tasks completed this month: {completed_this_month}")
        print(f"      - Active users: {len(users)}")
        
        print("\n✨ Migration completed successfully!")
        print("\n⚠️  IMPORTANT: Update your Flutter app to:")
        print("   1. Remove all local task storage (SharedPreferences/SQLite)")
        print("   2. Use the new API endpoints:")
        print("      - GET  /api/v1/tasks/my-tasks    (get user's tasks)")
        print("      - POST /api/v1/tasks/complete/{task_id}  (mark task complete)")
        print("      - POST /api/v1/tasks/uncomplete/{task_id}  (mark task incomplete)")


if __name__ == "__main__":
    print("Green Moment Database Cleanup and Migration\n")
    print("This script will:")
    print("1. Ensure standard tasks exist in the database")
    print("2. Create UserTask entries for all users for the current month")
    print("3. Fix task completion counters based on actual data")
    print("4. Prepare the database for cloud-only task storage\n")
    
    if "--auto" in sys.argv:
        # Run without prompting
        asyncio.run(cleanup_and_migrate())
    else:
        response = input("Continue? (y/n): ")
        if response.lower() == 'y':
            asyncio.run(cleanup_and_migrate())
        else:
            print("Aborted.")