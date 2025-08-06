#!/usr/bin/env python3
import os
import asyncio
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL and convert to sync version
DATABASE_URL = os.getenv('DATABASE_SYNC_URL', 'postgresql://postgres:password@localhost:5432/green_moment')

def check_user_data(user_id=35):
    """Check all data for a specific user"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print(f"\n=== Checking data for user ID: {user_id} ===\n")
        
        # Check user details
        result = conn.execute(text("SELECT * FROM users WHERE id = :user_id"), {"user_id": user_id})
        user = result.fetchone()
        if user:
            print("User found:")
            print(f"  Username: {user.username}")
            print(f"  Email: {user.email}")
            print(f"  Created: {user.created_at}")
            print(f"  Deleted: {user.deleted_at}")
            print(f"  Total carbon saved: {user.total_carbon_saved}")
        else:
            print("User not found!")
            return
        
        # Check chores
        result = conn.execute(text("SELECT COUNT(*) as count FROM chores WHERE user_id = :user_id"), {"user_id": user_id})
        chore_count = result.scalar()
        print(f"\nChores logged: {chore_count}")
        
        # Show recent chores
        result = conn.execute(text("""
            SELECT id, appliance_type, start_time, duration_minutes, created_at 
            FROM chores 
            WHERE user_id = :user_id 
            ORDER BY created_at DESC 
            LIMIT 5
        """), {"user_id": user_id})
        chores = result.fetchall()
        if chores:
            print("Recent chores:")
            for chore in chores:
                print(f"  - {chore.appliance_type}: {chore.start_time} ({chore.duration_minutes} min) - Created: {chore.created_at}")
        
        # Check user tasks
        result = conn.execute(text("SELECT COUNT(*) as count FROM user_tasks WHERE user_id = :user_id"), {"user_id": user_id})
        task_count = result.scalar()
        print(f"\nTasks completed: {task_count}")
        
        # Check monthly summaries
        result = conn.execute(text("SELECT COUNT(*) as count FROM monthly_summaries WHERE user_id = :user_id"), {"user_id": user_id})
        summary_count = result.scalar()
        print(f"\nMonthly summaries: {summary_count}")
        
        # Check for any recent chore attempts (last 24 hours)
        result = conn.execute(text("""
            SELECT COUNT(*) as count 
            FROM chores 
            WHERE user_id = :user_id 
            AND created_at > NOW() - INTERVAL '24 hours'
        """), {"user_id": user_id})
        recent_count = result.scalar()
        print(f"\nChores in last 24 hours: {recent_count}")

def check_all_user_tables(user_id=35):
    """Comprehensive check of all tables for user data"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print(f"\n=== COMPREHENSIVE DATA CHECK FOR USER ID: {user_id} ===\n")
        
        # 1. Users table
        result = conn.execute(text("SELECT * FROM users WHERE id = :user_id"), {"user_id": user_id})
        user = result.fetchone()
        print("1. USERS TABLE:")
        if user:
            for key in user._mapping.keys():
                print(f"   {key}: {getattr(user, key)}")
        else:
            print("   No user found")
        
        # 2. Chores table
        print("\n2. CHORES TABLE:")
        result = conn.execute(text("""
            SELECT * FROM chores 
            WHERE user_id = :user_id 
            ORDER BY created_at DESC
        """), {"user_id": user_id})
        chores = result.fetchall()
        print(f"   Total chores: {len(chores)}")
        for i, chore in enumerate(chores, 1):
            print(f"   Chore {i}:")
            for key in chore._mapping.keys():
                print(f"     {key}: {getattr(chore, key)}")
        
        # 3. User Tasks table
        print("\n3. USER_TASKS TABLE:")
        result = conn.execute(text("""
            SELECT ut.*, t.name as task_name 
            FROM user_tasks ut
            LEFT JOIN tasks t ON ut.task_id = t.id
            WHERE ut.user_id = :user_id
        """), {"user_id": user_id})
        tasks = result.fetchall()
        print(f"   Total tasks: {len(tasks)}")
        for task in tasks:
            print(f"   - Task '{task.task_name}': completed={task.completed}, month={task.month}/{task.year}")
        
        # 4. Monthly Summaries table
        print("\n4. MONTHLY_SUMMARIES TABLE:")
        result = conn.execute(text("""
            SELECT * FROM monthly_summaries 
            WHERE user_id = :user_id
        """), {"user_id": user_id})
        summaries = result.fetchall()
        print(f"   Total summaries: {len(summaries)}")
        for summary in summaries:
            print(f"   - {summary.month}/{summary.year}: {summary.total_carbon_saved} kg CO2e saved")

if __name__ == "__main__":
    check_user_data()
    print("\n" + "="*60)
    check_all_user_tables()