#!/usr/bin/env python3
"""
Investigate task synchronization between Flutter app and backend database
"""

import asyncio
import sys
import os
from datetime import datetime
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.task import Task, UserTask


async def investigate_task_storage():
    """Check task storage and sync status"""
    async with AsyncSessionLocal() as db:
        print("=== Task Storage Investigation ===\n")
        
        # 1. Check all tasks in the system
        result = await db.execute(select(Task))
        tasks = result.scalars().all()
        
        print(f"1. Total tasks in 'tasks' table: {len(tasks)}")
        if tasks:
            print("   Available tasks:")
            for task in tasks:
                print(f"   - ID: {task.id}, Name: {task.name}, Active: {task.is_active}")
        else:
            print("   ⚠️  No tasks found in the tasks table!")
            print("   This suggests tasks might not be seeded or created yet.")
        
        print("\n" + "="*50 + "\n")
        
        # 2. Check UserTask entries
        result = await db.execute(select(UserTask))
        user_tasks = result.scalars().all()
        
        print(f"2. Total UserTask entries: {len(user_tasks)}")
        
        # Group by user
        user_task_map = {}
        for ut in user_tasks:
            if ut.user_id not in user_task_map:
                user_task_map[ut.user_id] = []
            user_task_map[ut.user_id].append(ut)
        
        if user_task_map:
            print("   UserTask entries by user:")
            for user_id, tasks in user_task_map.items():
                # Get username
                result = await db.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
                username = user.username if user else f"User {user_id}"
                
                print(f"\n   {username}:")
                for task in tasks:
                    print(f"     - Task ID: {task.task_id}, Month: {task.month}/{task.year}, Completed: {task.completed}")
        else:
            print("   ⚠️  No UserTask entries found!")
        
        print("\n" + "="*50 + "\n")
        
        # 3. Check specific user: edwards_test1
        result = await db.execute(select(User).where(User.username == "edwards_test1"))
        edwards_user = result.scalar_one_or_none()
        
        if edwards_user:
            print(f"3. Investigating user 'edwards_test1' (ID: {edwards_user.id}):")
            
            # Check UserTask entries for current month
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            result = await db.execute(
                select(UserTask).where(
                    and_(
                        UserTask.user_id == edwards_user.id,
                        UserTask.month == current_month,
                        UserTask.year == current_year
                    )
                )
            )
            current_tasks = result.scalars().all()
            
            print(f"   - Current month ({current_month}/{current_year}) tasks: {len(current_tasks)}")
            if current_tasks:
                for task in current_tasks:
                    print(f"     Task {task.task_id}: Completed = {task.completed}")
            else:
                print("     ⚠️  No tasks for current month!")
            
            # Check all UserTask entries for this user
            result = await db.execute(
                select(UserTask).where(UserTask.user_id == edwards_user.id)
            )
            all_user_tasks = result.scalars().all()
            
            print(f"   - Total UserTask entries across all months: {len(all_user_tasks)}")
            
            # Check user's task completion counter
            print(f"   - current_month_tasks_completed field: {edwards_user.current_month_tasks_completed}")
            
        else:
            print("3. User 'edwards_test1' not found in database!")
        
        print("\n" + "="*50 + "\n")
        
        # 4. Analysis and conclusions
        print("4. Analysis:")
        print("\n   POSSIBLE REASONS FOR MISMATCH:")
        print("   a) Tasks are stored locally in Flutter app (SharedPreferences/SQLite)")
        print("   b) API endpoint for syncing task completion might not be implemented")
        print("   c) Flutter app might be using mock data for testing")
        print("   d) Database tasks haven't been seeded/initialized")
        print("   e) Task completion API might not be properly updating UserTask entries")
        
        print("\n   NEXT STEPS TO INVESTIGATE:")
        print("   1. Check Flutter app code for local storage (SharedPreferences)")
        print("   2. Verify API endpoints for task completion exist and work")
        print("   3. Check if tasks need to be seeded in the database")
        print("   4. Look for any sync mechanisms between app and backend")


async def check_api_endpoints():
    """Check which task-related API endpoints exist"""
    print("\n=== API Endpoints Check ===\n")
    
    # Read the API router files to understand available endpoints
    api_files = [
        "/home/bill/StudioProjects/green_moment_backend_api/app/api/v1/endpoints/users.py",
        "/home/bill/StudioProjects/green_moment_backend_api/app/api/v1/endpoints/progress.py",
        "/home/bill/StudioProjects/green_moment_backend_api/app/api/v1/api.py"
    ]
    
    print("Checking for task-related endpoints in API files...")
    
    for file_path in api_files:
        if os.path.exists(file_path):
            print(f"\n📄 {os.path.basename(file_path)}:")
            with open(file_path, 'r') as f:
                content = f.read()
                # Look for task-related endpoints
                if 'task' in content.lower():
                    # Find lines with @router decorators related to tasks
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if '@router' in line and 'task' in line.lower():
                            print(f"   Line {i+1}: {line.strip()}")
                            # Print the next few lines to see the function
                            for j in range(1, 4):
                                if i+j < len(lines):
                                    print(f"   Line {i+j+1}: {lines[i+j].strip()}")
                else:
                    print("   No task-related endpoints found")


if __name__ == "__main__":
    print("Starting task synchronization investigation...\n")
    asyncio.run(investigate_task_storage())
    asyncio.run(check_api_endpoints())
    
    print("\n\n💡 RECOMMENDATION:")
    print("Based on the investigation, it appears tasks are likely stored locally")
    print("in the Flutter app and not properly synced to the backend database.")
    print("Check the Flutter app's local storage implementation and ensure")
    print("proper API calls are made to sync task completion status.")