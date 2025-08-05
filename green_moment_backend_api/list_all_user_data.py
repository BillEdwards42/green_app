#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_SYNC_URL', 'postgresql://postgres:password@localhost:5432/green_moment')

def list_all_user_data(user_id=35):
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print(f"\n{'='*60}")
        print(f"ALL DATA FOR USER ID: {user_id}")
        print(f"{'='*60}\n")
        
        # 1. User record
        print("1. USER RECORD (users table):")
        print("-" * 50)
        result = conn.execute(text("SELECT * FROM users WHERE id = :user_id"), {"user_id": user_id})
        user = result.fetchone()
        if user:
            for col, val in user._mapping.items():
                print(f"  {col}: {val}")
        else:
            print("  No user found")
        
        # 2. All chores
        print("\n2. CHORE RECORDS (chores table):")
        print("-" * 50)
        result = conn.execute(text("""
            SELECT * FROM chores 
            WHERE user_id = :user_id 
            ORDER BY id
        """), {"user_id": user_id})
        chores = result.fetchall()
        print(f"Total: {len(chores)} chores\n")
        for i, chore in enumerate(chores, 1):
            print(f"Chore #{i}:")
            for col, val in chore._mapping.items():
                print(f"  {col}: {val}")
            print()
        
        # 3. User tasks
        print("3. USER TASK RECORDS (user_tasks table):")
        print("-" * 50)
        result = conn.execute(text("""
            SELECT ut.*, t.name as task_name, t.description as task_desc
            FROM user_tasks ut
            LEFT JOIN tasks t ON ut.task_id = t.id
            WHERE ut.user_id = :user_id
            ORDER BY ut.id
        """), {"user_id": user_id})
        tasks = result.fetchall()
        print(f"Total: {len(tasks)} task records\n")
        for i, task in enumerate(tasks, 1):
            print(f"Task Record #{i}:")
            for col, val in task._mapping.items():
                print(f"  {col}: {val}")
            print()
        
        # 4. Monthly summaries
        print("4. MONTHLY SUMMARY RECORDS (monthly_summaries table):")
        print("-" * 50)
        result = conn.execute(text("""
            SELECT * FROM monthly_summaries 
            WHERE user_id = :user_id
            ORDER BY year, month
        """), {"user_id": user_id})
        summaries = result.fetchall()
        print(f"Total: {len(summaries)} monthly summaries\n")
        for i, summary in enumerate(summaries, 1):
            print(f"Summary #{i}:")
            for col, val in summary._mapping.items():
                print(f"  {col}: {val}")
            print()
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY:")
        print(f"  - User account: {'EXISTS' if user else 'NOT FOUND'}")
        print(f"  - Chores logged: {len(chores)}")
        print(f"  - Task records: {len(tasks)}")
        print(f"  - Monthly summaries: {len(summaries)}")
        print(f"  - Total database records: {1 + len(chores) + len(tasks) + len(summaries)}")
        print("="*60)

if __name__ == "__main__":
    list_all_user_data()