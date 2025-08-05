#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_SYNC_URL', 'postgresql://postgres:password@localhost:5432/green_moment')

def get_full_chore_details():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Get ALL columns from chores table for user 35
        result = conn.execute(text("""
            SELECT * FROM chores 
            WHERE user_id = 35
            ORDER BY id
        """))
        chores = result.fetchall()
        
        print(f"=== FULL CHORE LOGS FOR USER ID 35 (hijk) ===\n")
        print(f"Total chores: {len(chores)}\n")
        
        for i, chore in enumerate(chores, 1):
            print(f"CHORE #{i}:")
            print("-" * 50)
            # Print all columns
            for column in chore._mapping.keys():
                value = getattr(chore, column)
                print(f"  {column}: {value}")
            print()

if __name__ == "__main__":
    get_full_chore_details()