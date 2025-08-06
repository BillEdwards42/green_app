#!/usr/bin/env python3
"""
Fix cumulative carbon values after migration
"""

import asyncio
import sys
import os
from sqlalchemy import select, and_
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.daily_carbon_progress import DailyCarbonProgress
from app.models.user import User


async def fix_cumulative_totals():
    """Fix cumulative totals to properly accumulate within each month"""
    
    async with AsyncSessionLocal() as db:
        # Get all users with carbon progress
        result = await db.execute(
            select(User.id).distinct()
            .join(DailyCarbonProgress)
        )
        user_ids = [row[0] for row in result.all()]
        
        print(f"Fixing cumulative totals for {len(user_ids)} users...")
        
        for user_id in user_ids:
            # Get all progress entries for this user
            result = await db.execute(
                select(DailyCarbonProgress)
                .where(DailyCarbonProgress.user_id == user_id)
                .order_by(DailyCarbonProgress.date)
            )
            progress_entries = result.scalars().all()
            
            if not progress_entries:
                continue
            
            print(f"\nUser ID {user_id}:")
            
            # Fix cumulative totals
            current_month = None
            cumulative = 0.0
            
            for entry in progress_entries:
                # Check if new month
                if current_month != entry.date.month:
                    # Reset cumulative for new month
                    cumulative = entry.daily_carbon_saved
                    current_month = entry.date.month
                else:
                    # Add to cumulative
                    cumulative += entry.daily_carbon_saved
                
                # Update if different
                if abs(entry.cumulative_carbon_saved - cumulative) > 0.001:
                    print(f"  {entry.date}: {entry.cumulative_carbon_saved:.3f} -> {cumulative:.3f}")
                    entry.cumulative_carbon_saved = cumulative
            
            # Update user's current month total
            current_date = date.today()
            current_month_entries = [e for e in progress_entries 
                                   if e.date.month == current_date.month 
                                   and e.date.year == current_date.year]
            
            if current_month_entries:
                # Get the last entry's cumulative total
                user = await db.get(User, user_id)
                if user:
                    user.current_month_carbon_saved = current_month_entries[-1].cumulative_carbon_saved
        
        await db.commit()
        print("\n✅ Cumulative totals fixed!")


if __name__ == "__main__":
    asyncio.run(fix_cumulative_totals())