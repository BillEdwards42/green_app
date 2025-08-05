#!/usr/bin/env python3
"""
Quick test to set up notification for the next X0 mark
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def quick_setup():
    async with AsyncSessionLocal() as db:
        # Your user ID is 36 (edwards_test1)
        user_id = 36
        
        # Calculate next X0 minute
        now = datetime.now()
        current_minute = now.minute
        
        # Find next X0 mark
        next_10 = ((current_minute // 10) + 1) * 10
        if next_10 >= 60:
            next_hour = (now.hour + 1) % 24
            scheduled_time = f"{next_hour:02d}:00"
        else:
            scheduled_time = f"{now.hour:02d}:{next_10:02d}"
        
        print(f"Current time: {now.strftime('%H:%M:%S')}")
        print(f"Setting notification for: {scheduled_time}")
        
        # Update notification settings directly
        await db.execute(text("""
            UPDATE notification_settings 
            SET enabled = true, 
                daily_recommendation = true,
                scheduled_time = :scheduled_time,
                updated_at = NOW()
            WHERE user_id = :user_id
        """), {"user_id": user_id, "scheduled_time": scheduled_time})
        
        await db.commit()
        
        print(f"✅ Notification scheduled for {scheduled_time}")
        print("Make sure the scheduler is running!")
        print("You should receive a notification at the scheduled time.")


if __name__ == "__main__":
    asyncio.run(quick_setup())