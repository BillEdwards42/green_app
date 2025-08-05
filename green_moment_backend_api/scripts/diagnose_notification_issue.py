#!/usr/bin/env python3
"""
Diagnose notification setup issues
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import User, DeviceToken, NotificationSettings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def diagnose():
    async with AsyncSessionLocal() as db:
        user_id = 36  # edwards_test1
        
        print("🔍 Checking database state for user 36...\n")
        
        # 1. Check device tokens
        print("📱 Device Tokens:")
        tokens = await db.execute(text("""
            SELECT id, device_id, token, is_active, created_at 
            FROM device_tokens 
            WHERE user_id = :user_id
            ORDER BY created_at DESC
        """), {"user_id": user_id})
        
        token_count = 0
        for token in tokens:
            token_count += 1
            print(f"  - ID: {token.id}")
            print(f"    Device: {token.device_id}")
            print(f"    Active: {token.is_active}")
            print(f"    Token: {token.token[:50]}...")
            print(f"    Created: {token.created_at}")
            print()
        
        if token_count == 0:
            print("  ❌ No device tokens found\n")
        
        # 2. Check notification settings
        print("🔔 Notification Settings:")
        settings_result = await db.execute(text("""
            SELECT id, enabled, scheduled_time, daily_recommendation, created_at, updated_at
            FROM notification_settings 
            WHERE user_id = :user_id
        """), {"user_id": user_id})
        
        settings = settings_result.fetchone()
        if settings:
            print(f"  - ID: {settings.id}")
            print(f"  - Enabled: {settings.enabled}")
            print(f"  - Scheduled Time: {settings.scheduled_time}")
            print(f"  - Daily Recommendations: {settings.daily_recommendation}")
            print(f"  - Created: {settings.created_at}")
            print(f"  - Updated: {settings.updated_at}")
        else:
            print("  ❌ No notification settings found")
        
        # 3. Test ORM queries
        print("\n🧪 Testing ORM queries:")
        
        try:
            # Test DeviceToken ORM query
            orm_tokens = await db.execute(
                select(DeviceToken).where(DeviceToken.user_id == user_id)
            )
            orm_token_list = orm_tokens.scalars().all()
            print(f"  ✅ DeviceToken ORM query: Found {len(orm_token_list)} tokens")
        except Exception as e:
            print(f"  ❌ DeviceToken ORM query failed: {e}")
        
        try:
            # Test NotificationSettings ORM query
            orm_settings = await db.execute(
                select(NotificationSettings).where(NotificationSettings.user_id == user_id)
            )
            orm_settings_obj = orm_settings.scalar_one_or_none()
            if orm_settings_obj:
                print(f"  ✅ NotificationSettings ORM query: Found settings")
            else:
                print(f"  ⚠️  NotificationSettings ORM query: No settings found")
        except Exception as e:
            print(f"  ❌ NotificationSettings ORM query failed: {e}")
        
        # 4. Test creating new objects
        print("\n🧪 Testing object creation:")
        
        try:
            # Test creating a DeviceToken object (without saving)
            test_token = DeviceToken(
                user_id=user_id,
                token="test_token_123",
                platform="android",
                device_id="test_device",
                app_version="1.0.0"
            )
            print(f"  ✅ DeviceToken creation: Success (ID: {test_token.id})")
        except Exception as e:
            print(f"  ❌ DeviceToken creation failed: {e}")
        
        try:
            # Test creating a NotificationSettings object (without saving)
            test_settings = NotificationSettings(
                user_id=user_id,
                enabled=True,
                scheduled_time="09:00"
            )
            print(f"  ✅ NotificationSettings creation: Success (ID: {test_settings.id})")
        except Exception as e:
            print(f"  ❌ NotificationSettings creation failed: {e}")


if __name__ == "__main__":
    asyncio.run(diagnose())