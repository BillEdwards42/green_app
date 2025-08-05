#!/usr/bin/env python3
"""
Seed initial tasks in the database
This creates the standard 3 tasks that all users need to complete each month
"""

import asyncio
import sys
import os
from datetime import datetime
from sqlalchemy import select

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.task import Task


# Define the 3 standard tasks
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


async def seed_tasks():
    """Seed the standard tasks into the database"""
    async with AsyncSessionLocal() as db:
        print("=== Seeding Tasks ===\n")
        
        # Check existing tasks
        result = await db.execute(select(Task))
        existing_tasks = result.scalars().all()
        
        if existing_tasks:
            print(f"⚠️  Found {len(existing_tasks)} existing tasks:")
            for task in existing_tasks:
                print(f"   - {task.name} (ID: {task.id})")
            
            response = input("\nDo you want to proceed and add new tasks? (y/n): ")
            if response.lower() != 'y':
                print("Aborted.")
                return
        
        # Create tasks
        created_count = 0
        for task_data in STANDARD_TASKS:
            # Check if task with same name already exists
            result = await db.execute(
                select(Task).where(Task.name == task_data["name"])
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"⏭️  Skipping '{task_data['name']}' - already exists")
            else:
                task = Task(
                    name=task_data["name"],
                    description=task_data["description"],
                    points=task_data["points"],
                    is_active=True
                )
                db.add(task)
                created_count += 1
                print(f"✅ Created task: {task_data['name']}")
        
        if created_count > 0:
            await db.commit()
            print(f"\n✨ Successfully created {created_count} tasks")
        else:
            print("\n👍 No new tasks needed")
        
        # Show final task list
        print("\n=== Current Tasks in Database ===")
        result = await db.execute(select(Task).order_by(Task.id))
        all_tasks = result.scalars().all()
        
        for task in all_tasks:
            print(f"ID: {task.id}")
            print(f"   Name: {task.name}")
            print(f"   Description: {task.description}")
            print(f"   Points: {task.points}")
            print(f"   Active: {task.is_active}")
            print()


if __name__ == "__main__":
    print("Task Seeder - Creating standard tasks for Green Moment\n")
    asyncio.run(seed_tasks())