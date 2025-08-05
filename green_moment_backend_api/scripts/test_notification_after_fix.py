#!/usr/bin/env python3
"""
Test notification setup after fixing the models
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import User, DeviceToken, NotificationSettings
from app.services.notification_service import NotificationService

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def test_notification_with_fixed_models(email: str, fcm_token: str):
    """Test notification with the fixed models"""
    
    async with AsyncSessionLocal() as db:
        try:
            print("🔍 Finding user...")
            # Find user
            result = await db.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ User with email {email} not found!")
                return
                
            print(f"✅ Found user: {user.username} (ID: {user.id}, Type: {type(user.id)})")
            
            # Test 1: Create/update device token using ORM
            print("\n📱 Testing device token with ORM...")
            
            # Check existing token
            existing_token = await db.execute(
                select(DeviceToken).where(
                    DeviceToken.user_id == user.id,  # Now using integer directly
                    DeviceToken.device_id == "test_fixed_models"
                )
            )
            existing_token = existing_token.scalar_one_or_none()
            
            if existing_token:
                print("  Updating existing token...")
                existing_token.token = fcm_token
                existing_token.is_active = True
                existing_token.updated_at = datetime.utcnow()
            else:
                print("  Creating new token...")
                device_token = DeviceToken(
                    user_id=user.id,  # Integer now!
                    token=fcm_token,
                    platform="android",
                    device_id="test_fixed_models",
                    app_version="1.0.0"
                )
                db.add(device_token)
            
            await db.commit()
            print("✅ Device token saved via ORM!")
            
            # Test 2: Create/update notification settings using ORM
            print("\n🔔 Testing notification settings with ORM...")
            
            # Calculate next X0 minute
            now = datetime.now()
            next_10_minute = ((now.minute // 10) + 1) * 10
            if next_10_minute >= 60:
                next_10_minute = 0
                scheduled_hour = (now.hour + 1) % 24
            else:
                scheduled_hour = now.hour
            scheduled_time = f"{scheduled_hour:02d}:{next_10_minute:02d}"
            
            # Check existing settings
            existing_settings = await db.execute(
                select(NotificationSettings).where(
                    NotificationSettings.user_id == user.id  # Integer now!
                )
            )
            existing_settings = existing_settings.scalar_one_or_none()
            
            if existing_settings:
                print("  Updating existing settings...")
                existing_settings.enabled = True
                existing_settings.daily_recommendation = True
                existing_settings.scheduled_time = scheduled_time
                existing_settings.updated_at = datetime.utcnow()
            else:
                print("  Creating new settings...")
                settings = NotificationSettings(
                    user_id=user.id,  # Integer now!
                    enabled=True,
                    daily_recommendation=True,
                    scheduled_time=scheduled_time,
                    weather_updates=False
                )
                db.add(settings)
            
            await db.commit()
            print(f"✅ Notification settings saved! Scheduled for: {scheduled_time}")
            
            # Test 3: Send notification using the service
            print("\n🚀 Testing notification send...")
            
            result = await NotificationService.send_notification(
                user_id=str(user.id),  # Service still expects string
                body="🎉 Models fixed! Notifications working properly now!",
                title=None,
                data={
                    'type': 'test_after_fix',
                    'scheduled_time': scheduled_time,
                    'timestamp': datetime.now().isoformat()
                },
                notification_type='test_notification',
                db=db
            )
            
            print(f"\n📊 Result: {result}")
            
            if result['success']:
                print("\n✅ SUCCESS! All systems working!")
                print(f"📅 Next scheduled notification: {scheduled_time}")
                print("\n🎯 You can now run the scheduler:")
                print("   python scripts/run_notification_scheduler.py")
            else:
                print(f"\n⚠️  Something went wrong: {result}")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


async def main():
    print("🔧 Testing Notifications After Model Fix")
    print("=" * 50)
    
    email = input("\n📧 Enter your Gmail address: ").strip()
    print("\n📱 Enter the FCM token from your phone")
    print("(You can find this in the app's dashboard)")
    token = input("Token: ").strip()
    
    if email and token:
        await test_notification_with_fixed_models(email, token)
    else:
        print("❌ Email and token are required!")


if __name__ == "__main__":
    asyncio.run(main())