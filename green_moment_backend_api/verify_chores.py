#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_SYNC_URL', 'postgresql://postgres:password@localhost:5432/green_moment')

def verify_chores():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Count ALL chores for user 35
        result = conn.execute(text("""
            SELECT COUNT(*) as total_count 
            FROM chores 
            WHERE user_id = 35
        """))
        total = result.scalar()
        print(f"Total chores for user 35: {total}")
        
        # Get all chores with details
        result = conn.execute(text("""
            SELECT id, appliance_type, start_time, duration_minutes, created_at
            FROM chores 
            WHERE user_id = 35
            ORDER BY id
        """))
        chores = result.fetchall()
        
        print(f"\nAll chores for user 35:")
        for chore in chores:
            print(f"ID {chore.id}: {chore.appliance_type} - {chore.start_time} ({chore.duration_minutes} min)")
        
        # Also check if there are any chores in the database at all
        result = conn.execute(text("SELECT COUNT(*) FROM chores"))
        total_all = result.scalar()
        print(f"\nTotal chores in database (all users): {total_all}")
        
        # Check unique user IDs that have chores
        result = conn.execute(text("""
            SELECT DISTINCT user_id, COUNT(*) as chore_count 
            FROM chores 
            GROUP BY user_id 
            ORDER BY user_id
        """))
        user_counts = result.fetchall()
        print(f"\nChores per user:")
        for uc in user_counts:
            print(f"  User {uc.user_id}: {uc.chore_count} chores")

if __name__ == "__main__":
    verify_chores()