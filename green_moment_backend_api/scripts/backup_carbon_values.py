#!/usr/bin/env python3
"""
Backup current carbon values before conversion
"""

import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.user import User
from app.models.daily_carbon_progress import DailyCarbonProgress
from app.models.monthly_summary import MonthlySummary


async def backup_carbon_values():
    """Backup all carbon values to JSON file"""
    
    backup_data = {
        "timestamp": datetime.now().isoformat(),
        "users": [],
        "daily_progress": [],
        "monthly_summaries": []
    }
    
    async with AsyncSessionLocal() as db:
        # Backup users
        result = await db.execute(select(User))
        users = result.scalars().all()
        for user in users:
            backup_data["users"].append({
                "id": user.id,
                "username": user.username,
                "total_carbon_saved": user.total_carbon_saved,
                "current_month_carbon_saved": user.current_month_carbon_saved
            })
        
        # Backup daily progress
        result = await db.execute(select(DailyCarbonProgress))
        progress_entries = result.scalars().all()
        for entry in progress_entries:
            backup_data["daily_progress"].append({
                "id": entry.id,
                "user_id": entry.user_id,
                "date": entry.date.isoformat(),
                "daily_carbon_saved": entry.daily_carbon_saved,
                "cumulative_carbon_saved": entry.cumulative_carbon_saved
            })
        
        # Backup monthly summaries
        result = await db.execute(select(MonthlySummary))
        summaries = result.scalars().all()
        for summary in summaries:
            backup_data["monthly_summaries"].append({
                "id": summary.id,
                "user_id": summary.user_id,
                "month": summary.month,
                "year": summary.year,
                "total_carbon_saved": summary.total_carbon_saved
            })
    
    # Save to file
    backup_file = f"carbon_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_file, 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    print(f"✅ Backup saved to {backup_file}")
    print(f"   - {len(backup_data['users'])} users")
    print(f"   - {len(backup_data['daily_progress'])} daily progress entries")
    print(f"   - {len(backup_data['monthly_summaries'])} monthly summaries")


if __name__ == "__main__":
    asyncio.run(backup_carbon_values())