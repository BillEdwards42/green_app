#!/usr/bin/env python3
"""
Check historical chore data before migration
"""

import asyncio
import sys
import os
from datetime import datetime
from sqlalchemy import select, func, and_
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.chore import Chore
from app.models.daily_carbon_progress import DailyCarbonProgress


async def check_historical_data():
    """Analyze existing chore and carbon data"""
    
    async with AsyncSessionLocal() as db:
        print("\n📊 Historical Data Analysis")
        print("=" * 60)
        
        # Count users
        result = await db.execute(select(func.count(User.id)))
        user_count = result.scalar()
        print(f"\n👥 Total users: {user_count}")
        
        # Count chores
        result = await db.execute(select(func.count(Chore.id)))
        chore_count = result.scalar()
        print(f"📝 Total chores: {chore_count}")
        
        # Date range of chores
        result = await db.execute(
            select(func.min(Chore.start_time), func.max(Chore.start_time))
        )
        min_date, max_date = result.one()
        if min_date:
            print(f"📅 Chore date range: {min_date.date()} to {max_date.date()}")
        
        # Count existing daily_carbon_progress entries
        result = await db.execute(select(func.count(DailyCarbonProgress.id)))
        progress_count = result.scalar()
        print(f"💚 Existing daily_carbon_progress entries: {progress_count}")
        
        # Analyze chores by user
        print("\n\n👤 Per-User Analysis:")
        print("-" * 60)
        
        result = await db.execute(
            select(User).order_by(User.created_at)
        )
        users = result.scalars().all()
        
        for user in users[:10]:  # Show first 10 users
            # Count user's chores
            result = await db.execute(
                select(func.count(Chore.id))
                .where(Chore.user_id == user.id)
            )
            user_chore_count = result.scalar()
            
            # Count user's carbon progress entries
            result = await db.execute(
                select(func.count(DailyCarbonProgress.id))
                .where(DailyCarbonProgress.user_id == user.id)
            )
            user_progress_count = result.scalar()
            
            # Get date range
            result = await db.execute(
                select(func.min(Chore.start_time), func.max(Chore.start_time))
                .where(Chore.user_id == user.id)
            )
            min_date, max_date = result.one()
            
            print(f"\n{user.username}:")
            print(f"  - League: {user.current_league}")
            print(f"  - Total carbon saved: {user.total_carbon_saved:.3f} kg")
            print(f"  - Current month carbon: {user.current_month_carbon_saved:.3f} kg")
            print(f"  - Chores: {user_chore_count}")
            print(f"  - Carbon progress entries: {user_progress_count}")
            if min_date:
                print(f"  - Date range: {min_date.date()} to {max_date.date()}")
        
        # Analyze chores by month
        print("\n\n📅 Chores by Month:")
        print("-" * 60)
        
        result = await db.execute(
            select(
                func.date_trunc('month', Chore.start_time).label('month'),
                func.count(Chore.id).label('count')
            )
            .group_by('month')
            .order_by('month')
        )
        
        for row in result:
            month_date = row.month
            count = row.count
            if month_date:
                print(f"{month_date.strftime('%Y-%m')}: {count} chores")
        
        # Check for data inconsistencies
        print("\n\n⚠️  Data Consistency Checks:")
        print("-" * 60)
        
        # Users with chores but no carbon progress
        result = await db.execute(
            select(User)
            .join(Chore)
            .outerjoin(DailyCarbonProgress)
            .where(DailyCarbonProgress.id.is_(None))
            .group_by(User.id)
        )
        users_without_progress = result.scalars().all()
        
        if users_without_progress:
            print(f"\n❌ {len(users_without_progress)} users have chores but no carbon progress:")
            for user in users_without_progress[:5]:
                print(f"   - {user.username}")
        else:
            print("\n✅ All users with chores have carbon progress entries")
        
        # Check carbon intensity data availability
        if os.path.exists('logs/actual_carbon_intensity.csv'):
            with open('logs/actual_carbon_intensity.csv', 'r') as f:
                lines = f.readlines()
                print(f"\n✅ Carbon intensity data available: {len(lines)-1} entries")
                if len(lines) > 1:
                    # Show date range
                    first_line = lines[1].strip().split(',')
                    last_line = lines[-1].strip().split(',')
                    if len(first_line) > 0 and len(last_line) > 0:
                        try:
                            first_date = datetime.fromisoformat(first_line[0]).date()
                            last_date = datetime.fromisoformat(last_line[0]).date()
                            print(f"   Date range: {first_date} to {last_date}")
                        except:
                            pass
        else:
            print("\n❌ Carbon intensity data file not found!")


def main():
    asyncio.run(check_historical_data())


if __name__ == "__main__":
    main()