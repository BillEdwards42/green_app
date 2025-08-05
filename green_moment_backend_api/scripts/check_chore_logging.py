#!/usr/bin/env python3
"""
Diagnostic script to check chore logging issues
"""

import asyncio
import sys
import os
from datetime import datetime
from sqlalchemy import select, func, text

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.chore import Chore


async def check_chore_logging():
    """Check chore logging status for all users"""
    async with AsyncSessionLocal() as db:
        print("=== Chore Logging Diagnostic ===\n")
        
        # 1. Check total chores in database
        result = await db.execute(select(func.count(Chore.id)))
        total_chores = result.scalar()
        print(f"Total chores in database: {total_chores}")
        
        # 2. Check chores by user
        result = await db.execute(
            select(
                Chore.user_id,
                User.username,
                func.count(Chore.id).label('chore_count'),
                func.min(Chore.start_time).label('first_chore'),
                func.max(Chore.start_time).label('last_chore')
            ).join(User, User.id == Chore.user_id)
            .group_by(Chore.user_id, User.username)
            .order_by(func.count(Chore.id).desc())
        )
        
        user_chores = result.all()
        
        if user_chores:
            print(f"\nUsers with chores logged:")
            print("-" * 80)
            print(f"{'Username':<20} {'Chores':<10} {'First Chore':<20} {'Last Chore':<20}")
            print("-" * 80)
            
            for row in user_chores:
                print(f"{row.username:<20} {row.chore_count:<10} "
                      f"{row.first_chore.strftime('%Y-%m-%d %H:%M'):<20} "
                      f"{row.last_chore.strftime('%Y-%m-%d %H:%M'):<20}")
        else:
            print("\n⚠️  No chores found for any user!")
        
        # 3. Check specific user
        username = sys.argv[1] if len(sys.argv) > 1 else "edwards_test1"
        
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if user:
            print(f"\n\nDetailed check for user '{username}':")
            print("-" * 50)
            
            # Get recent chores
            result = await db.execute(
                select(Chore)
                .where(Chore.user_id == user.id)
                .order_by(Chore.start_time.desc())
                .limit(5)
            )
            chores = result.scalars().all()
            
            if chores:
                print("Recent chores:")
                for chore in chores:
                    print(f"  - {chore.start_time}: {chore.appliance_type} "
                          f"({chore.duration_minutes} min)")
            else:
                print("❌ No chores found for this user!")
                
                # Check if user exists and is active
                print(f"\nUser details:")
                print(f"  ID: {user.id}")
                print(f"  Created: {user.created_at}")
                print(f"  League: {user.current_league}")
                print(f"  Deleted: {user.deleted_at}")
                
        # 4. Check chores table structure
        print("\n\nChores table structure:")
        result = await db.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'chores'
            ORDER BY ordinal_position
        """))
        
        columns = result.all()
        for col in columns:
            print(f"  - {col.column_name}: {col.data_type} (nullable: {col.is_nullable})")
        
        # 5. Recent chores from any user
        print("\n\nMost recent chores (any user):")
        result = await db.execute(
            select(Chore, User.username)
            .join(User, User.id == Chore.user_id)
            .order_by(Chore.created_at.desc())
            .limit(5)
        )
        
        recent = result.all()
        if recent:
            for chore, username in recent:
                print(f"  - {chore.created_at}: {username} - {chore.appliance_type}")
        else:
            print("  No recent chores found")


if __name__ == "__main__":
    print("Checking chore logging status...\n")
    asyncio.run(check_chore_logging())