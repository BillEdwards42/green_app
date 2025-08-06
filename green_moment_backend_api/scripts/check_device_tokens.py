#!/usr/bin/env python3
"""
Check device tokens for a user
"""
import asyncio
import sys
import os

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, and_
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.notification import DeviceToken, NotificationSettings


async def check_device_tokens(username: str):
    """Check device tokens and notification settings for a user"""
    async with AsyncSessionLocal() as db:
        # Get user
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User '{username}' not found")
            return
            
        print(f"\n📊 User: {user.username} (ID: {user.id})")
        
        # Check device tokens
        result = await db.execute(
            select(DeviceToken).where(DeviceToken.user_id == user.id)
        )
        tokens = result.scalars().all()
        
        print(f"\n📱 Device Tokens ({len(tokens)} total):")
        for token in tokens:
            print(f"  - ID: {token.id}")
            print(f"    Token: {token.token[:50]}...")
            print(f"    Platform: {token.platform}")
            print(f"    Device ID: {token.device_id}")
            print(f"    Active: {token.is_active}")
            print(f"    Created: {token.created_at}")
            print(f"    Updated: {token.updated_at}")
            print()
        
        # Check notification settings
        result = await db.execute(
            select(NotificationSettings).where(NotificationSettings.user_id == user.id)
        )
        settings = result.scalar_one_or_none()
        
        print(f"\n⚙️ Notification Settings:")
        if settings:
            print(f"  - Enabled: {settings.enabled}")
            print(f"  - Scheduled Time: {settings.scheduled_time}")
            print(f"  - Daily Recommendation: {settings.daily_recommendation}")
            print(f"  - Achievement Alerts: {settings.achievement_alerts}")
            print(f"  - Weekly Summary: {settings.weekly_summary}")
        else:
            print("  - No settings found")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_device_tokens.py <username>")
        sys.exit(1)
        
    username = sys.argv[1]
    asyncio.run(check_device_tokens(username))