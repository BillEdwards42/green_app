#!/usr/bin/env python3
"""
Seed league-specific tasks matching Flutter app structure
These are the exact tasks from the Flutter app's LeagueRequirements
"""

import asyncio
import sys
import os
from sqlalchemy import select, delete

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.task import Task


# League-specific tasks from Flutter app
LEAGUE_TASKS = {
    'bronze': [
        {
            "name": "第一次打開app",
            "description": "First time opening the app",
            "points": 50,
            "task_type": "firstAppOpen"
        },
        {
            "name": "第一次登入",
            "description": "First time logging in",
            "points": 50,
            "task_type": "firstLogin"
        },
        {
            "name": "第一次紀錄家電使用",
            "description": "First time logging appliance usage",
            "points": 100,
            "task_type": "firstApplianceLog"
        }
    ],
    'silver': [
        {
            "name": "排碳減少30公克",
            "description": "Reduce carbon emissions by 30g",
            "points": 100,
            "task_type": "carbonReduction",
            "target": 30
        },
        {
            "name": "每週紀錄3次或以上",
            "description": "Log usage 3 or more times per week",
            "points": 100,
            "task_type": "weeklyLogs",
            "target": 3
        },
        {
            "name": "每週app開啟超過5次",
            "description": "Open app more than 5 times per week",
            "points": 100,
            "task_type": "weeklyAppOpens",
            "target": 5
        }
    ],
    'gold': [
        {
            "name": "排碳減少100公克",
            "description": "Reduce carbon emissions by 100g",
            "points": 150,
            "task_type": "carbonReduction",
            "target": 100
        },
        {
            "name": "每週紀錄5次或以上",
            "description": "Log usage 5 or more times per week",
            "points": 150,
            "task_type": "weeklyLogs",
            "target": 5
        },
        {
            "name": "紀錄過超過或等於5種的不同家電使用",
            "description": "Log usage for 5 or more different appliances",
            "points": 150,
            "task_type": "applianceVariety",
            "target": 5
        }
    ],
    'emerald': [
        {
            "name": "排碳減少500公克",
            "description": "Reduce carbon emissions by 500g",
            "points": 200,
            "task_type": "carbonReduction",
            "target": 500
        },
        {
            "name": "app每天至少開啟一次",
            "description": "Open app at least once every day",
            "points": 200,
            "task_type": "dailyAppOpen"
        },
        {
            "name": "每天至少紀錄一次",
            "description": "Log usage at least once every day",
            "points": 200,
            "task_type": "dailyLog"
        }
    ]
}


async def seed_league_tasks():
    """Seed all league-specific tasks into the database"""
    async with AsyncSessionLocal() as db:
        print("=== Seeding League-Specific Tasks ===\n")
        
        # Check existing tasks
        result = await db.execute(select(Task))
        existing_tasks = result.scalars().all()
        
        if existing_tasks:
            print(f"⚠️  Found {len(existing_tasks)} existing tasks.")
            if "--auto" in sys.argv:
                print("Auto mode: Deleting existing tasks...")
                # Delete all UserTask entries first (foreign key constraint)
                from app.models.task import UserTask
                await db.execute(delete(UserTask))
                # Delete all existing tasks
                await db.execute(delete(Task))
                await db.commit()
                print("✅ Deleted all existing tasks and user task entries")
            else:
                response = input("Do you want to DELETE ALL existing tasks and recreate them? (y/n): ")
                if response.lower() == 'y':
                    # Delete all existing tasks
                    await db.execute(delete(Task))
                    await db.commit()
                    print("✅ Deleted all existing tasks")
                else:
                    print("Aborted.")
                    return
        
        # Create tasks for each league
        created_count = 0
        for league, tasks in LEAGUE_TASKS.items():
            print(f"\n📋 Creating tasks for {league.upper()} league:")
            
            for task_data in tasks:
                task = Task(
                    name=task_data["name"],
                    description=task_data["description"],
                    points=task_data["points"],
                    league=league,
                    task_type=task_data["task_type"],
                    target_value=task_data.get("target"),
                    is_active=True
                )
                db.add(task)
                created_count += 1
                print(f"   ✅ {task_data['name']} ({task_data['points']} points)")
        
        await db.commit()
        print(f"\n✨ Successfully created {created_count} tasks across all leagues")
        
        # Show final task list
        print("\n=== All Tasks in Database ===")
        result = await db.execute(select(Task).order_by(Task.league, Task.id))
        all_tasks = result.scalars().all()
        
        current_league = None
        for task in all_tasks:
            if task.league != current_league:
                current_league = task.league
                print(f"\n{task.league.upper()} League:")
            
            print(f"  ID: {task.id}")
            print(f"    Name: {task.name}")
            print(f"    Type: {task.task_type}")
            print(f"    Points: {task.points}")
            if task.target_value:
                print(f"    Target: {task.target_value}")
            print()


if __name__ == "__main__":
    print("League Task Seeder - Creating tasks matching Flutter app structure\n")
    asyncio.run(seed_league_tasks())