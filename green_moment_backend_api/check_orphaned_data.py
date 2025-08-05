#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_SYNC_URL', 'postgresql://postgres:password@localhost:5432/green_moment')

def check_orphaned_data():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("\n=== CHECKING FOR ORPHANED DATA ===\n")
        
        # Check if ANY chores exist for user_id 35
        result = conn.execute(text("SELECT * FROM chores WHERE user_id = 35"))
        chores = result.fetchall()
        print(f"Chores with user_id = 35: {len(chores)}")
        if chores:
            for chore in chores:
                print(f"  ORPHANED CHORE: {chore}")
        
        # Check all users in the system
        result = conn.execute(text("SELECT id, username, deleted_at FROM users ORDER BY id"))
        users = result.fetchall()
        print(f"\nAll users in system: {len(users)}")
        for user in users:
            print(f"  User {user.id}: {user.username} (deleted: {user.deleted_at})")
        
        # Check all chores in the system
        result = conn.execute(text("SELECT id, user_id, appliance_type FROM chores ORDER BY id"))
        all_chores = result.fetchall()
        print(f"\nAll chores in system: {len(all_chores)}")
        for chore in all_chores:
            print(f"  Chore {chore.id}: user_id={chore.user_id}, type={chore.appliance_type}")

if __name__ == "__main__":
    check_orphaned_data()